from django.contrib import admin
from django.utils.html import format_html

from sites_core.admin import ScopedObjectAdminMixin, SiteScopedAdmin

from .models import Image, ImageVariant


def image_preview(field_file, *, width: int = 96) -> str:
    if not field_file:
        return "-"
    try:
        url = field_file.url
    except ValueError:
        return "-"
    return format_html(
        '<img src="{}" alt="" style="max-width: {}px; max-height: {}px; height: auto;" />',
        url,
        width,
        width,
    )


class ImageVariantInline(admin.TabularInline):
    model = ImageVariant
    extra = 0
    fields = [
        "preview",
        "kind",
        "payload_kind",
        "file",
        "width",
        "height",
        "filesize",
        "payload_url",
    ]
    readonly_fields = ["preview", "payload_kind", "width", "height", "filesize", "payload_url"]

    @admin.display(description="Preview")
    def preview(self, obj):
        return image_preview(obj.file, width=72)


@admin.register(Image)
class ImageAdmin(SiteScopedAdmin):
    list_display = ["preview", "__str__", "site", "width", "height", "filesize", "payload_id"]
    list_filter = ["site", "mime_type"]
    search_fields = ["title", "alt_text", "filename", "payload_id"]
    readonly_fields = [
        "preview",
        "payload_id",
        "payload_url",
        "payload_thumbnail_url",
        "payload_created_at",
        "payload_updated_at",
        "created_at",
        "updated_at",
    ]
    inlines = [ImageVariantInline]

    @admin.display(description="Preview")
    def preview(self, obj):
        return image_preview(obj.original)


@admin.register(ImageVariant)
class ImageVariantAdmin(ScopedObjectAdminMixin, admin.ModelAdmin):
    list_display = ["preview", "image", "kind", "payload_kind", "width", "height", "filesize"]
    list_filter = ["image__site", "kind", "mime_type"]
    readonly_fields = ["preview", "payload_kind"]
    search_fields = ["image__title", "image__filename", "filename", "payload_kind", "payload_url"]

    @admin.display(description="Preview")
    def preview(self, obj):
        return image_preview(obj.file)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset
        return queryset.filter(image__site__in=request.user.sites.all())

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "image" and not request.user.is_superuser:
            kwargs["queryset"] = Image.objects.filter(site__in=request.user.sites.all())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_list_filter(self, request):
        list_filter = super().get_list_filter(request)
        if request.user.is_superuser:
            return list_filter
        return [item for item in list_filter if item != "image__site"]
