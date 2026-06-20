from django.urls import reverse

from music.models import Album, Artist, Song, Track, VideoClip
from events.models import Event
from sites_core.models import Site, SiteSettings
from writing.models import Article, Book


def test_public_home_uses_site_from_request_host(client, db, settings):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    kent = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    other = Site.objects.create(name="Other", slug="other", domain="example.com")
    Article.objects.create(site=kent, title="Kent article", slug="kent-article", is_published=True)
    Article.objects.create(site=other, title="Other article", slug="other-article", is_published=True)

    response = client.get(reverse("home"), HTTP_HOST="kent-artiste.com")

    assert response.status_code == 200
    assert "Kent article" in response.text
    assert "Other article" not in response.text


def test_public_home_falls_back_to_kent_for_localhost(client, db):
    Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")

    response = client.get(reverse("home"), HTTP_HOST="localhost")

    assert response.status_code == 200


def test_public_base_loads_kent_scoped_stylesheet(client, db, settings):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")

    response = client.get(reverse("home"), HTTP_HOST="kent-artiste.com")

    assert response.status_code == 200
    assert 'class="site site--kent"' in response.text
    assert "/static/kent/css/site.css" in response.text


def test_home_renders_news_cards_like_original_layout(client, db, settings):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    Article.objects.create(
        site=site,
        title="Journal entry",
        slug="journal-entry",
        category=Article.Category.NEWS,
        content_plain="A readable excerpt for the news card.",
        is_published=True,
    )

    response = client.get(reverse("home"), HTTP_HOST="kent-artiste.com")

    assert response.status_code == 200
    assert 'class="news-card"' in response.text
    assert "au_fil_derniers.svg" in response.text
    assert "Actualités" in response.text
    assert "News" not in response.text
    assert "A readable excerpt for the news card." in response.text


def test_home_renders_actualites_section_with_image_left_layout(client, db, settings):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    Event.objects.create(site=site, title="Concert", slug="concert", is_published=True)

    response = client.get(reverse("home"), HTTP_HOST="kent-artiste.com")

    assert response.status_code == 200
    assert "home-dates__grid" in response.text
    assert "home-dates__image" in response.text
    assert "home-date-card" in response.text
    assert "line_horizontal_squiggly.svg" in response.text
    assert "section-title-mask section-title--dates" in response.text


def test_home_does_not_render_hero_without_site_setting_checkbox(client, db, settings):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    SiteSettings.objects.create(site=site, show_homepage_hero=False)

    response = client.get(reverse("home"), HTTP_HOST="kent-artiste.com")

    assert response.status_code == 200
    assert '<section class="home-hero"' not in response.text


def test_home_renders_hero_when_site_setting_checkbox_is_enabled(client, db, settings):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    SiteSettings.objects.create(
        site=site,
        show_homepage_hero=True,
        homepage_hero_text="Custom hero",
        homepage_hero_button_text="Découvrir",
        homepage_hero_button_url="/a-propos",
    )

    response = client.get(reverse("home"), HTTP_HOST="kent-artiste.com")

    assert response.status_code == 200
    assert "home-hero" in response.text
    assert "kent_cut.webp" in response.text
    assert "Custom hero" in response.text
    assert "Découvrir" in response.text


def test_home_renders_newsletter_and_quick_links(client, db, settings):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")

    response = client.get(reverse("home"), HTTP_HOST="kent-artiste.com")

    assert response.status_code == 200
    assert 'id="newsletter"' in response.text
    assert "actualite.svg" in response.text
    assert "kent_gauche.jpg" in response.text
    assert "Oui, je veux la newslettre" in response.text
    assert "line_horizontal_straight.svg" in response.text
    assert "quick-link-card--music" in response.text
    assert "quick-link-card--drawings" in response.text
    assert "quick-link-card--books" in response.text


def test_newsletter_signup_redirects_to_home_anchor(client, db, settings):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")

    response = client.post(
        reverse("newsletter_signup"),
        {"email": "reader@example.com"},
        HTTP_HOST="kent-artiste.com",
    )

    assert response.status_code == 302
    assert response["Location"] == "/?newsletter=success#newsletter"


