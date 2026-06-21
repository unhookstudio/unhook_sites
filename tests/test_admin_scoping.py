from django.contrib import admin
from django.contrib.auth.models import Permission
from django.test import RequestFactory
from django.urls import reverse

from music.models import Album, Artist, Song, Track
from photos.models import Photo, PhotoCollection, PhotoCollectionItem
from sites_core.models import NavigationLink, Site, User


def test_site_admin_limits_staff_to_allowed_sites(db):
    kent = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    other = Site.objects.create(name="Other", slug="other", domain="example.com")
    user = User.objects.create_user(username="editor", is_staff=True)
    user.sites.add(kent)
    request = RequestFactory().get("/admin/sites_core/site/")
    request.user = user

    queryset = admin.site._registry[Site].get_queryset(request)

    assert list(queryset) == [kent]
    assert other not in queryset


def test_site_admin_shows_all_sites_to_superuser(db):
    kent = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    other = Site.objects.create(name="Other", slug="other", domain="example.com")
    user = User.objects.create_superuser(username="admin")
    request = RequestFactory().get("/admin/sites_core/site/")
    request.user = user

    queryset = admin.site._registry[Site].get_queryset(request)

    assert set(queryset) == {kent, other}


def test_site_scoped_admin_uses_default_site_as_initial_data(db):
    kent = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    user = User.objects.create_user(username="editor", is_staff=True, default_site=kent)
    user.sites.add(kent)
    request = RequestFactory().get("/admin/sites_core/navigationlink/add/")
    request.user = user

    model_admin = admin.site._registry[NavigationLink]
    initial = model_admin.get_changeform_initial_data(request)

    assert initial["site"] == kent.pk


def test_site_scoped_admin_does_not_set_initial_blank_default_site(db):
    user = User.objects.create_user(username="editor", is_staff=True)
    request = RequestFactory().get("/admin/sites_core/navigationlink/add/")
    request.user = user

    model_admin = admin.site._registry[NavigationLink]
    initial = model_admin.get_changeform_initial_data(request)

    assert "site" not in initial


def test_site_admin_changelist_and_detail_are_scoped_for_staff(client, db):
    kent = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    other = Site.objects.create(name="Other", slug="other", domain="example.com")
    user = User.objects.create_user(username="editor", password="password", is_staff=True)
    user.sites.add(kent)
    user.user_permissions.add(
        Permission.objects.get(codename="view_site"),
        Permission.objects.get(codename="change_site"),
    )

    client.force_login(user)

    changelist = client.get(reverse("admin:sites_core_site_changelist"))
    other_detail = client.get(reverse("admin:sites_core_site_change", args=[other.pk]))

    assert changelist.status_code == 200
    assert "Kent" in changelist.text
    assert "Other" not in changelist.text
    assert other_detail.status_code == 404


def test_site_owned_admin_changelist_and_detail_are_scoped_for_staff(client, db):
    kent = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    other = Site.objects.create(name="Other", slug="other", domain="example.com")
    kent_link = NavigationLink.objects.create(site=kent, label="Kent link", url="/kent/")
    other_link = NavigationLink.objects.create(site=other, label="Other link", url="/other/")
    user = User.objects.create_user(username="editor", password="password", is_staff=True)
    user.sites.add(kent)
    user.user_permissions.add(
        Permission.objects.get(codename="view_navigationlink"),
        Permission.objects.get(codename="change_navigationlink"),
    )

    client.force_login(user)

    changelist = client.get(reverse("admin:sites_core_navigationlink_changelist"))
    other_detail = client.get(
        reverse("admin:sites_core_navigationlink_change", args=[other_link.pk])
    )

    assert changelist.status_code == 200
    assert kent_link.label in changelist.text
    assert other_link.label not in changelist.text
    assert other_detail.status_code == 404


def test_site_scoped_admin_hides_site_filter_for_staff(client, db):
    kent = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    user = User.objects.create_user(username="editor", password="password", is_staff=True)
    user.sites.add(kent)
    user.user_permissions.add(Permission.objects.get(codename="view_navigationlink"))

    client.force_login(user)
    changelist = client.get(reverse("admin:sites_core_navigationlink_changelist"))

    assert changelist.status_code == 200
    assert "site__id__exact" not in changelist.text


def test_site_scoped_admin_hides_site_field_for_staff(db):
    kent = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    user = User.objects.create_user(username="editor", is_staff=True, default_site=kent)
    user.sites.add(kent)
    request = RequestFactory().get("/admin/sites_core/navigationlink/add/")
    request.user = user

    model_admin = admin.site._registry[NavigationLink]

    assert "site" in model_admin.get_exclude(request)


