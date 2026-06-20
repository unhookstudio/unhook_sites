from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import ValidationError
from django.http import Http404
from django.utils.html import format_html

from media_library.models import Image

from .models import NavigationLink, Redirect, Site, SiteSettings, User


class ScopedObjectAdminMixin:
    def change_view(self, request, object_id, form_url="", extra_context=None):
        if not self._object_visible_to_request(request, object_id):
            raise Http404
        return super().change_view(request, object_id, form_url, extra_context)

    def _object_visible_to_request(self, request, object_id):
        try:
            return self.get_queryset(request).filter(pk=object_id).exists()
        except (TypeError, ValueError, ValidationError):
            return False


class SiteScopedAdmin(ScopedObjectAdminMixin, admin.ModelAdmin):
    site_field = "site"

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset
        return queryset.filter(**{f"{self.site_field}__in": request.user.sites.all()})

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == self.site_field and not request.user.is_superuser:
            kwargs["queryset"] = request.user.sites.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_list_filter(self, request):
        list_filter = super().get_list_filter(request)
        if request.user.is_superuser:
            return list_filter
        return [item for item in list_filter if item != self.site_field]

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        if not request.user.is_superuser and request.user.default_site_id:
            initial.setdefault(self.site_field, request.user.default_site_id)
        return initial


class SiteSettingsInline(admin.StackedInline):
    model = SiteSettings
    can_delete = False
    extra = 0
    fields = [
        "footer_text",
        "newsletter_text",
        "show_homepage_hero",
        "homepage_hero_preview",
        "homepage_hero_image",
        "homepage_hero_text",
        "homepage_hero_button_text",
        "homepage_hero_button_url",
        "instagram_url",
        "facebook_url",
        "youtube_url",
    ]
    readonly_fields = ["homepage_hero_preview"]

    @admin.display(description="Hero image preview")
    def homepage_hero_preview(self, obj):
        if not obj or not obj.homepage_hero_image or not obj.homepage_hero_image.original:
            return "-"
        try:
            url = obj.homepage_hero_image.original.url
        except ValueError:
            return "-"
        return format_html(
            '<img src="{}" alt="" style="max-width: 220px; max-height: 140px; height: auto;" />',
            url,
        )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "homepage_hero_image" and not request.user.is_superuser:
            kwargs["queryset"] = Image.objects.filter(site__in=request.user.sites.all())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Site)
class SiteAdmin(ScopedObjectAdminMixin, admin.ModelAdmin):
    list_display = ["name", "slug", "domain", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name", "slug", "domain"]
    prepopulated_fields = {"slug": ["name"]}
    inlines = [SiteSettingsInline]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset
        return queryset.filter(pk__in=request.user.sites.values("pk"))

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Site access", {"fields": ("sites", "default_site")}),
    )
    filter_horizontal = UserAdmin.filter_horizontal + ("sites",)


@admin.register(NavigationLink)
class NavigationLinkAdmin(SiteScopedAdmin):
    list_display = ["label", "site", "url", "order", "is_active"]
    list_filter = ["site", "is_active"]
    search_fields = ["label", "url"]


@admin.register(Redirect)
class RedirectAdmin(SiteScopedAdmin):
    list_display = ["old_path", "new_url_or_path", "status_code", "site", "is_active"]
    list_filter = ["site", "status_code", "is_active"]
    search_fields = ["old_path", "new_url_or_path"]
