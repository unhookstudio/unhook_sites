from events.models import Event


def public_navigation(request):
    site = getattr(request, "site", None)
    if site is None:
        return {"has_published_events": False}

    return {
        "has_published_events": Event.objects.filter(
            site=site,
            is_published=True,
        ).exists()
    }
