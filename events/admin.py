from django.contrib import admin

from unhook_sites.admin import DomainModelAdmin

from .models import Event, KeyDate


@admin.register(Event)
class EventAdmin(DomainModelAdmin):
    rich_text_fields = ("description_html",)
    list_display = ["title", "site", "date", "is_published", "payload_id"]
    list_filter = ["site", "is_published"]
    search_fields = ["title", "slug", "payload_id"]
    prepopulated_fields = {"slug": ["title"]}


@admin.register(KeyDate)
class KeyDateAdmin(DomainModelAdmin):
    rich_text_fields = ("description_html",)
    list_display = ["title", "site", "date", "is_published", "payload_id"]
    list_filter = ["site", "is_published"]
    search_fields = ["title", "slug", "payload_id"]
    prepopulated_fields = {"slug": ["title"]}
