from events.models import Event
from sites_core.models import SiteSettings, TextSnippet

from .content_defaults import DEFAULT_SITE_COPY, DEFAULT_TEXT_SNIPPETS


def public_navigation(request):
    site = getattr(request, "site", None)
    if site is None:
        return {
            "has_published_events": False,
            "site_copy": DEFAULT_SITE_COPY,
            "site_settings": None,
            "text_snippets": DEFAULT_TEXT_SNIPPETS,
        }

    site_settings = SiteSettings.objects.filter(site=site).first()
    site_copy = dict(DEFAULT_SITE_COPY)
    if site_settings is not None:
        for key in site_copy:
            value = getattr(site_settings, key, "")
            if value:
                site_copy[key] = value

    text_snippets = dict(DEFAULT_TEXT_SNIPPETS)
    for snippet in TextSnippet.objects.filter(site=site).only("key", "text"):
        if snippet.text:
            text_snippets[snippet.key] = snippet.text

    return {
        "has_published_events": Event.objects.filter(
            site=site,
            is_published=True,
        ).exists(),
        "site_copy": site_copy,
        "site_settings": site_settings,
        "text_snippets": text_snippets,
    }
