from django.urls import reverse


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
    assert "/health/" in response.text
