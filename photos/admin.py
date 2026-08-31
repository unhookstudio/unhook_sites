from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from media_library.admin import image_preview
from sites_core.admin import ScopedObjectAdminMixin
from unhook_sites.admin import DomainModelAdmin

from .models import Photo, PhotoCollection, PhotoCollectionItem, PhotoStory


class PhotoCollectionMembershipInline(TabularInline):
    model = PhotoCollectionItem
    fk_name = "photo"
    extra = 0
    fields = ["collection", "collection_status", "order", "caption"]
    readonly_fields = ["collection_status"]
    autocomplete_fields = ["collection"]
    verbose_name = "collection"
    verbose_name_plural = "collections où apparaît cette photo"

    @admin.display(description="Publiée")
    def collection_status(self, obj):
        if not obj.collection_id:
            return "-"
        return "oui" if obj.collection.is_published else "non"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "collection":
            queryset = PhotoCollection.objects.all()
            photo_id = request.resolver_match.kwargs.get("object_id") if request.resolver_match else None
            if photo_id:
                photo = Photo.objects.filter(pk=photo_id).only("site_id").first()
                if photo:
                    queryset = queryset.filter(site=photo.site)
            elif not request.user.is_superuser:
                queryset = queryset.filter(site__in=request.user.sites.all())
            kwargs["queryset"] = queryset
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Photo)
class PhotoAdmin(DomainModelAdmin):
    rich_text_fields = ("description_html",)
    list_display = [
        "preview",
        "title",
        "site",
        "date",
        "category",
        "photographer",
        "is_published",
        "payload_id",
    ]
    list_filter = ["site", "category", "is_published"]
    search_fields = ["title", "slug", "category", "photographer", "payload_id"]
    prepopulated_fields = {"slug": ["title"]}
    autocomplete_fields = ["image"]
    readonly_fields = [*DomainModelAdmin.readonly_fields, "preview"]
    inlines = [PhotoCollectionMembershipInline]

    @admin.display(description="Aperçu")
    def preview(self, obj):
        if not obj.image:
            return "-"
        return image_preview(obj.image.original)


@admin.register(PhotoStory)
class PhotoStoryAdmin(DomainModelAdmin):
    rich_text_fields = ("description_html",)
    list_display = ["title", "site", "date", "photographer", "is_published", "payload_id"]
    list_filter = ["site", "is_published"]
    search_fields = ["title", "slug", "photographer", "payload_id"]
    prepopulated_fields = {"slug": ["title"]}
    autocomplete_fields = ["image"]


class PhotoCollectionItemInline(TabularInline):
    model = PhotoCollectionItem
    extra = 0
    fields = ["preview", "photo", "order", "caption"]
    readonly_fields = ["preview"]
    autocomplete_fields = ["photo"]

    @admin.display(description="Aperçu")
    def preview(self, obj):
        if not obj.photo_id or not obj.photo.image:
            return "-"
        return image_preview(obj.photo.image.original, width=72)


@admin.register(PhotoCollection)
class PhotoCollectionAdmin(DomainModelAdmin):
    rich_text_fields = ("description_html",)
    list_display = ["title", "site", "subtitle", "is_published", "payload_id"]
    list_filter = ["site", "is_published"]
    search_fields = ["title", "slug", "subtitle", "payload_id"]
    prepopulated_fields = {"slug": ["title"]}
    inlines = [PhotoCollectionItemInline]


@admin.register(PhotoCollectionItem)
class PhotoCollectionItemAdmin(ScopedObjectAdminMixin, ModelAdmin):
    list_display = ["preview", "collection", "photo", "order", "caption"]
    list_filter = ["collection__site"]
    search_fields = ["collection__title", "photo__title", "caption"]
    autocomplete_fields = ["collection", "photo"]

    @admin.display(description="Aperçu")
    def preview(self, obj):
        if not obj.photo.image:
            return "-"
        return image_preview(obj.photo.image.original)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset
        return queryset.filter(collection__site__in=request.user.sites.all())

    def get_list_filter(self, request):
        list_filter = super().get_list_filter(request)
        if request.user.is_superuser:
            return list_filter
        return [item for item in list_filter if item != "collection__site"]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            if db_field.name == "collection":
                kwargs["queryset"] = PhotoCollection.objects.filter(
                    site__in=request.user.sites.all()
                )
            if db_field.name == "photo":
                kwargs["queryset"] = Photo.objects.filter(site__in=request.user.sites.all())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
