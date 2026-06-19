from pathlib import PurePath

from django.db import models

from sites_core.models import SiteOwnedModel


def _clean_filename(filename: str) -> str:
    return PurePath(filename).name


def image_original_upload_path(instance: "Image", filename: str) -> str:
    site_slug = instance.site.slug if instance.site_id else "unassigned"
    return f"sites/{site_slug}/images/originals/{_clean_filename(filename)}"


def image_variant_upload_path(instance: "ImageVariant", filename: str) -> str:
    site_slug = instance.image.site.slug if instance.image_id else "unassigned"
    variant_kind = instance.payload_kind or instance.kind
    return f"sites/{site_slug}/images/variants/{variant_kind}/{_clean_filename(filename)}"


class Image(SiteOwnedModel):
    title = models.CharField(max_length=255, blank=True)
    alt_text = models.CharField(max_length=255, blank=True)
    caption = models.TextField(blank=True)
    original = models.ImageField(upload_to=image_original_upload_path, blank=True)
    width = models.PositiveIntegerField(blank=True, null=True)
    height = models.PositiveIntegerField(blank=True, null=True)
    filesize = models.PositiveIntegerField(blank=True, null=True)
    mime_type = models.CharField(max_length=120, blank=True)
    filename = models.CharField(max_length=255, blank=True)
    payload_id = models.PositiveIntegerField(blank=True, null=True)
    payload_url = models.URLField(max_length=1000, blank=True)
    payload_thumbnail_url = models.URLField(max_length=1000, blank=True)
    payload_created_at = models.DateTimeField(blank=True, null=True)
    payload_updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["site", "title", "filename", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["site", "payload_id"],
                name="unique_image_payload_id_per_site",
            ),
        ]

    def __str__(self) -> str:
        return self.title or self.alt_text or self.filename or f"Image {self.pk}"


class ImageVariant(models.Model):
    class Kind(models.TextChoices):
        THUMBNAIL = "thumbnail", "Thumbnail"
        SQUARE = "square", "Square"
        SMALL = "small", "Small"
        MEDIUM = "medium", "Medium"
        LARGE = "large", "Large"
        XLARGE = "xlarge", "XLarge"
        OG = "og", "Open Graph"
        OTHER = "other", "Other"

    image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name="variants")
    kind = models.CharField(max_length=40, choices=Kind.choices)
    payload_kind = models.CharField(max_length=80, blank=True)
    file = models.ImageField(upload_to=image_variant_upload_path, blank=True)
    width = models.PositiveIntegerField(blank=True, null=True)
    height = models.PositiveIntegerField(blank=True, null=True)
    filesize = models.PositiveIntegerField(blank=True, null=True)
    mime_type = models.CharField(max_length=120, blank=True)
    filename = models.CharField(max_length=255, blank=True)
    payload_url = models.URLField(max_length=1000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["image", "kind"]
        constraints = [
            models.UniqueConstraint(
                fields=["image", "payload_kind"],
                name="unique_image_variant_payload_kind_per_image",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.image} ({self.kind})"

    def save(self, *args, **kwargs):
        if not self.payload_kind:
            self.payload_kind = self.kind
        super().save(*args, **kwargs)
