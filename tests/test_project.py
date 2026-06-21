from django.urls import reverse
from django.contrib.staticfiles.finders import find

from music.models import Album, Artist, Song
from sites_core.models import Site
from writing.models import Book


def test_robots_txt(client):
    response = client.get(reverse("robots"))

    assert response.status_code == 200
    assert response["content-type"] == "text/plain"
    assert "Sitemap:" in response.text


def test_sitemap_xml_lists_current_site_public_urls(client, db, settings):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    kent = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    artist = Artist.objects.create(site=kent, name="Kent", slug="kent")
    Album.objects.create(
        site=kent,
        artist=artist,
        title="Kent album",
        slug="kent-album",
        is_published=True,
    )
    Song.objects.create(site=kent, title="Kent song", slug="kent-song", is_published=True)
    Book.objects.create(site=kent, title="Kent book", slug="kent-book", is_published=True)

    response = client.get(reverse("sitemap"), HTTP_HOST="kent-artiste.com")

    assert response.status_code == 200
    assert response["content-type"] == "application/xml"
    assert "<urlset" in response.text
    assert "http://kent-artiste.com/" in response.text
    assert "http://kent-artiste.com/musique" in response.text
    assert "http://kent-artiste.com/album/kent-album" in response.text
    assert "http://kent-artiste.com/chanson/kent-song" in response.text
    assert "http://kent-artiste.com/livres/kent-book" in response.text
    assert "/health/" not in response.text
    assert "/admin/" not in response.text


def test_sitemap_xml_does_not_list_other_site_content(client, db, settings):
    settings.ALLOWED_HOSTS = ["kent-artiste.com", "other.example.com"]
    kent = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    other = Site.objects.create(name="Other", slug="other", domain="other.example.com")
    kent_artist = Artist.objects.create(site=kent, name="Kent", slug="kent")
    other_artist = Artist.objects.create(site=other, name="Other", slug="other")
    Album.objects.create(
        site=kent,
        artist=kent_artist,
        title="Kent album",
        slug="kent-album",
        is_published=True,
    )
    Album.objects.create(
        site=other,
        artist=other_artist,
        title="Other album",
        slug="other-album",
        is_published=True,
    )

    response = client.get(reverse("sitemap"), HTTP_HOST="kent-artiste.com")

    assert response.status_code == 200
    assert "http://kent-artiste.com/album/kent-album" in response.text
    assert "other-album" not in response.text


def test_kent_static_assets_are_discoverable():
    assert find("kent/css/site.css") is not None
    assert find("kent/assets/au_fil.svg") is not None
    assert find("kent/assets/actualite.svg") is not None
    assert find("kent/assets/line_horizontal_squiggly.svg") is not None
    assert find("kent/assets/line_horizontal_straight.svg") is not None
    assert find("kent/assets/musiquev.svg") is not None


def test_kent_base_uses_configured_youtube_embed():
    with open("templates/kent_site/base.html", encoding="utf-8") as template_file:
        template = template_file.read()

    assert "https://www.youtube.com/embed/" in template
    assert "origin=\" + encodeURIComponent(window.location.origin)" in template
    assert 'iframe.referrerPolicy = "strict-origin-when-cross-origin"' in template
