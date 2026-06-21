from django.contrib import admin
from django.utils.html import format_html_join

from media_library.admin import image_preview
from unhook_sites.admin import DomainModelAdmin

from .models import BD, Drawing


@admin.register(BD)
class BDAdmin(DomainModelAdmin):
    rich_text_fields = ("description_html",)
    list_display = [
        "cover_preview",
        "title",
        "site",
        "category",
        "release_date",
        "is_published",
        "payload_id",
    ]
    list_filter = ["site", "category", "is_published"]
    search_fields = ["title", "slug", "author", "illustrator", "editor", "payload_id"]
    prepopulated_fields = {"slug": ["title"]}
    autocomplete_fields = ["cover_image", "additional_images"]
    readonly_fields = [*DomainModelAdmin.readonly_fields, "cover_preview"]

    @admin.display(description="Couverture")
    def cover_preview(self, obj):
        if not obj.cover_image:
            return "-"
        return image_preview(obj.cover_image.original)


@admin.register(Drawing)
class DrawingAdmin(DomainModelAdmin):
    rich_text_fields = ("description_html",)
    list_display = ["images_preview", "title", "site", "release_date", "is_published", "payload_id"]
    list_filter = ["site", "is_published"]
    search_fields = ["title", "slug", "payload_id"]
    prepopulated_fields = {"slug": ["title"]}
    autocomplete_fields = ["images"]
    readonly_fields = [*DomainModelAdmin.readonly_fields, "images_preview"]

    @admin.display(description="Images")
    def images_preview(self, obj):
        images = list(obj.images.all()[:4])
        if not images:
            return "-"
        return format_html_join(
            "",
            '<span style="display: inline-block; margin-right: 4px;">{}</span>',
            ((image_preview(image.original, width=72),) for image in images),
        )
