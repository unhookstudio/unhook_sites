from django.db import models

from media_library.models import Image
from sites_core.models import PublishableModel, SiteOwnedModel


class Event(SiteOwnedModel, PublishableModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField()
    date = models.DateTimeField(blank=True, null=True)
    description_html = models.TextField(blank=True)
    payload_description = models.JSONField(blank=True, null=True)
    cover_image = models.ForeignKey(Image, blank=True, null=True, on_delete=models.SET_NULL)
    payload_id = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        ordering = ["-date", "title"]
        constraints = [
            models.UniqueConstraint(fields=["site", "slug"], name="unique_event_slug_per_site"),
            models.UniqueConstraint(
                fields=["site", "payload_id"],
                name="unique_event_payload_id_per_site",
            ),
        ]

    def __str__(self) -> str:
        return self.title


class KeyDate(SiteOwnedModel, PublishableModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField()
    date = models.DateTimeField(blank=True, null=True)
    description_html = models.TextField(blank=True)
    payload_description = models.JSONField(blank=True, null=True)
    payload_id = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        ordering = ["-date", "title"]
        constraints = [
            models.UniqueConstraint(fields=["site", "slug"], name="unique_keydate_slug_per_site"),
            models.UniqueConstraint(
                fields=["site", "payload_id"],
                name="unique_keydate_payload_id_per_site",
            ),
        ]

    def __str__(self) -> str:
        return self.title
