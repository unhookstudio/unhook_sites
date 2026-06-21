from django.db import models

from media_library.models import Image
from sites_core.models import PublishableModel, Site, SiteOwnedModel


class Photo(SiteOwnedModel, PublishableModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField()
    description_html = models.TextField(blank=True)
    payload_description = models.JSONField(blank=True, null=True)
    image = models.ForeignKey(Image, blank=True, null=True, on_delete=models.SET_NULL)
    date = models.DateField(blank=True, null=True)
    category = models.CharField(max_length=120, blank=True)
    photographer = models.CharField(max_length=255, blank=True)
    payload_id = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        verbose_name = "photo"
        verbose_name_plural = "photos"
        ordering = ["-date", "title"]
        constraints = [
            models.UniqueConstraint(fields=["site", "slug"], name="unique_photo_slug_per_site"),
            models.UniqueConstraint(fields=["site", "payload_id"], name="unique_photo_payload_id_per_site"),
        ]

    def __str__(self) -> str:
        return self.title


class PhotoStory(SiteOwnedModel, PublishableModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField()
    image = models.ForeignKey(Image, blank=True, null=True, on_delete=models.SET_NULL)
    description_html = models.TextField(blank=True)
    payload_description = models.JSONField(blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    photographer = models.CharField(max_length=255, blank=True)
    payload_id = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        verbose_name = "histoire de photo"
        verbose_name_plural = "histoires de photos"
        ordering = ["-date", "title"]
        constraints = [
            models.UniqueConstraint(fields=["site", "slug"], name="unique_photostory_slug_per_site"),
            models.UniqueConstraint(fields=["site", "payload_id"], name="unique_photostory_payload_id_per_site"),
        ]

    def __str__(self) -> str:
        return self.title


class PhotoCollection(SiteOwnedModel, PublishableModel):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="photo_collections")
    title = models.CharField(max_length=255)
    slug = models.SlugField()
    subtitle = models.CharField(max_length=255, blank=True)
    description_html = models.TextField(blank=True)
    payload_description = models.JSONField(blank=True, null=True)
    photos = models.ManyToManyField(Photo, through="PhotoCollectionItem", blank=True)
    payload_id = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        verbose_name = "collection de photos"
        verbose_name_plural = "collections de photos"
        ordering = ["title"]
        constraints = [
            models.UniqueConstraint(fields=["site", "slug"], name="unique_photocollection_slug_per_site"),
            models.UniqueConstraint(
                fields=["site", "payload_id"],
                name="unique_photocollection_payload_id_per_site",
            ),
        ]

    def __str__(self) -> str:
        return self.title


class PhotoCollectionItem(models.Model):
    collection = models.ForeignKey(PhotoCollection, on_delete=models.CASCADE, related_name="items")
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name="collection_items")
    caption = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "photo de collection"
        verbose_name_plural = "photos de collection"
        ordering = ["collection", "order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["collection", "photo"],
                name="unique_photo_per_collection",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.collection} - {self.photo}"