def test_site_scoped_admin_shows_filtered_site_field_for_multi_site_staff(db):
    kent = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    second = Site.objects.create(name="Second", slug="second", domain="second.example.com")
    other = Site.objects.create(name="Other", slug="other", domain="example.com")
    user = User.objects.create_user(username="editor", is_staff=True)
    user.sites.add(kent, second)
    request = RequestFactory().get("/admin/sites_core/navigationlink/add/")
    request.user = user

    model_admin = admin.site._registry[NavigationLink]
    site_field = model_admin.formfield_for_foreignkey(
        NavigationLink._meta.get_field("site"),
        request,
    )

    assert "site" not in model_admin.get_exclude(request)
    assert set(site_field.queryset) == {kent, second}
    assert other not in site_field.queryset


def test_site_scoped_admin_add_assigns_staff_site_and_ignores_posted_site(client, db):
    kent = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    other = Site.objects.create(name="Other", slug="other", domain="example.com")
    user = User.objects.create_user(
        username="editor",
        password="password",
        is_staff=True,
        default_site=kent,
    )
    user.sites.add(kent)
    user.user_permissions.add(Permission.objects.get(codename="add_navigationlink"))

    client.force_login(user)
    response = client.post(
        reverse("admin:sites_core_navigationlink_add"),
        {
            "site": other.pk,
            "label": "Discographie",
            "url": "/musique",
            "order": 10,
            "is_active": "on",
        },
    )

    assert response.status_code == 302
    link = NavigationLink.objects.get()
    assert link.site == kent
    assert link.label == "Discographie"


def test_site_scoped_admin_add_uses_sole_allowed_site_without_default(client, db):
    kent = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    user = User.objects.create_user(username="editor", password="password", is_staff=True)
    user.sites.add(kent)
    user.user_permissions.add(Permission.objects.get(codename="add_navigationlink"))

    client.force_login(user)
    response = client.post(
        reverse("admin:sites_core_navigationlink_add"),
        {
            "label": "Livres",
            "url": "/livres",
            "order": 20,
            "is_active": "on",
        },
    )

    assert response.status_code == 302
    link = NavigationLink.objects.get()
    assert link.site == kent


def test_site_scoped_admin_denies_add_without_assignable_site(client, db):
    user = User.objects.create_user(username="editor", password="password", is_staff=True)
    user.user_permissions.add(Permission.objects.get(codename="add_navigationlink"))

    client.force_login(user)
    response = client.get(reverse("admin:sites_core_navigationlink_add"))

    assert response.status_code == 403


def test_track_admin_foreign_keys_are_scoped_for_staff(db):
    kent = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    other = Site.objects.create(name="Other", slug="other", domain="example.com")
    kent_artist = Artist.objects.create(site=kent, name="Kent", slug="kent")
    other_artist = Artist.objects.create(site=other, name="Other", slug="other")
    kent_album = Album.objects.create(site=kent, artist=kent_artist, title="Kent album", slug="kent")
    other_album = Album.objects.create(
        site=other,
        artist=other_artist,
        title="Other album",
        slug="other",
    )
    kent_song = Song.objects.create(site=kent, title="Kent song", slug="kent-song")
    other_song = Song.objects.create(site=other, title="Other song", slug="other-song")
    user = User.objects.create_user(username="editor", is_staff=True)
    user.sites.add(kent)
    request = RequestFactory().get("/admin/music/track/add/")
    request.user = user

    model_admin = admin.site._registry[Track]
    album_field = model_admin.formfield_for_foreignkey(Track._meta.get_field("album"), request)
    song_field = model_admin.formfield_for_foreignkey(Track._meta.get_field("song"), request)

    assert list(album_field.queryset) == [kent_album]
    assert other_album not in album_field.queryset
    assert list(song_field.queryset) == [kent_song]
    assert other_song not in song_field.queryset


def test_photo_collection_item_admin_foreign_keys_are_scoped_for_staff(db):
    kent = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    other = Site.objects.create(name="Other", slug="other", domain="example.com")
    kent_photo = Photo.objects.create(site=kent, title="Kent photo", slug="kent-photo")
    other_photo = Photo.objects.create(site=other, title="Other photo", slug="other-photo")
    kent_collection = PhotoCollection.objects.create(
        site=kent,
        title="Kent collection",
        slug="kent",
    )
    other_collection = PhotoCollection.objects.create(
        site=other,
        title="Other collection",
        slug="other",
    )
    user = User.objects.create_user(username="editor", is_staff=True)
    user.sites.add(kent)
    request = RequestFactory().get("/admin/photos/photocollectionitem/add/")
    request.user = user

    model_admin = admin.site._registry[PhotoCollectionItem]
    collection_field = model_admin.formfield_for_foreignkey(
        PhotoCollectionItem._meta.get_field("collection"),
        request,
    )
    photo_field = model_admin.formfield_for_foreignkey(
        PhotoCollectionItem._meta.get_field("photo"),
        request,
    )

    assert list(collection_field.queryset) == [kent_collection]
    assert other_collection not in collection_field.queryset
    assert list(photo_field.queryset) == [kent_photo]
    assert other_photo not in photo_field.queryset
