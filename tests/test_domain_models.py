from django.contrib import admin
from django.contrib.auth.models import Permission
from django.db import IntegrityError
from django.test import RequestFactory
from django.urls import reverse
import pytest

from media_library.models import Image
from music.models import Album, Artist, Song, Track
from photos.models import Photo, PhotoCollection, PhotoCollectionItem, PhotoStory
from sites_core.models import Site, User
from visual_art.models import BD, Drawing
from writing.models import Article, Book


def test_publishable_domain_model_sets_publish_state_without_saving(db):
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    article = Article.objects.create(site=site, title="News", slug="news")

    article.publish()

    assert article.is_published is True
    assert article.published_at is not None
    article.refresh_from_db()
    assert article.is_published is False


def test_book_keeps_specific_model_with_flexible_page_placement(db):
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")

    book = Book.objects.create(
        site=site,
        title="Illustrated Book",
        slug="illustrated-book",
        category=Book.Category.ILLUSTRATED,
        show_on_books_page=True,
        show_on_drawings_page=True,
    )

    assert book.show_on_books_page is True
    assert book.show_on_drawings_page is True


def test_bd_drawing_and_book_are_separate_models(db):
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")

    book = Book.objects.create(site=site, title="Book", slug="book")
    bd = BD.objects.create(site=site, title="BD", slug="bd")
    drawing = Drawing.objects.create(site=site, title="Drawing", slug="drawing")

    assert str(book) == "Book"
    assert str(bd) == "BD"
    assert str(drawing) == "Drawing"


def test_payload_rich_text_json_is_preserved_alongside_html(db):
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    payload_content = {"root": {"children": [{"type": "paragraph"}]}}

    article = Article.objects.create(
        site=site,
        title="News",
        slug="news",
        content_html="<p>News</p>",
        payload_content=payload_content,
    )

    assert article.content_html == "<p>News</p>"
    assert article.payload_content == payload_content


def test_domain_model_can_reference_media_library_image(db):
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    image = Image.objects.create(site=site, title="Cover")

    book = Book.objects.create(site=site, title="Book", slug="book", cover_image=image)

    assert book.cover_image == image


def test_photo_story_uses_image_field_for_payload_upload_media(db):
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    image = Image.objects.create(site=site, title="Story image")

    story = PhotoStory.objects.create(site=site, title="Story", slug="story", image=image)

    assert story.image == image


def test_track_payload_id_is_unique_for_idempotent_import(db):
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    artist = Artist.objects.create(site=site, name="Kent", slug="kent")
    album = Album.objects.create(site=site, artist=artist, title="Album", slug="album")
    first_song = Song.objects.create(site=site, title="First", slug="first")
    second_song = Song.objects.create(site=site, title="Second", slug="second")
    Track.objects.create(album=album, song=first_song, track_number=1, payload_id=10)

    with pytest.raises(IntegrityError):
        Track.objects.create(album=album, song=second_song, track_number=2, payload_id=10)


def test_payload_json_fields_are_readonly_for_non_superuser_admin(db):
    user = User.objects.create_user(username="editor", is_staff=True)
    request = RequestFactory().get("/admin/writing/article/add/")
    request.user = user

    readonly_fields = admin.site._registry[Article].get_readonly_fields(request)

    assert "payload_content" in readonly_fields


def test_payload_json_fields_remain_editable_for_superuser_admin(db):
    user = User.objects.create_superuser(username="admin")
    request = RequestFactory().get("/admin/writing/article/add/")
    request.user = user

    readonly_fields = admin.site._registry[Article].get_readonly_fields(request)

    assert "payload_content" not in readonly_fields


