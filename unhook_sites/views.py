from xml.etree.ElementTree import Element, SubElement, tostring

from django.http import Http404, HttpRequest, HttpResponse
from django.urls import reverse

from .sitemaps import entries_for_site


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


def sitemap_xml(request: HttpRequest) -> HttpResponse:
    if request.site is None:
        raise Http404("Site not configured")

    urlset = Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for entry in entries_for_site(request.site):
        url = SubElement(urlset, "url")
        SubElement(url, "loc").text = request.build_absolute_uri(entry.path)
        if entry.lastmod is not None:
            SubElement(url, "lastmod").text = entry.lastmod.date().isoformat()
        SubElement(url, "changefreq").text = entry.changefreq
        SubElement(url, "priority").text = entry.priority

    xml = tostring(urlset, encoding="utf-8", xml_declaration=True)
    return HttpResponse(xml, content_type="application/xml")
