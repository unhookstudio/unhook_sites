from events.models import Event
from sites_core.models import SiteSettings


def public_navigation(request):
    site = getattr(request, "site", None)
    if site is None:
        return {"has_published_events": False, "site_settings": None}

    return {
        "has_published_events": Event.objects.filter(
            site=site,
            is_published=True,
        ).exists(),
        "site_settings": SiteSettings.objects.filter(site=site).first(),
    }
