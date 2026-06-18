from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class Site(models.Model):
    name = models.CharField(max_length=160)
    slug = models.SlugField(unique=True)
    domain = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class User(AbstractUser):
    sites = models.ManyToManyField(Site, blank=True, related_name="users")
    default_site = models.ForeignKey(
        Site,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="default_users",
    )


class SiteOwnedModel(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class PublishableModel(models.Model):
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        abstract = True

    def publish(self) -> None:
        """Mark this instance as published without saving it."""
        self.is_published = True
        if self.published_at is None:
            self.published_at = timezone.now()


class SiteSettings(models.Model):
    site = models.OneToOneField(Site, on_delete=models.CASCADE, related_name="settings")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    footer_text = models.TextField(blank=True)
    newsletter_text = models.TextField(blank=True)
    instagram_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)

    class Meta:
        verbose_name = "site settings"
        verbose_name_plural = "site settings"

    def __str__(self) -> str:
        return f"Settings for {self.site}"


class NavigationLink(SiteOwnedModel):
    label = models.CharField(max_length=120)
    url = models.CharField(max_length=500)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["site", "order", "label"]

    def __str__(self) -> str:
        return self.label


class Redirect(SiteOwnedModel):
    class StatusCode(models.IntegerChoices):
        MOVED_PERMANENTLY = 301, "301 Moved Permanently"
        FOUND = 302, "302 Found"
        TEMPORARY_REDIRECT = 307, "307 Temporary Redirect"
        PERMANENT_REDIRECT = 308, "308 Permanent Redirect"

    old_path = models.CharField(max_length=500)
    new_url_or_path = models.CharField(max_length=500)
    status_code = models.PositiveSmallIntegerField(
        choices=StatusCode.choices,
        default=StatusCode.MOVED_PERMANENTLY,
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["site", "old_path"]
        unique_together = [("site", "old_path")]

    def __str__(self) -> str:
        return f"{self.old_path} -> {self.new_url_or_path}"