def test_domain_admin_changelist_and_detail_are_scoped_for_staff(client, db):
    kent = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    other = Site.objects.create(name="Other", slug="other", domain="example.com")
    kent_article = Article.objects.create(site=kent, title="Kent article", slug="kent-article")
    other_article = Article.objects.create(site=other, title="Other article", slug="other-article")
    user = User.objects.create_user(username="editor", password="password", is_staff=True)
    user.sites.add(kent)
    user.user_permissions.add(
        Permission.objects.get(codename="view_article"),
        Permission.objects.get(codename="change_article"),
    )

    client.force_login(user)

    changelist = client.get(reverse("admin:writing_article_changelist"))
    other_detail = client.get(reverse("admin:writing_article_change", args=[other_article.pk]))

    assert changelist.status_code == 200
    assert kent_article.title in changelist.text
    assert other_article.title not in changelist.text
    assert other_detail.status_code == 404


def test_track_admin_changelist_and_detail_are_scoped_for_staff(client, db):
    kent = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    other = Site.objects.create(name="Other", slug="other", domain="example.com")
    kent_artist = Artist.objects.create(site=kent, name="Kent", slug="kent")
    other_artist = Artist.objects.create(site=other, name="Other", slug="other")
    kent_album = Album.objects.create(site=kent, artist=kent_artist, title="Kent album", slug="kent-album")
    other_album = Album.objects.create(
        site=other,
        artist=other_artist,
        title="Other album",
        slug="other-album",
    )
    kent_song = Song.objects.create(site=kent, title="Kent song", slug="kent-song")
    other_song = Song.objects.create(site=other, title="Other song", slug="other-song")
    Track.objects.create(
        album=kent_album,
        song=kent_song,
        track_number=1,
        display_title="Kent track",
    )
    other_track = Track.objects.create(
        album=other_album,
        song=other_song,
        track_number=1,
        display_title="Other track",
    )
    user = User.objects.create_user(username="editor", password="password", is_staff=True)
    user.sites.add(kent)
    user.user_permissions.add(
        Permission.objects.get(codename="view_track"),
        Permission.objects.get(codename="change_track"),
    )

    client.force_login(user)

    changelist = client.get(reverse("admin:music_track_changelist"))
    other_detail = client.get(reverse("admin:music_track_change", args=[other_track.pk]))

    assert changelist.status_code == 200
    assert kent_album.title in changelist.text
    assert other_album.title not in changelist.text
    assert "album__site__id__exact" not in changelist.text
    assert other_detail.status_code == 404


def test_photo_collection_item_admin_changelist_and_detail_are_scoped_for_staff(client, db):
    kent = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    other = Site.objects.create(name="Other", slug="other", domain="example.com")
    kent_photo = Photo.objects.create(site=kent, title="Kent photo", slug="kent-photo")
    other_photo = Photo.objects.create(site=other, title="Other photo", slug="other-photo")
    kent_collection = PhotoCollection.objects.create(
        site=kent,
        title="Kent collection",
        slug="kent-collection",
    )
    other_collection = PhotoCollection.objects.create(
        site=other,
        title="Other collection",
        slug="other-collection",
    )
    kent_item = PhotoCollectionItem.objects.create(
        collection=kent_collection,
        photo=kent_photo,
        caption="Kent item",
    )
    other_item = PhotoCollectionItem.objects.create(
        collection=other_collection,
        photo=other_photo,
        caption="Other item",
    )
    user = User.objects.create_user(username="editor", password="password", is_staff=True)
    user.sites.add(kent)
    user.user_permissions.add(
        Permission.objects.get(codename="view_photocollectionitem"),
        Permission.objects.get(codename="change_photocollectionitem"),
    )

    client.force_login(user)

    changelist = client.get(reverse("admin:photos_photocollectionitem_changelist"))
    other_detail = client.get(
        reverse("admin:photos_photocollectionitem_change", args=[other_item.pk])
    )

    assert changelist.status_code == 200
    assert kent_item.caption in changelist.text
    assert other_item.caption not in changelist.text
    assert "collection__site__id__exact" not in changelist.text
    assert other_detail.status_code == 404
