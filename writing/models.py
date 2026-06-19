from django.db import models

from media_library.models import Image
from sites_core.models import PublishableModel, SiteOwnedModel


class Article(SiteOwnedModel, PublishableModel):
    class Category(models.TextChoices):
        NEWS = "news", "News"
        PRESS = "press", "Press"
        HEART = "coup-de-coeur", "Coup de coeur"
        OTHER = "other", "Other"

    title = models.CharField(max_length=255)
    slug = models.SlugField()
    content_html = models.TextField(blank=True)
    content_plain = models.TextField(blank=True)
    payload_content = models.JSONField(blank=True, null=True)
    category = models.CharField(max_length=60, choices=Category.choices, default=Category.NEWS)
    featured_image = models.ForeignKey(Image, blank=True, null=True, on_delete=models.SET_NULL)
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)
    payload_id = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        ordering = ["-published_at", "title"]
        constraints = [
            models.UniqueConstraint(fields=["site", "slug"], name="unique_article_slug_per_site"),
            models.UniqueConstraint(fields=["site", "payload_id"], name="unique_article_payload_id_per_site"),
        ]

    def __str__(self) -> str:
        return self.title


class Book(SiteOwnedModel, PublishableModel):
    class Category(models.TextChoices):
        NOVELS = "novels", "Romans"
        ILLUSTRATED = "illustrated", "Livres illustres"
        CHILDREN = "children", "Jeunesse"
        ESSAYS = "essays", "Essais"
        OTHER = "other", "Other"

    title = models.CharField(max_length=255)
    slug = models.SlugField()
    category = models.CharField(max_length=60, choices=Category.choices, default=Category.NOVELS)
    author = models.CharField(max_length=255, blank=True)
    illustrator = models.CharField(max_length=255, blank=True)
    short_description_html = models.TextField(blank=True)
    description_html = models.TextField(blank=True)
    payload_short_description = models.JSONField(blank=True, null=True)
    payload_description = models.JSONField(blank=True, null=True)
    cover_image = models.ForeignKey(Image, blank=True, null=True, on_delete=models.SET_NULL)
    additional_images = models.ManyToManyField(Image, blank=True, related_name="book_additional_uses")
    editor = models.CharField(max_length=255, blank=True)
    release_date = models.DateField(blank=True, null=True)
    shop_url = models.URLField(blank=True)
    publisher_url = models.URLField(blank=True)
    show_on_books_page = models.BooleanField(default=True)
    show_on_drawings_page = models.BooleanField(default=False)
    payload_id = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        ordering = ["-release_date", "title"]
        constraints = [
            models.UniqueConstraint(fields=["site", "slug"], name="unique_book_slug_per_site"),
            models.UniqueConstraint(fields=["site", "payload_id"], name="unique_book_payload_id_per_site"),
        ]

    def __str__(self) -> str:
        return self.title
