import re
from html import unescape

from django import forms
from django.contrib import admin
from django.utils.html import strip_tags
from django_prose_editor.widgets import AdminProseEditorWidget

from media_library.admin import image_preview
from unhook_sites.admin import DateOnlyFriendlySplitDateTimeField, DomainModelAdmin

from .models import Article, Book


class ArticleAdminForm(forms.ModelForm):
    published_at = DateOnlyFriendlySplitDateTimeField(
        label="Publié le",
        required=False,
        default_time="15:00",
    )

    class Meta:
        model = Article
        exclude = ["content_plain"]
        widgets = {
            "content_html": AdminProseEditorWidget(
                attrs={"rows": 8, "style": "min-height: 12rem;"}
            ),
        }


@admin.register(Article)
class ArticleAdmin(DomainModelAdmin):
    form = ArticleAdminForm
    list_display = ["title", "site", "category", "published_at", "is_published", "payload_id"]
    list_filter = ["site", "category", "is_published"]
    search_fields = ["title", "slug", "content_plain", "payload_id"]
    prepopulated_fields = {"slug": ["title"]}
    autocomplete_fields = ["featured_image"]

    def save_model(self, request, obj, form, change):
        obj.content_plain = _plain_text_from_html(obj.content_html)
        super().save_model(request, obj, form, change)


@admin.register(Book)
class BookAdmin(DomainModelAdmin):
    rich_text_fields = ("short_description_html", "description_html")
    list_display = [
        "cover_preview",
        "title",
        "site",
        "category",
        "release_date",
        "show_on_books_page",
        "show_on_drawings_page",
        "is_published",
        "payload_id",
    ]
    list_filter = ["site", "category", "show_on_books_page", "show_on_drawings_page", "is_published"]
    search_fields = ["title", "slug", "author", "illustrator", "editor", "payload_id"]
    prepopulated_fields = {"slug": ["title"]}
    autocomplete_fields = ["cover_image", "additional_images"]
    readonly_fields = [*DomainModelAdmin.readonly_fields, "cover_preview"]

    @admin.display(description="Couverture")
    def cover_preview(self, obj):
        if not obj.cover_image:
            return "-"
        return image_preview(obj.cover_image.original)


def _plain_text_from_html(value: str) -> str:
    return re.sub(r"\s+", " ", unescape(strip_tags(value or ""))).strip()
