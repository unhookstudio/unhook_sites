from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
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
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="%(class)ss")
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
    contact_title = models.CharField(max_length=255, blank=True)
    contact_intro_text = models.TextField(blank=True)
    show_homepage_hero = models.BooleanField(default=False)
    homepage_hero_image = models.ForeignKey(
        "media_library.Image",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    homepage_hero_text = models.TextField(
        blank=True,
        help_text="Falls back to the default Kent introduction when left blank.",
    )
    homepage_hero_button_text = models.CharField(
        max_length=80,
        blank=True,
        help_text="Falls back to “(Re)Découvrir” when left blank.",
    )
    homepage_hero_button_url = models.CharField(max_length=500, default="/a-propos")
    instagram_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)
    bandcamp_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)

    class Meta:
        verbose_name = "réglages du site"
        verbose_name_plural = "réglages du site"

    def __str__(self) -> str:
        return f"Settings for {self.site}"

    def clean(self) -> None:
        super().clean()
        if (
            self.homepage_hero_image_id
            and self.site_id
            and self.homepage_hero_image.site_id != self.site_id
        ):
            raise ValidationError(
                {"homepage_hero_image": "The hero image must belong to the same site."}
            )

    @property
    def effective_homepage_hero_text(self) -> str:
        return self.homepage_hero_text or (
            "D'un garage lyonnais,\n"
            "en passant par\n"
            "Métal hurlant et Taratata,\n"
            "jusqu'à la BNF."
        )

    @property
    def effective_homepage_hero_button_text(self) -> str:
        return self.homepage_hero_button_text or "(Re)Découvrir"

    @property
    def effective_homepage_hero_button_url(self) -> str:
        return self.homepage_hero_button_url or "/a-propos"


class NavigationLink(SiteOwnedModel):
    label = models.CharField(max_length=120)
    url = models.CharField(max_length=500)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "lien de navigation"
        verbose_name_plural = "liens de navigation"
        ordering = ["site", "order", "label"]

    def __str__(self) -> str:
        return self.label


class TextSnippet(SiteOwnedModel):
    key = models.SlugField(max_length=120)
    label = models.CharField(max_length=160)
    text = models.TextField(blank=True)

    class Meta:
        verbose_name = "texte éditorial"
        verbose_name_plural = "textes éditoriaux"
        ordering = ["site", "label"]
        constraints = [
            models.UniqueConstraint(
                fields=["site", "key"],
                name="unique_text_snippet_key_per_site",
            )
        ]

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
        verbose_name = "redirection"
        verbose_name_plural = "redirections"
        ordering = ["site", "old_path"]
        unique_together = [("site", "old_path")]

    def __str__(self) -> str:
        return f"{self.old_path} -> {self.new_url_or_path}"
