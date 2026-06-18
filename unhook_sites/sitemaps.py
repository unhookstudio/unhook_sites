from django.contrib.sitemaps import Sitemap

class StaticViewSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.5

    def items(self):
        return []

    def location(self, item):
        return item
