from django.http import HttpRequest, HttpResponse
from django.urls import reverse


def canonical_url(request: HttpRequest, viewname: str, *args: object, **kwargs: object) -> str:
    return request.build_absolute_uri(reverse(viewname, args=args, kwargs=kwargs))


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