def test_musique_lists_only_published_site_albums(client, db, settings):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    artist = Artist.objects.create(site=site, name="Kent", slug="kent")
    Album.objects.create(
        site=site,
        artist=artist,
        title="Published album",
        slug="published-album",
        is_published=True,
    )
    Album.objects.create(
        site=site,
        artist=artist,
        title="Draft album",
        slug="draft-album",
        is_published=False,
    )

    response = client.get(reverse("musique"), HTTP_HOST="kent-artiste.com")

    assert response.status_code == 200
    assert "Published album" in response.text
    assert "Draft album" not in response.text


def test_musique_shows_album_preview_disclosure_and_video_cards(client, db, settings):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    artist = Artist.objects.create(site=site, name="Kent", slug="kent")
    for index in range(8):
        Album.objects.create(
            site=site,
            artist=artist,
            title=f"Album {index}",
            slug=f"album-{index}",
            is_published=True,
            category=Album.Category.COMMERCIAL,
        )
    VideoClip.objects.create(
        site=site,
        title="Clip",
        slug="clip",
        video_id="abc123",
        is_published=True,
    )

    response = client.get(reverse("musique"), HTTP_HOST="kent-artiste.com")

    assert response.status_code == 200
    assert "quote--musique" in response.text
    assert "music-disclosure" in response.text
    assert "data-music-albums-expand" in response.text
    assert "data-music-albums-collapse" in response.text
    assert "Voir tout (8 albums)" in response.text
    assert "Voir moins" in response.text
    assert 'class="music-album-grid music-album-grid--continued" hidden' in response.text
    assert "music-video-card" in response.text
    assert "https://img.youtube.com/vi/abc123/hqdefault.jpg" in response.text
    assert "music-video-card__play" in response.text


def test_home_renders_featured_album_panel(client, db, settings):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    artist = Artist.objects.create(site=site, name="Kent", slug="kent")
    Album.objects.create(
        site=site,
        artist=artist,
        title="Featured album",
        slug="featured-album",
        is_published=True,
        label="Label",
    )

    response = client.get(reverse("home"), HTTP_HOST="kent-artiste.com")

    assert response.status_code == 200
    assert "featured-album" in response.text
    assert "Voir la discographie" in response.text
    assert "Featured album" in response.text
    assert "section-title-mask section-title--album" in response.text


def test_album_detail_shows_tracks(client, db, settings):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    artist = Artist.objects.create(site=site, name="Kent", slug="kent")
    album = Album.objects.create(
        site=site,
        artist=artist,
        title="Album",
        slug="album",
        is_published=True,
    )
    song = Song.objects.create(site=site, title="Song", slug="song", is_published=True)
    Track.objects.create(album=album, song=song, track_number=1)

    response = client.get(reverse("album_detail", args=["album"]), HTTP_HOST="kent-artiste.com")

    assert response.status_code == 200
    assert "Album" in response.text
    assert "Song" in response.text


def test_livres_uses_book_page_placement_flag(client, db, settings):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    Book.objects.create(
        site=site,
        title="Visible book",
        slug="visible-book",
        is_published=True,
        show_on_books_page=True,
    )
    Book.objects.create(
        site=site,
        title="Drawings only book",
        slug="drawings-only-book",
        is_published=True,
        show_on_books_page=False,
        show_on_drawings_page=True,
    )

    response = client.get(reverse("livres"), HTTP_HOST="kent-artiste.com")

    assert response.status_code == 200
    assert "Visible book" in response.text
    assert "Drawings only book" not in response.text


def test_post_detail_404s_for_drafts(client, db, settings):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    Article.objects.create(site=site, title="Draft", slug="draft", is_published=False)

    response = client.get(reverse("post_detail", args=["draft"]), HTTP_HOST="kent-artiste.com")

    assert response.status_code == 404
