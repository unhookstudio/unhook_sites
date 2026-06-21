from dataclasses import dataclass
from datetime import datetime

from django.urls import reverse

from events.models import Event
from music.models import Album, Song
from visual_art.models import BD, Drawing
from writing.models import Article, Book


@dataclass(frozen=True)
class SitemapEntry:
    path: str
    lastmod: datetime | None = None
    changefreq: str = "weekly"
    priority: str = "0.5"


def entries_for_site(site) -> list[SitemapEntry]:
    entries: list[SitemapEntry] = [
        SitemapEntry(reverse("home"), priority="1.0"),
        SitemapEntry(reverse("musique"), priority="0.8"),
        SitemapEntry(reverse("livres"), priority="0.8"),
        SitemapEntry(reverse("dessins"), priority="0.8"),
        SitemapEntry(reverse("a_propos"), priority="0.6"),
        SitemapEntry(reverse("contact"), priority="0.4"),
        SitemapEntry(reverse("mentions_legales"), priority="0.2"),
    ]

    if _published(Event, site).exists():
        entries.append(SitemapEntry(reverse("dates"), priority="0.7", changefreq="daily"))

    if _published(Article, site).exists():
        entries.append(SitemapEntry(reverse("posts"), priority="0.6"))

    entries.extend(
        SitemapEntry(
            reverse("album_detail", kwargs={"slug": album.slug}),
            lastmod=album.updated_at,
            priority="0.7",
        )
        for album in _published(Album, site).only("slug", "updated_at")
    )
    entries.extend(
        SitemapEntry(
            reverse("song_detail", kwargs={"slug": song.slug}),
            lastmod=song.updated_at,
            priority="0.6",
        )
        for song in _published(Song, site).only("slug", "updated_at")
    )
    entries.extend(
        SitemapEntry(
            reverse("book_detail", kwargs={"slug": book.slug}),
            lastmod=book.updated_at,
            priority="0.7",
        )
        for book in _published(Book, site).only("slug", "updated_at")
    )
    entries.extend(
        SitemapEntry(
            reverse("dessin_detail", kwargs={"slug": bd.slug}),
            lastmod=bd.updated_at,
            priority="0.7",
        )
        for bd in _published(BD, site).only("slug", "updated_at")
    )
    entries.extend(
        SitemapEntry(
            reverse("dessin_detail", kwargs={"slug": drawing.slug}),
            lastmod=drawing.updated_at,
            priority="0.6",
        )
        for drawing in _published(Drawing, site).only("slug", "updated_at")
    )
    entries.extend(
        SitemapEntry(
            reverse("post_detail", kwargs={"slug": article.slug}),
            lastmod=article.updated_at,
            priority="0.6",
        )
        for article in _published(Article, site).only("slug", "updated_at")
    )

    return _dedupe(entries)


def _published(model, site):
    return model.objects.filter(site=site, is_published=True)


def _dedupe(entries: list[SitemapEntry]) -> list[SitemapEntry]:
    seen: set[str] = set()
    deduped: list[SitemapEntry] = []
    for entry in entries:
        if entry.path in seen:
            continue
        seen.add(entry.path)
        deduped.append(entry)
    return deduped
