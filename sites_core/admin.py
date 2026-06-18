from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import NavigationLink, Redirect, Site, SiteSettings, User


class SiteScopedAdmin(admin.ModelAdmin):
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

    def save_model(self, request, obj, form, change):
        if not change and not request.user.is_superuser and hasattr(obj, self.site_field):
            if getattr(obj, f"{self.site_field}_id") is None:
                setattr(obj, self.site_field, request.user.default_site)
        super().save_model(request, obj, form, change)


class SiteSettingsInline(admin.StackedInline):
    model = SiteSettings
    can_delete = False
    extra = 0


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "domain", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name", "slug", "domain"]
    prepopulated_fields = {"slug": ["name"]}
    inlines = [SiteSettingsInline]


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
