from sites_core.models import Site


class CurrentSiteMiddleware:
    """Resolve the public Site for each request from the request host."""

    skipped_prefixes = (
        "/admin/",
        "/health/",
        "/robots.txt",
        "/sitemap.xml",
        "/static/",
        "/media/",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.site = None if self._should_skip(request.path_info) else self._resolve_site(request)
        return self.get_response(request)

    def _should_skip(self, path: str) -> bool:
        return any(path.startswith(prefix) for prefix in self.skipped_prefixes)

    def _resolve_site(self, request) -> Site:
        host = request.get_host().split(":", 1)[0].lower()
        site = Site.objects.filter(domain__iexact=host, is_active=True).first()
        if site is not None:
            return site

        fallback = Site.objects.filter(slug="kent", is_active=True).first()
        if fallback is not None:
            return fallback

        return None
