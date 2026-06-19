from io import BytesIO
from pathlib import PurePath
from time import sleep
from urllib.request import urlopen

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from PIL import Image as PillowImage

from media_library.models import Image, ImageVariant


def _download(url: str) -> bytes:
    with urlopen(url, timeout=60) as response:
        return response.read()


def _filename_from_url(url: str, fallback: str) -> str:
    return PurePath(url.split("?", 1)[0]).name or fallback


def _image_metadata(content: bytes) -> dict[str, int]:
    with PillowImage.open(BytesIO(content)) as image:
        width, height = image.size
    return {
        "width": width,
        "height": height,
        "filesize": len(content),
    }


class Command(BaseCommand):
    help = "Download media files from Payload URLs for existing media records."

    def add_arguments(self, parser):
        parser.add_argument("--site", required=True, help="Site slug to download media for.")
        parser.add_argument(
            "--variants",
            action="store_true",
            help="Also download known image variants.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Redownload files even when a local file is already present.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            help="Limit the number of image records processed in this run.",
        )
        parser.add_argument(
            "--retries",
            type=int,
            default=2,
            help="Number of retries after the first failed download attempt.",
        )

    def handle(self, *args, **options):
        downloaded = 0
        failures = []
        images = Image.objects.filter(site__slug=options["site"]).select_related("site")
        if options["limit"] is not None:
            images = images[: options["limit"]]
        for image in images:
            downloaded += self._attempt_download(
                label=f"image:{image.pk}",
                callback=lambda image=image: self._download_image(image, force=options["force"]),
                retries=options["retries"],
                failures=failures,
            )
            if not options["variants"]:
                continue
            for variant in image.variants.select_related("image", "image__site"):
                downloaded += self._attempt_download(
                    label=f"variant:{variant.pk}",
                    callback=lambda variant=variant: self._download_variant(
                        variant,
                        force=options["force"],
                    ),
                    retries=options["retries"],
                    failures=failures,
                )

        self.stdout.write(self.style.SUCCESS(f"Downloaded {downloaded} files."))
        if failures:
            self.stderr.write(self.style.ERROR(f"Failed to download {len(failures)} files:"))
            for label, error in failures:
                self.stderr.write(f"- {label}: {error}")

    def _attempt_download(self, *, label: str, callback, retries: int, failures: list) -> int:
        attempts = max(retries, 0) + 1
        for attempt in range(1, attempts + 1):
            try:
                return 1 if callback() else 0
            except Exception as exc:  # noqa: BLE001 - management command must continue per file.
                if attempt == attempts:
                    failures.append((label, str(exc)))
                    return 0
                sleep(min(attempt, 3))

        return 0

    def _download_image(self, image: Image, *, force: bool) -> bool:
        if not image.payload_url or self._has_matching_file(
            image.original,
            image.filesize,
            force=force,
        ):
            return False
        content = _download(image.payload_url)
        filename = image.filename or _filename_from_url(image.payload_url, f"image-{image.pk}")
        metadata = _image_metadata(content)
        image.original.save(filename, ContentFile(content), save=False)
        image.width = metadata["width"]
        image.height = metadata["height"]
        image.filesize = metadata["filesize"]
        image.save(update_fields=["original", "width", "height", "filesize", "updated_at"])
        return True

    def _download_variant(self, variant: ImageVariant, *, force: bool) -> bool:
        if not variant.payload_url or self._has_matching_file(
            variant.file,
            variant.filesize,
            force=force,
        ):
            return False
        content = _download(variant.payload_url)
        filename = variant.filename or _filename_from_url(
            variant.payload_url,
            f"variant-{variant.pk}",
        )
        metadata = _image_metadata(content)
        variant.file.save(filename, ContentFile(content), save=False)
        variant.width = metadata["width"]
        variant.height = metadata["height"]
        variant.filesize = metadata["filesize"]
        variant.save(update_fields=["file", "width", "height", "filesize", "updated_at"])
        return True

    def _has_matching_file(self, field_file, expected_size: int | None, *, force: bool) -> bool:
        if force or not field_file:
            return False
        if expected_size is None:
            return True
        try:
            return field_file.size == expected_size
        except OSError:
            return False
