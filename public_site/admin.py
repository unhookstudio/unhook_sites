from django.contrib import admin

from sites_core.admin import SiteScopedAdmin

from .models import ContactSubmission


@admin.register(ContactSubmission)
class ContactSubmissionAdmin(SiteScopedAdmin):
    list_display = ["email", "site", "status", "created_at"]
    list_filter = ["site", "status"]
    search_fields = ["email", "message"]
    readonly_fields = ["created_at", "updated_at"]
