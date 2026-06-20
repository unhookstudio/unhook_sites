from django.urls import reverse
from django.contrib.staticfiles.finders import find


def test_robots_txt(client):
    response = client.get(reverse("robots"))

    assert response.status_code == 200
    assert response["content-type"] == "text/plain"
    assert "Sitemap:" in response.text


def test_sitemap_xml(client):
    response = client.get(reverse("sitemap"))

    assert response.status_code == 200
    assert response["content-type"] == "application/xml"
    assert "<urlset" in response.text
    assert "/health/" not in response.text


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
