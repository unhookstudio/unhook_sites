from django.contrib import admin

from sites_core.admin import SiteScopedAdmin

from .models import ContactSubmission, NewsletterSubscription


@admin.register(ContactSubmission)
class ContactSubmissionAdmin(SiteScopedAdmin):
    list_display = ["email", "site", "status", "notification_sent_at", "created_at"]
    list_filter = ["site", "status"]
    search_fields = ["email", "message"]
    readonly_fields = [
        "notification_sent_at",
        "notification_error",
        "created_at",
        "updated_at",
    ]


@admin.register(NewsletterSubscription)
class NewsletterSubscriptionAdmin(SiteScopedAdmin):
    list_display = ["email", "site", "status", "source", "last_synced_at", "created_at"]
    list_filter = ["site", "status", "source"]
    search_fields = ["email"]
    readonly_fields = ["last_synced_at", "last_error", "created_at", "updated_at"]
