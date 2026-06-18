from pathlib import PurePath
from urllib.request import urlopen

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from media_library.models import Image, ImageVariant


def _download(url: str) -> bytes:
    with urlopen(url, timeout=60) as response:
        return response.read()


def _filename_from_url(url: str, fallback: str) -> str:
    return PurePath(url.split("?", 1)[0]).name or fallback


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

    def handle(self, *args, **options):
        downloaded = 0
        images = Image.objects.filter(site__slug=options["site"]).select_related("site")
        for image in images:
            if self._download_image(image, force=options["force"]):
                downloaded += 1
            if options["variants"]:
                for variant in image.variants.select_related("image", "image__site"):
                    if self._download_variant(variant, force=options["force"]):
                        downloaded += 1

        self.stdout.write(self.style.SUCCESS(f"Downloaded {downloaded} files."))

    def _download_image(self, image: Image, *, force: bool) -> bool:
        if not image.payload_url or self._has_matching_file(
            image.original,
            image.filesize,
            force=force,
        ):
            return False
        content = _download(image.payload_url)
        filename = image.filename or _filename_from_url(image.payload_url, f"image-{image.pk}")
        image.original.save(filename, ContentFile(content), save=True)
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
        variant.file.save(filename, ContentFile(content), save=True)
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
