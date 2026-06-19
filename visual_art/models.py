from django.db import models

from media_library.models import Image
from sites_core.models import PublishableModel, SiteOwnedModel


class BD(SiteOwnedModel, PublishableModel):
    class Category(models.TextChoices):
        ADULT = "adult", "Adulte"
        YOUTH = "youth", "Jeunesse"
        OTHER = "other", "Other"

    title = models.CharField(max_length=255)
    slug = models.SlugField()
    category = models.CharField(max_length=60, choices=Category.choices, default=Category.ADULT)
    author = models.CharField(max_length=255, blank=True)
    illustrator = models.CharField(max_length=255, blank=True)
    description_html = models.TextField(blank=True)
    payload_description = models.JSONField(blank=True, null=True)
    cover_image = models.ForeignKey(Image, blank=True, null=True, on_delete=models.SET_NULL)
    additional_images = models.ManyToManyField(Image, blank=True, related_name="bd_additional_uses")
    editor = models.CharField(max_length=255, blank=True)
    release_date = models.DateField(blank=True, null=True)
    shop_url = models.URLField(blank=True)
    publisher_url = models.URLField(blank=True)
    payload_id = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        verbose_name = "BD"
        verbose_name_plural = "BDs"
        ordering = ["-release_date", "title"]
        constraints = [
            models.UniqueConstraint(fields=["site", "slug"], name="unique_bd_slug_per_site"),
            models.UniqueConstraint(fields=["site", "payload_id"], name="unique_bd_payload_id_per_site"),
        ]

    def __str__(self) -> str:
        return self.title


class Drawing(SiteOwnedModel, PublishableModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField()
    description_html = models.TextField(blank=True)
    payload_description = models.JSONField(blank=True, null=True)
    images = models.ManyToManyField(Image, blank=True, related_name="drawing_uses")
    release_date = models.DateField(blank=True, null=True)
    payload_id = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        ordering = ["-release_date", "title"]
        constraints = [
            models.UniqueConstraint(fields=["site", "slug"], name="unique_drawing_slug_per_site"),
            models.UniqueConstraint(fields=["site", "payload_id"], name="unique_drawing_payload_id_per_site"),
        ]

    def __str__(self) -> str:
        return self.title
