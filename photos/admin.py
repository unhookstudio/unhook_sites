from django.contrib import admin

from sites_core.admin import ScopedObjectAdminMixin
from unhook_sites.admin import DomainModelAdmin

from .models import Photo, PhotoCollection, PhotoCollectionItem, PhotoStory


@admin.register(Photo)
class PhotoAdmin(DomainModelAdmin):
    rich_text_fields = ("description_html",)
    list_display = ["title", "site", "date", "category", "photographer", "is_published", "payload_id"]
    list_filter = ["site", "category", "is_published"]
    search_fields = ["title", "slug", "category", "photographer", "payload_id"]
    prepopulated_fields = {"slug": ["title"]}
    autocomplete_fields = ["image"]


@admin.register(PhotoStory)
class PhotoStoryAdmin(DomainModelAdmin):
    rich_text_fields = ("description_html",)
    list_display = ["title", "site", "date", "photographer", "is_published", "payload_id"]
    list_filter = ["site", "is_published"]
    search_fields = ["title", "slug", "photographer", "payload_id"]
    prepopulated_fields = {"slug": ["title"]}
    autocomplete_fields = ["photo"]


class PhotoCollectionItemInline(admin.TabularInline):
    model = PhotoCollectionItem
    extra = 0
    autocomplete_fields = ["photo"]


@admin.register(PhotoCollection)
class PhotoCollectionAdmin(DomainModelAdmin):
    rich_text_fields = ("description_html",)
    list_display = ["title", "site", "subtitle", "is_published", "payload_id"]
    list_filter = ["site", "is_published"]
    search_fields = ["title", "slug", "subtitle", "payload_id"]
    prepopulated_fields = {"slug": ["title"]}
    inlines = [PhotoCollectionItemInline]


@admin.register(PhotoCollectionItem)
class PhotoCollectionItemAdmin(ScopedObjectAdminMixin, admin.ModelAdmin):
    list_display = ["collection", "photo", "order", "caption"]
    list_filter = ["collection__site"]
    search_fields = ["collection__title", "photo__title", "caption"]
    autocomplete_fields = ["collection", "photo"]

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
