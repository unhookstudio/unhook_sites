from django.db import models

from sites_core.models import SiteOwnedModel


class ContactSubmission(SiteOwnedModel):
    class Status(models.TextChoices):
        NEW = "new", "New"
        REVIEWED = "reviewed", "Reviewed"
        SPAM = "spam", "Spam"

    email = models.EmailField()
    message = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.email} - {self.created_at:%Y-%m-%d}"
