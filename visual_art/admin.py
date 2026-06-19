from django.contrib import admin

from unhook_sites.admin import DomainModelAdmin

from .models import BD, Drawing


@admin.register(BD)
class BDAdmin(DomainModelAdmin):
    rich_text_fields = ("description_html",)
    list_display = ["title", "site", "category", "release_date", "is_published", "payload_id"]
    list_filter = ["site", "category", "is_published"]
    search_fields = ["title", "slug", "author", "illustrator", "editor", "payload_id"]
    prepopulated_fields = {"slug": ["title"]}
    autocomplete_fields = ["cover_image", "additional_images"]


@admin.register(Drawing)
class DrawingAdmin(DomainModelAdmin):
    rich_text_fields = ("description_html",)
    list_display = ["title", "site", "release_date", "is_published", "payload_id"]
    list_filter = ["site", "is_published"]
    search_fields = ["title", "slug", "payload_id"]
    prepopulated_fields = {"slug": ["title"]}
    autocomplete_fields = ["images"]
