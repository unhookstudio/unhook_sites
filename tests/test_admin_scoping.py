from django.contrib import admin
from django.contrib.auth.models import Permission
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone
from django_prose_editor.widgets import AdminProseEditorWidget

from events.admin import EventAdminForm
from events.models import Event
from music.models import Album, Artist, Song, Track, VideoClip
from photos.models import Photo, PhotoCollection, PhotoCollectionItem
from sites_core.admin import TextSnippetAdminForm
from sites_core.models import NavigationLink, Site, SiteSettings, TextSnippet, User
from writing.admin import ArticleAdminForm
from writing.models import Article


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


def test_site_settings_dates_description_uses_rich_text_editor(db):
    user = User.objects.create_superuser(username="admin")
    request = RequestFactory().get("/admin/sites_core/site/add/")
    request.user = user
    inline = admin.site._registry[Site].inlines[0](Site, admin.site)

    field = inline.formfield_for_dbfield(
        SiteSettings._meta.get_field("dates_description"),
        request,
    )

    assert isinstance(field.widget, AdminProseEditorWidget)


def test_site_settings_inline_uses_french_editor_labels(db):
    user = User.objects.create_superuser(username="admin")
    request = RequestFactory().get("/admin/sites_core/site/add/")
    request.user = user
    inline = admin.site._registry[Site].inlines[0](Site, admin.site)

    labels = {
        field_name: inline.formfield_for_dbfield(
            SiteSettings._meta.get_field(field_name),
            request,
        ).label
        for field_name in [
            "newsletter_text",
            "contact_title",
            "show_homepage_hero",
            "homepage_hero_image",
            "homepage_hero_button_url",
            "favicon_svg",
        ]
    }

    assert labels == {
        "newsletter_text": "Texte newsletter",
        "contact_title": "Titre contact",
        "show_homepage_hero": "Afficher l'image d'accueil",
        "homepage_hero_image": "Image d'accueil",
        "homepage_hero_button_url": "Lien du bouton d'accueil",
        "favicon_svg": "Favicon SVG",
    }


def test_about_biography_text_snippet_uses_rich_text_editor(db):
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    snippet = TextSnippet.objects.create(
        site=site,
        key="about_biography",
        label="À propos - biographie",
        text="<p>Bio.</p>",
    )

    form = TextSnippetAdminForm(instance=snippet)

    assert isinstance(form.fields["text"].widget, AdminProseEditorWidget)
    assert form.fields["text"].widget.attrs["rows"] == 10


def test_admin_language_is_forced_to_french(client, db):
    User.objects.create_superuser(username="admin", password="password")
    client.login(username="admin", password="password")

    response = client.get(
        reverse("admin:index"),
        HTTP_ACCEPT_LANGUAGE="en-US,en;q=0.9",
    )

    assert response.status_code == 200
    assert '<html lang="fr-fr"' in response.text
    assert "Gestion du site" in response.text
    assert "Site administration" not in response.text


def test_event_admin_add_form_uses_french_editor_labels(db):
    user = User.objects.create_superuser(username="admin")
    request = RequestFactory().get("/admin/events/event/add/")
    request.user = user
    model_admin = admin.site._registry[Event]

    labels = {
        field_name: model_admin.formfield_for_dbfield(
            Event._meta.get_field(field_name),
            request,
        ).label
        for field_name in ["title", "end_date", "hide_time", "location_details", "is_published"]
    }

    assert labels == {
        "title": "Titre",
        "end_date": "Date de fin",
        "hide_time": "Masquer l'heure",
        "location_details": "Lieu / ville",
        "is_published": "Publié",
    }


def test_video_clip_admin_add_form_uses_french_editor_labels(db):
    user = User.objects.create_superuser(username="admin")
    request = RequestFactory().get("/admin/music/videoclip/add/")
    request.user = user
    model_admin = admin.site._registry[VideoClip]

    labels = {
        field_name: model_admin.formfield_for_dbfield(
            VideoClip._meta.get_field(field_name),
            request,
        ).label
        for field_name in ["title", "description_html", "video_id", "thumbnail", "sort_order"]
    }

    assert labels == {
        "title": "Titre",
        "description_html": "Description",
        "video_id": "ID vidéo YouTube",
        "thumbnail": "Miniature",
        "sort_order": "Ordre d'affichage",
    }


