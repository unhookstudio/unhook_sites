from django.contrib import admin

from unhook_sites.admin import DomainModelAdmin

from .models import Article, Book


@admin.register(Article)
class ArticleAdmin(DomainModelAdmin):
    rich_text_fields = ("content_html",)
    list_display = ["title", "site", "category", "published_at", "is_published", "payload_id"]
    list_filter = ["site", "category", "is_published"]
    search_fields = ["title", "slug", "content_plain", "payload_id"]
    prepopulated_fields = {"slug": ["title"]}
    autocomplete_fields = ["featured_image"]


@admin.register(Book)
class BookAdmin(DomainModelAdmin):
    rich_text_fields = ("short_description_html", "description_html")
    list_display = [
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
