from django.db import models

from media_library.models import Image
from sites_core.models import PublishableModel, SiteOwnedModel


class Artist(SiteOwnedModel):
    name = models.CharField(max_length=160)
    slug = models.SlugField()
    payload_id = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        verbose_name = "artiste"
        verbose_name_plural = "artistes"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["site", "slug"], name="unique_artist_slug_per_site"),
        ]

    def __str__(self) -> str:
        return self.name


class Album(SiteOwnedModel, PublishableModel):
    class Category(models.TextChoices):
        COMMERCIAL = "commercial", "Commercial"
        RARE = "rare", "Rare"
        PARTICIPATION = "participation", "Participation"
        OTHER = "other", "Autre"

    title = models.CharField(max_length=255)
    slug = models.SlugField()
    artist = models.ForeignKey(Artist, blank=True, null=True, on_delete=models.SET_NULL)
    category = models.CharField(max_length=40, choices=Category.choices, default=Category.COMMERCIAL)
    description_html = models.TextField(blank=True)
    credits_html = models.TextField(blank=True)
    payload_description = models.JSONField(blank=True, null=True)
    payload_credits = models.JSONField(blank=True, null=True)
    cover_image = models.ForeignKey(Image, blank=True, null=True, on_delete=models.SET_NULL)
    additional_images = models.ManyToManyField(Image, blank=True, related_name="+")
    release_date = models.DateField(blank=True, null=True)
    label = models.CharField(max_length=255, blank=True)
    shop_url = models.URLField(blank=True)
    bandcamp_url = models.URLField(blank=True)
    payload_id = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        verbose_name = "album"
        verbose_name_plural = "albums"
        ordering = ["-release_date", "title"]
        constraints = [
            models.UniqueConstraint(fields=["site", "slug"], name="unique_album_slug_per_site"),
            models.UniqueConstraint(fields=["site", "payload_id"], name="unique_album_payload_id_per_site"),
        ]

    def __str__(self) -> str:
        return self.title


class Song(SiteOwnedModel, PublishableModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField()
    written_date = models.DateField(blank=True, null=True)
    composer = models.CharField(max_length=255, blank=True)
    lyricist = models.CharField(max_length=255, blank=True)
    publisher = models.CharField(max_length=255, blank=True)
    description_html = models.TextField(blank=True)
    lyrics_html = models.TextField(blank=True)
    payload_description = models.JSONField(blank=True, null=True)
    payload_lyrics = models.JSONField(blank=True, null=True)
    shop_link = models.URLField(blank=True)
    streaming_links = models.JSONField(default=list, blank=True)
    payload_id = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        verbose_name = "chanson"
        verbose_name_plural = "chansons"
        ordering = ["title"]
        constraints = [
            models.UniqueConstraint(fields=["site", "slug"], name="unique_song_slug_per_site"),
            models.UniqueConstraint(fields=["site", "payload_id"], name="unique_song_payload_id_per_site"),
        ]

    def __str__(self) -> str:
        return self.title


class Track(models.Model):
    class VersionType(models.TextChoices):
        STUDIO = "studio", "Studio"
        LIVE = "live", "Live"
        REMIX = "remix", "Remix"
        DEMO = "demo", "Demo"

    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name="tracks")
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name="tracks")
    display_title = models.CharField(max_length=255, blank=True)
    note = models.CharField(max_length=255, blank=True)
    disc_number = models.PositiveIntegerField(default=1)
    track_number = models.PositiveIntegerField()
    duration = models.CharField(max_length=20, blank=True)
    version_type = models.CharField(max_length=40, choices=VersionType.choices, default=VersionType.STUDIO)
    payload_id = models.PositiveIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "piste"
        verbose_name_plural = "pistes"
        ordering = ["album", "disc_number", "track_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["album", "disc_number", "track_number"],
                name="unique_track_position_per_album",
            ),
            models.UniqueConstraint(fields=["payload_id"], name="unique_track_payload_id"),
        ]

    def __str__(self) -> str:
        return self.display_title or f"{self.album} - {self.song}"


class VideoClip(SiteOwnedModel, PublishableModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField()
    description_html = models.TextField(blank=True)
    payload_description = models.JSONField(blank=True, null=True)
    video_id = models.CharField(max_length=100, blank=True)
    thumbnail = models.ForeignKey(Image, blank=True, null=True, on_delete=models.SET_NULL)
    release_date = models.DateField(blank=True, null=True)
    sort_order = models.PositiveIntegerField(blank=True, null=True)
    payload_id = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        verbose_name = "clip vidéo"
        verbose_name_plural = "clips vidéo"
        ordering = ["-release_date", "title"]
        constraints = [
            models.UniqueConstraint(fields=["site", "slug"], name="unique_videoclip_slug_per_site"),
            models.UniqueConstraint(fields=["site", "payload_id"], name="unique_videoclip_payload_id_per_site"),
        ]

    def __str__(self) -> str:
        return self.title
