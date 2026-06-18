from django.http import HttpRequest, HttpResponse
from django.urls import reverse


def robots_txt(request: HttpRequest) -> HttpResponse:
    sitemap_url = request.build_absolute_uri(reverse("sitemap"))
    lines = [
        "User-agent: *",
        "Allow: /",
        f"Sitemap: {sitemap_url}",
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")


def health_check(request: HttpRequest) -> HttpResponse:
    return HttpResponse("ok\n", content_type="text/plain")
