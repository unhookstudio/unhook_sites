from django.db import models

from sites_core.models import SiteOwnedModel


class ContactSubmission(SiteOwnedModel):
    class Status(models.TextChoices):
        NEW = "new", "Nouveau"
        REVIEWED = "reviewed", "Lu"
        SPAM = "spam", "Spam"

    email = models.EmailField()
    message = models.TextField()
    status = models.CharField(
        "statut",
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
    )
    notification_sent_at = models.DateTimeField("notification envoyée le", blank=True, null=True)
    notification_error = models.TextField("erreur de notification", blank=True)

    class Meta:
        verbose_name = "message de contact"
        verbose_name_plural = "messages de contact"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.email} - {self.created_at:%Y-%m-%d}"


class NewsletterSubscription(SiteOwnedModel):
    class Status(models.TextChoices):
        SUBSCRIBED = "subscribed", "Inscrit"
        ERROR = "error", "Erreur de synchronisation"

    email = models.EmailField()
    status = models.CharField(
        "statut",
        max_length=20,
        choices=Status.choices,
        default=Status.SUBSCRIBED,
    )
    source = models.CharField(max_length=80, default="homepage")
    last_synced_at = models.DateTimeField("dernière synchronisation", blank=True, null=True)
    last_error = models.TextField("dernière erreur", blank=True)

    class Meta:
        verbose_name = "inscription newsletter"
        verbose_name_plural = "inscriptions newsletter"
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["site", "email"],
                name="unique_newsletter_email_per_site",
            )
        ]

    def __str__(self) -> str:
        return self.email
