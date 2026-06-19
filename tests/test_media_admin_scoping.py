from django.contrib.auth.models import Permission
from django.urls import reverse

from media_library.admin import ImageVariantAdmin, ImageVariantInline
from media_library.models import Image, ImageVariant
from sites_core.models import Site, User


def test_image_admin_changelist_and_detail_are_scoped_for_staff(client, db):
    kent = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    other = Site.objects.create(name="Other", slug="other", domain="example.com")
    kent_image = Image.objects.create(site=kent, title="Kent image")
    other_image = Image.objects.create(site=other, title="Other image")
    user = User.objects.create_user(username="editor", password="password", is_staff=True)
    user.sites.add(kent)
    user.user_permissions.add(
        Permission.objects.get(codename="view_image"),
        Permission.objects.get(codename="change_image"),
    )

    client.force_login(user)

    changelist = client.get(reverse("admin:media_library_image_changelist"))
    other_detail = client.get(reverse("admin:media_library_image_change", args=[other_image.pk]))

    assert changelist.status_code == 200
    assert kent_image.title in changelist.text
    assert other_image.title not in changelist.text
    assert other_detail.status_code == 404


def test_image_variant_admin_changelist_and_detail_are_scoped_for_staff(client, db):
    kent = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    other = Site.objects.create(name="Other", slug="other", domain="example.com")
    kent_image = Image.objects.create(site=kent, title="Kent image")
    other_image = Image.objects.create(site=other, title="Other image")
    kent_variant = ImageVariant.objects.create(
        image=kent_image,
        kind=ImageVariant.Kind.THUMBNAIL,
        filename="kent-thumb.jpg",
    )
    other_variant = ImageVariant.objects.create(
        image=other_image,
        kind=ImageVariant.Kind.THUMBNAIL,
        filename="other-thumb.jpg",
    )
    user = User.objects.create_user(username="editor", password="password", is_staff=True)
    user.sites.add(kent)
    user.user_permissions.add(
        Permission.objects.get(codename="view_imagevariant"),
        Permission.objects.get(codename="change_imagevariant"),
    )

    client.force_login(user)

    changelist = client.get(reverse("admin:media_library_imagevariant_changelist"))
    other_detail = client.get(
        reverse("admin:media_library_imagevariant_change", args=[other_variant.pk])
    )

    assert changelist.status_code == 200
    assert str(kent_variant.image) in changelist.text
    assert str(other_variant.image) not in changelist.text
    assert other_detail.status_code == 404


def test_image_variant_admin_hides_site_filter_for_staff(client, db):
    kent = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    image = Image.objects.create(site=kent, title="Kent image")
    ImageVariant.objects.create(image=image, kind=ImageVariant.Kind.THUMBNAIL)
    user = User.objects.create_user(username="editor", password="password", is_staff=True)
    user.sites.add(kent)
    user.user_permissions.add(Permission.objects.get(codename="view_imagevariant"))

    client.force_login(user)
    changelist = client.get(reverse("admin:media_library_imagevariant_changelist"))

    assert changelist.status_code == 200
    assert "image__site__id__exact" not in changelist.text


def test_payload_kind_is_readonly_in_media_admin():
    assert "payload_kind" in ImageVariantInline.readonly_fields
    assert "payload_kind" in ImageVariantAdmin.readonly_fields