def test_event_admin_form_accepts_date_without_time_and_hides_time(db):
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    form = EventAdminForm(
        data={
            "site": str(site.pk),
            "title": "La comédie du livre",
            "slug": "la-comedie-du-livre",
            "date_0": "2026-05-22",
            "date_1": "",
            "end_date_0": "",
            "end_date_1": "",
            "url": "",
            "location_details": "Montpellier",
            "description_html": "",
        }
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["date"] == timezone.make_aware(
        timezone.datetime(2026, 5, 22, 0, 0)
    )
    assert form.cleaned_data["hide_time"] is True


def test_event_admin_form_keeps_time_visible_when_time_is_entered(db):
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    form = EventAdminForm(
        data={
            "site": str(site.pk),
            "title": "Librairie Expérience",
            "slug": "librairie-experience",
            "date_0": "2026-05-29",
            "date_1": "17:30",
            "end_date_0": "",
            "end_date_1": "",
            "url": "",
            "location_details": "Lyon",
            "description_html": "",
        }
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["date"] == timezone.make_aware(
        timezone.datetime(2026, 5, 29, 17, 30)
    )
    assert form.cleaned_data["hide_time"] is False


def test_event_admin_form_uses_browser_date_and_time_inputs(db):
    form = EventAdminForm()

    rendered = str(form["date"])

    assert 'type="date"' in rendered
    assert 'type="time"' in rendered
    assert 'step="60"' in rendered


def test_article_admin_add_form_uses_french_editor_labels(db):
    user = User.objects.create_superuser(username="admin")
    request = RequestFactory().get("/admin/writing/article/add/")
    request.user = user
    model_admin = admin.site._registry[Article]

    labels = {
        field_name: model_admin.formfield_for_dbfield(
            Article._meta.get_field(field_name),
            request,
        ).label
        for field_name in ["title", "content_html", "category", "featured_image", "is_published"]
    }

    assert labels == {
        "title": "Titre",
        "content_html": "Contenu",
        "category": "Catégorie",
        "featured_image": "Image",
        "is_published": "Publié",
    }


def test_article_admin_form_accepts_publication_date_without_time_as_3pm(db):
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    form = ArticleAdminForm(
        data={
            "site": str(site.pk),
            "title": "Journal",
            "slug": "journal",
            "published_at_0": "2026-05-22",
            "published_at_1": "",
            "content_html": "<p>Texte</p>",
            "category": Article.Category.NEWS,
            "meta_title": "",
            "meta_description": "",
        }
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["published_at"] == timezone.make_aware(
        timezone.datetime(2026, 5, 22, 15, 0)
    )


def test_article_admin_form_hides_plain_text_and_uses_larger_content_editor(db):
    form = ArticleAdminForm()

    assert "content_plain" not in form.fields
    assert isinstance(form.fields["content_html"].widget, AdminProseEditorWidget)
    assert form.fields["content_html"].widget.attrs["rows"] == 8
    assert form.fields["content_html"].widget.attrs["style"] == "min-height: 12rem;"


def test_article_admin_form_uses_browser_date_and_time_inputs(db):
    form = ArticleAdminForm()

    rendered = str(form["published_at"])

    assert 'type="date"' in rendered
    assert 'type="time"' in rendered
    assert 'step="60"' in rendered


def test_article_admin_syncs_plain_text_when_saved(db):
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    user = User.objects.create_superuser(username="admin")
    request = RequestFactory().post("/admin/writing/article/add/")
    request.user = user
    form = ArticleAdminForm(
        data={
            "site": str(site.pk),
            "title": "Journal",
            "slug": "journal",
            "published_at_0": "",
            "published_at_1": "",
            "content_html": "<p>Un <strong>texte</strong>&nbsp;lié.</p>",
            "category": Article.Category.NEWS,
            "meta_title": "",
            "meta_description": "",
        }
    )

    assert form.is_valid(), form.errors
    article = form.save(commit=False)
    admin.site._registry[Article].save_model(request, article, form, change=False)

    assert article.content_plain == "Un texte lié."


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
