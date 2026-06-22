from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import ValidationError
from django.http import Http404
from django.utils.html import format_html

from media_library.models import Image

from .models import NavigationLink, Redirect, Site, SiteSettings, TextSnippet, User

admin.site.site_header = "Administration Kent"
admin.site.site_title = "Administration Kent"
admin.site.index_title = "Gestion du site"


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

    def has_add_permission(self, request):
        has_permission = super().has_add_permission(request)
        if request.user.is_superuser:
            return has_permission
        return has_permission and self._site_for_request(request) is not None

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset
        return queryset.filter(**{f"{self.site_field}__in": request.user.sites.all()})

    def get_exclude(self, request, obj=None):
        exclude = list(super().get_exclude(request, obj) or [])
        if self._should_hide_site_field(request) and self.site_field not in exclude:
            exclude.append(self.site_field)
        return exclude

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
        site = self._site_for_request(request)
        if not request.user.is_superuser and site is not None:
            initial.setdefault(self.site_field, site.pk)
        return initial

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser and not getattr(obj, f"{self.site_field}_id", None):
            site = self._site_for_request(request)
            if site is not None:
                setattr(obj, self.site_field, site)
        super().save_model(request, obj, form, change)

    def _site_for_request(self, request):
        if request.user.is_superuser:
            return None
        if (
            request.user.default_site_id
            and request.user.sites.filter(pk=request.user.default_site_id).exists()
        ):
            return request.user.default_site
        sites = list(request.user.sites.all()[:2])
        if len(sites) == 1:
            return sites[0]
        return None

    def _should_hide_site_field(self, request):
        if request.user.is_superuser:
            return False
        return request.user.sites.count() == 1


class SiteSettingsInline(admin.StackedInline):
    model = SiteSettings
    can_delete = False
    extra = 0
    fields = [
        "footer_text",
        "newsletter_text",
        "contact_title",
        "contact_intro_text",
        "show_homepage_hero",
        "homepage_hero_preview",
        "homepage_hero_image",
        "homepage_hero_text",
        "homepage_hero_button_text",
        "homepage_hero_button_url",
        "instagram_url",
        "facebook_url",
        "bandcamp_url",
        "youtube_url",
        "favicon_preview",
        "favicon_svg",
        "favicon_ico",
        "apple_touch_icon",
    ]
    readonly_fields = ["homepage_hero_preview", "favicon_preview"]

    @admin.display(description="Aperçu de l'image d'accueil")
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

    @admin.display(description="Favicon actuel")
    def favicon_preview(self, obj):
        if not obj:
            return "-"
        links = []
        for label, field_name in (
            ("SVG", "favicon_svg"),
            ("ICO/PNG", "favicon_ico"),
            ("Apple", "apple_touch_icon"),
        ):
            file = getattr(obj, field_name)
            if file:
                links.append(format_html('<a href="{}" target="_blank">{}</a>', file.url, label))
        if not links:
            return "-"
        return format_html(" · ".join(["{}"] * len(links)), *links)

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


@admin.register(TextSnippet)
class TextSnippetAdmin(SiteScopedAdmin):
    list_display = ["label", "key", "site", "updated_at"]
    list_filter = ["site"]
    search_fields = ["label", "key", "text"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Redirect)
class RedirectAdmin(SiteScopedAdmin):
    list_display = ["old_path", "new_url_or_path", "status_code", "site", "is_active"]
    list_filter = ["site", "status_code", "is_active"]
    search_fields = ["old_path", "new_url_or_path"]
