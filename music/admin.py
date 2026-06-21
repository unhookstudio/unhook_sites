from django.contrib import admin

from media_library.admin import image_preview
from sites_core.admin import ScopedObjectAdminMixin
from unhook_sites.admin import DomainModelAdmin

from .models import Album, Artist, Song, Track, VideoClip


class TrackInline(admin.TabularInline):
    model = Track
    extra = 0
    autocomplete_fields = ["song"]


@admin.register(Artist)
class ArtistAdmin(DomainModelAdmin):
    list_display = ["name", "site", "payload_id"]
    list_filter = ["site"]
    search_fields = ["name", "slug", "payload_id"]
    prepopulated_fields = {"slug": ["name"]}


@admin.register(Album)
class AlbumAdmin(DomainModelAdmin):
    rich_text_fields = ("description_html", "credits_html")
    list_display = [
        "cover_preview",
        "title",
        "site",
        "artist",
        "category",
        "release_date",
        "is_published",
        "payload_id",
    ]
    list_filter = ["site", "artist", "category", "is_published"]
    search_fields = ["title", "slug", "label", "payload_id"]
    prepopulated_fields = {"slug": ["title"]}
    autocomplete_fields = ["artist", "cover_image", "additional_images"]
    readonly_fields = [*DomainModelAdmin.readonly_fields, "cover_preview"]
    inlines = [TrackInline]

    @admin.display(description="Cover")
    def cover_preview(self, obj):
        if not obj.cover_image:
            return "-"
        return image_preview(obj.cover_image.original)


@admin.register(Song)
class SongAdmin(DomainModelAdmin):
    rich_text_fields = ("description_html", "lyrics_html")
    list_display = ["title", "site", "composer", "lyricist", "is_published", "payload_id"]
    list_filter = ["site", "is_published"]
    search_fields = ["title", "slug", "composer", "lyricist", "payload_id"]
    prepopulated_fields = {"slug": ["title"]}


@admin.register(Track)
class TrackAdmin(ScopedObjectAdminMixin, admin.ModelAdmin):
    list_display = ["album", "song", "disc_number", "track_number", "version_type", "payload_id"]
    list_filter = ["album__site", "version_type"]
    search_fields = ["display_title", "album__title", "song__title", "payload_id"]
    autocomplete_fields = ["album", "song"]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset
        return queryset.filter(album__site__in=request.user.sites.all())

    def get_list_filter(self, request):
        list_filter = super().get_list_filter(request)
        if request.user.is_superuser:
            return list_filter
        return [item for item in list_filter if item != "album__site"]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            if db_field.name == "album":
                kwargs["queryset"] = Album.objects.filter(site__in=request.user.sites.all())
            if db_field.name == "song":
                kwargs["queryset"] = Song.objects.filter(site__in=request.user.sites.all())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(VideoClip)
class VideoClipAdmin(DomainModelAdmin):
    rich_text_fields = ("description_html",)
    list_display = [
        "title",
        "site",
        "sort_order",
        "video_id",
        "release_date",
        "is_published",
        "payload_id",
    ]
    list_editable = ["sort_order"]
    list_filter = ["site", "is_published"]
    search_fields = ["title", "slug", "video_id", "payload_id"]
    prepopulated_fields = {"slug": ["title"]}
    autocomplete_fields = ["thumbnail"]
