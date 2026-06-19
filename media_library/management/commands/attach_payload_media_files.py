import mimetypes
from pathlib import Path, PurePath
from urllib.parse import unquote, urlsplit

from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from PIL import Image as PillowImage

from media_library.models import Image, ImageVariant


def _basename_from_url(url: str) -> str:
    if not url:
        return ""
    return unquote(PurePath(urlsplit(url).path).name)


def _metadata_from_path(path: Path) -> dict[str, int | str]:
    with PillowImage.open(path) as image:
        width, height = image.size
    mime_type, _encoding = mimetypes.guess_type(path.name)
    return {
        "width": width,
        "height": height,
        "filesize": path.stat().st_size,
        "mime_type": mime_type or "",
    }


class LocalFileIndex:
    def __init__(self, source_dir: Path):
        self.paths_by_name: dict[str, Path | None] = {}
        self.paths_by_lower_name: dict[str, Path | None] = {}

        for path in source_dir.iterdir():
            if not path.is_file() or path.name.startswith("."):
                continue
            self._add(path.name, path)
            self._add(unquote(path.name), path)
            self._add_lower(path.name, path)
            self._add_lower(unquote(path.name), path)

    def find(self, *names: str) -> Path | None:
        for name in names:
            if not name:
                continue
            path = self.paths_by_name.get(name)
            if path is not None:
                return path
            path = self.paths_by_lower_name.get(name.lower())
            if path is not None:
                return path
        return None

    def _add(self, name: str, path: Path) -> None:
        existing = self.paths_by_name.get(name)
        if existing == path:
            return
        self.paths_by_name[name] = path if existing is None else None

    def _add_lower(self, name: str, path: Path) -> None:
        key = name.lower()
        existing = self.paths_by_lower_name.get(key)
        if existing == path:
            return
        self.paths_by_lower_name[key] = path if existing is None else None


class Command(BaseCommand):
    help = "Attach already-downloaded Payload media files from a local directory."

    def add_arguments(self, parser):
        parser.add_argument("--site", required=True, help="Site slug to attach media for.")
        parser.add_argument(
            "--source-dir",
            default="data/payload/r2-media",
            help="Directory containing downloaded Payload media files.",
        )
        parser.add_argument(
            "--variants",
            action="store_true",
            help="Also attach known image variants.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Reattach files even when a matching local file is already present.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            help="Limit the number of image records processed in this run.",
        )

    def handle(self, *args, **options):
        source_dir = Path(options["source_dir"])
        if not source_dir.is_dir():
            raise CommandError(f"Source directory does not exist: {source_dir}")

        file_index = LocalFileIndex(source_dir)
        attached = 0
        missing = []
        failures = []

        images = Image.objects.filter(site__slug=options["site"]).select_related("site")
        if options["limit"] is not None:
            images = images[: options["limit"]]

        for image in images:
            attached += self._attach_image(
                image=image,
                file_index=file_index,
                force=options["force"],
                missing=missing,
                failures=failures,
            )
            if not options["variants"]:
                continue
            for variant in image.variants.select_related("image", "image__site"):
                attached += self._attach_variant(
                    variant=variant,
                    file_index=file_index,
                    force=options["force"],
                    missing=missing,
                    failures=failures,
                )

        self.stdout.write(self.style.SUCCESS(f"Attached {attached} files."))
        if missing:
            self.stderr.write(self.style.WARNING(f"Missing {len(missing)} files:"))
            for label in missing:
                self.stderr.write(f"- {label}")
        if failures:
            self.stderr.write(self.style.ERROR(f"Failed to attach {len(failures)} files:"))
            for label, error in failures:
                self.stderr.write(f"- {label}: {error}")

    def _attach_image(
        self,
        *,
        image: Image,
        file_index: LocalFileIndex,
        force: bool,
        missing: list[str],
        failures: list[tuple[str, str]],
    ) -> int:
        if not force and self._has_matching_file(image.original, image.filesize):
            return 0

        source_path = file_index.find(image.filename, _basename_from_url(image.payload_url))
        if source_path is None:
            missing.append(f"image:{image.pk}:{image.filename or image.payload_url}")
            return 0

        try:
            metadata = _metadata_from_path(source_path)
            with source_path.open("rb") as handle:
                image.original.save(source_path.name, File(handle), save=False)
            image.width = metadata["width"]
            image.height = metadata["height"]
            image.filesize = metadata["filesize"]
            image.mime_type = metadata["mime_type"]
            image.save(
                update_fields=[
                    "original",
                    "width",
                    "height",
                    "filesize",
                    "mime_type",
                    "updated_at",
                ],
            )
        except Exception as exc:  # noqa: BLE001 - keep attaching remaining files.
            failures.append((f"image:{image.pk}:{source_path.name}", str(exc)))
            return 0

        return 1

    def _attach_variant(
        self,
        *,
        variant: ImageVariant,
        file_index: LocalFileIndex,
        force: bool,
        missing: list[str],
        failures: list[tuple[str, str]],
    ) -> int:
        if not force and self._has_matching_file(variant.file, variant.filesize):
            return 0

        source_path = file_index.find(variant.filename, _basename_from_url(variant.payload_url))
        if source_path is None:
            missing.append(f"variant:{variant.pk}:{variant.filename or variant.payload_url}")
            return 0

        try:
            metadata = _metadata_from_path(source_path)
            with source_path.open("rb") as handle:
                variant.file.save(source_path.name, File(handle), save=False)
            variant.width = metadata["width"]
            variant.height = metadata["height"]
            variant.filesize = metadata["filesize"]
            variant.mime_type = metadata["mime_type"]
            variant.save(
                update_fields=[
                    "file",
                    "width",
                    "height",
                    "filesize",
                    "mime_type",
                    "updated_at",
                ],
            )
        except Exception as exc:  # noqa: BLE001 - keep attaching remaining files.
            failures.append((f"variant:{variant.pk}:{source_path.name}", str(exc)))
            return 0

        return 1

    def _has_matching_file(self, field_file, expected_size: int | None) -> bool:
        if not field_file:
            return False
        if expected_size is None:
            return True
        try:
            return field_file.size == expected_size
        except OSError:
            return False
