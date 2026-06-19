from io import BytesIO, StringIO

import pytest
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.db import IntegrityError
from PIL import Image as PillowImage

from media_library.management.commands.download_payload_media import Command
from media_library.models import Image, ImageVariant
from media_library.payload import absolute_payload_url, upsert_payload_media_doc
from sites_core.models import Site


def png_bytes(width=2, height=3):
    output = BytesIO()
    PillowImage.new("RGB", (width, height), color="white").save(output, format="PNG")
    return output.getvalue()


def test_image_upload_path_uses_site_slug(db, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    image = Image.objects.create(site=site, title="Cover")

    image.original.save("cover.jpg", ContentFile(b"not-really-an-image"), save=False)

    assert image.original.name == "sites/kent/images/originals/cover.jpg"


def test_variant_upload_path_uses_site_slug_and_kind(db, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    image = Image.objects.create(site=site, title="Cover")
    variant = ImageVariant(image=image, kind=ImageVariant.Kind.THUMBNAIL)

    variant.file.save("cover-thumb.jpg", ContentFile(b"not-really-an-image"), save=False)

    assert variant.file.name == "sites/kent/images/variants/thumbnail/cover-thumb.jpg"


def test_variant_upload_path_prefers_raw_payload_kind(db, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    image = Image.objects.create(site=site, title="Cover")
    variant = ImageVariant(
        image=image,
        kind=ImageVariant.Kind.OTHER,
        payload_kind="custom-wide",
    )

    variant.file.save("cover-custom.jpg", ContentFile(b"not-really-an-image"), save=False)

    assert variant.file.name == "sites/kent/images/variants/custom-wide/cover-custom.jpg"


def test_payload_media_upsert_is_idempotent(db):
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    doc = {
        "id": 167,
        "alt": "Slogans dada",
        "filename": "Slogans dada 2.jpg",
        "mimeType": "image/jpeg",
        "filesize": 1159507,
        "width": 4320,
        "height": 2700,
        "url": "/api/media/file/Slogans%20dada%202.jpg",
        "thumbnailURL": "/api/media/file/Slogans%20dada%202-300x188.jpg",
        "createdAt": "2026-05-12T07:33:20.516Z",
        "updatedAt": "2026-05-12T07:33:20.516Z",
        "sizes": {
            "thumbnail": {
                "url": "/api/media/file/Slogans%20dada%202-300x188.jpg",
                "width": 300,
                "height": 188,
                "mimeType": "image/jpeg",
                "filesize": 18221,
                "filename": "Slogans dada 2-300x188.jpg",
            }
        },
    }

    image = upsert_payload_media_doc(site=site, doc=doc)
    same_image = upsert_payload_media_doc(site=site, doc={**doc, "alt": "Updated alt"})

    assert same_image.pk == image.pk
    assert Image.objects.count() == 1
    assert ImageVariant.objects.count() == 1
    assert same_image.alt_text == "Updated alt"
    assert ImageVariant.objects.get().payload_kind == "thumbnail"


def test_payload_media_upsert_preserves_distinct_unknown_size_keys(db):
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    doc = {
        "id": 167,
        "filename": "image.jpg",
        "url": "/api/media/file/image.jpg",
        "sizes": {
            "customWide": {
                "url": "/api/media/file/image-custom-wide.jpg",
                "filename": "image-custom-wide.jpg",
            },
            "customTall": {
                "url": "/api/media/file/image-custom-tall.jpg",
                "filename": "image-custom-tall.jpg",
            },
        },
    }

    upsert_payload_media_doc(site=site, doc=doc)
    upsert_payload_media_doc(site=site, doc=doc)

    variants = ImageVariant.objects.order_by("payload_kind")
    assert variants.count() == 2
    assert [variant.kind for variant in variants] == [
        ImageVariant.Kind.OTHER,
        ImageVariant.Kind.OTHER,
    ]
    assert [variant.payload_kind for variant in variants] == ["customTall", "customWide"]


def test_payload_id_is_unique_per_site(db):
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    Image.objects.create(site=site, payload_id=1)

    with pytest.raises(IntegrityError):
        Image.objects.create(site=site, payload_id=1)


def test_import_payload_media_reports_actual_upserts(db, monkeypatch):
    Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    docs = [
        {"id": 1, "filename": "first.jpg", "url": "/api/media/file/first.jpg"},
        {"id": 2, "filename": "second.jpg", "url": "/api/media/file/second.jpg"},
    ]

    monkeypatch.setattr(
        "media_library.management.commands.import_payload_media.fetch_payload_collection",
        lambda *args, **kwargs: docs,
    )
    stdout = StringIO()

    call_command("import_payload_media", "--site", "kent", stdout=stdout)

    assert Image.objects.count() == 2
    assert "Imported 2 of 2 fetched media records." in stdout.getvalue()


def test_import_payload_media_rolls_back_when_upsert_fails(db, monkeypatch):
    Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    docs = [
        {"id": 1, "filename": "first.jpg", "url": "/api/media/file/first.jpg"},
        {"id": 2, "filename": "second.jpg", "url": "/api/media/file/second.jpg"},
    ]

    def upsert_or_fail(*, site, doc, base_url):
        if doc["id"] == 2:
            raise RuntimeError("boom")
        return upsert_payload_media_doc(site=site, doc=doc, base_url=base_url)

    monkeypatch.setattr(
        "media_library.management.commands.import_payload_media.fetch_payload_collection",
        lambda *args, **kwargs: docs,
    )
    monkeypatch.setattr(
        "media_library.management.commands.import_payload_media.upsert_payload_media_doc",
        upsert_or_fail,
    )

    with pytest.raises(RuntimeError):
        call_command("import_payload_media", "--site", "kent")

    assert Image.objects.count() == 0


def test_site_owned_reverse_related_names_are_class_based(db):
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    image = Image.objects.create(site=site, title="Cover")

    assert list(site.images.all()) == [image]


def test_absolute_payload_url_keeps_absolute_urls():
    assert absolute_payload_url("https://example.com/image.jpg") == "https://example.com/image.jpg"


def test_absolute_payload_url_expands_relative_payload_urls():
    assert (
        absolute_payload_url("/api/media/file/image.jpg", base_url="https://www.kent-artiste.com")
        == "https://www.kent-artiste.com/api/media/file/image.jpg"
    )


def test_download_command_only_skips_matching_file_size(db, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    image = Image.objects.create(site=site, filesize=4)
    image.original.save("file.jpg", ContentFile(b"1234"), save=True)
    command = Command()

    assert command._has_matching_file(image.original, 4, force=False) is True
    assert command._has_matching_file(image.original, 5, force=False) is False
    assert command._has_matching_file(image.original, 4, force=True) is False


def test_download_command_continues_after_failure(db, settings, tmp_path, monkeypatch):
    settings.MEDIA_ROOT = tmp_path
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    failed = Image.objects.create(
        site=site,
        filename="failed.jpg",
        payload_url="https://payload.test/failed.jpg",
    )
    successful = Image.objects.create(
        site=site,
        filename="successful.jpg",
        payload_url="https://payload.test/successful.jpg",
    )

    def fake_download(url):
        if url == failed.payload_url:
            raise OSError("network down")
        return png_bytes()

    monkeypatch.setattr("media_library.management.commands.download_payload_media._download", fake_download)
    stdout = StringIO()
    stderr = StringIO()

    call_command(
        "download_payload_media",
        "--site",
        "kent",
        "--retries",
        "0",
        stdout=stdout,
        stderr=stderr,
    )
    successful.refresh_from_db()
    failed.refresh_from_db()

    assert successful.original
    assert not failed.original
    assert "Downloaded 1 files." in stdout.getvalue()
    assert f"image:{failed.pk}" in stderr.getvalue()
    assert "network down" in stderr.getvalue()


def test_download_command_retries_transient_failure(db, settings, tmp_path, monkeypatch):
    settings.MEDIA_ROOT = tmp_path
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    image = Image.objects.create(
        site=site,
        filename="retry.jpg",
        payload_url="https://payload.test/retry.jpg",
    )
    attempts = {"count": 0}

    def fake_download(url):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise OSError("temporary failure")
        return png_bytes()

    monkeypatch.setattr("media_library.management.commands.download_payload_media._download", fake_download)
    monkeypatch.setattr("media_library.management.commands.download_payload_media.sleep", lambda delay: None)

    call_command("download_payload_media", "--site", "kent", "--retries", "1")
    image.refresh_from_db()

    assert attempts["count"] == 2
    assert image.original


def test_download_command_refreshes_original_metadata_from_local_file(
    db,
    settings,
    tmp_path,
    monkeypatch,
):
    settings.MEDIA_ROOT = tmp_path
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    image = Image.objects.create(
        site=site,
        filename="original.png",
        payload_url="https://payload.test/original.png",
        width=99,
        height=99,
        filesize=99,
    )
    content = png_bytes(width=7, height=11)

    monkeypatch.setattr(
        "media_library.management.commands.download_payload_media._download",
        lambda url: content,
    )

    call_command("download_payload_media", "--site", "kent", "--force")
    image.refresh_from_db()

    assert image.width == 7
    assert image.height == 11
    assert image.filesize == len(content)


def test_download_command_refreshes_variant_metadata_from_local_file(
    db,
    settings,
    tmp_path,
    monkeypatch,
):
    settings.MEDIA_ROOT = tmp_path
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    image = Image.objects.create(site=site, title="Cover")
    variant = ImageVariant.objects.create(
        image=image,
        kind=ImageVariant.Kind.THUMBNAIL,
        payload_kind="thumbnail",
        filename="thumb.png",
        payload_url="https://payload.test/thumb.png",
        width=99,
        height=99,
        filesize=99,
    )
    content = png_bytes(width=13, height=17)

    monkeypatch.setattr(
        "media_library.management.commands.download_payload_media._download",
        lambda url: content,
    )

    call_command("download_payload_media", "--site", "kent", "--variants", "--force")
    variant.refresh_from_db()

    assert variant.width == 13
    assert variant.height == 17
    assert variant.filesize == len(content)
