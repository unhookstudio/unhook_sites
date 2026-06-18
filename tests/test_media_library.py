from django.core.files.base import ContentFile
from django.db import IntegrityError

from media_library.management.commands.download_payload_media import Command
from media_library.models import Image, ImageVariant
from media_library.payload import absolute_payload_url, upsert_payload_media_doc
from sites_core.models import Site


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


def test_payload_id_is_unique_per_site(db):
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    Image.objects.create(site=site, payload_id=1)

    try:
        Image.objects.create(site=site, payload_id=1)
    except IntegrityError:
        pass
    else:
        raise AssertionError("duplicate payload_id should fail per site")


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
