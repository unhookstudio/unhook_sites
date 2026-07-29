from django.db import models

from media_library.models import Image
from sites_core.models import PublishableModel, SiteOwnedModel


class Event(SiteOwnedModel, PublishableModel):
    title = models.CharField("titre", max_length=255)
    slug = models.SlugField()
    date = models.DateTimeField("date", blank=True, null=True)
    end_date = models.DateTimeField("date de fin", blank=True, null=True)
    hide_time = models.BooleanField("masquer l'heure", default=False)
    url = models.URLField("lien", blank=True)
    location_details = models.CharField("lieu / ville", max_length=500, blank=True)
    description_html = models.TextField("description", blank=True)
    payload_description = models.JSONField("description Payload", blank=True, null=True)
    cover_image = models.ForeignKey(
        Image,
        verbose_name="image",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    payload_id = models.PositiveIntegerField("ID Payload", blank=True, null=True)

    class Meta:
        verbose_name = "date"
        verbose_name_plural = "dates"
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
    title = models.CharField("titre", max_length=255)
    slug = models.SlugField()
    date = models.DateTimeField("date", blank=True, null=True)
    description_html = models.TextField("description", blank=True)
    payload_description = models.JSONField("description Payload", blank=True, null=True)
    payload_id = models.PositiveIntegerField("ID Payload", blank=True, null=True)

    class Meta:
        verbose_name = "date clé"
        verbose_name_plural = "dates clés"
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
