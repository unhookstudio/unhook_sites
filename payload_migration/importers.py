from datetime import datetime
from typing import Any

from django.db import transaction
from django.utils.dateparse import parse_datetime

from events.models import Event, KeyDate
from media_library.models import Image
from music.models import Album, Artist, Song, Track, VideoClip
from photos.models import Photo, PhotoCollection, PhotoCollectionItem, PhotoStory
from visual_art.models import BD, Drawing
from writing.models import Article, Book

from .lexical import LexicalConverter


def _date(value: str | None):
    if not value:
        return None
    parsed = parse_datetime(value)
    if parsed:
        return parsed.date()
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return None


def _datetime(value: str | None):
    if not value:
        return None
    return parse_datetime(value)


def _payload_id(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, dict):
        return value.get("id")
    return value


def _media(site, value: Any) -> Image | None:
    payload_id = _payload_id(value)
    if payload_id is None:
        return None
    return Image.objects.filter(site=site, payload_id=payload_id).first()


def _is_published(doc: dict[str, Any]) -> bool:
    return doc.get("_status", "published") == "published"


def _slug(doc: dict[str, Any]) -> str:
    return doc.get("slug") or f"payload-{doc['id']}"


def _upsert(model, *, site, payload_id, defaults):
    return model.objects.update_or_create(site=site, payload_id=payload_id, defaults=defaults)[0]


class PayloadSnapshotImporter:
    def __init__(self, *, site, converter: LexicalConverter | None = None):
        self.site = site
        self.converter = converter or LexicalConverter()

    def import_snapshot(self, snapshot: dict[str, list[dict[str, Any]]], *, max_docs: int | None = None) -> dict[str, int]:
        counts: dict[str, int] = {}
        with transaction.atomic():
            counts["posts"] = self._import_many("posts", snapshot, self.import_article, max_docs=max_docs)
            counts["albums"] = self._import_many("albums", snapshot, self.import_album, max_docs=max_docs)
            counts["chansons"] = self._import_many("chansons", snapshot, self.import_song, max_docs=max_docs)
            counts["album-tracks"] = self._import_many("album-tracks", snapshot, self.import_track, max_docs=max_docs)
            counts["video-clips"] = self._import_many("video-clips", snapshot, self.import_video_clip, max_docs=max_docs)
            counts["livres"] = self._import_many("livres", snapshot, self.import_book, max_docs=max_docs)
            counts["bds"] = self._import_many("bds", snapshot, self.import_bd, max_docs=max_docs)
            counts["dessins"] = self._import_many("dessins", snapshot, self.import_drawing, max_docs=max_docs)
            counts["dates"] = self._import_many("dates", snapshot, self.import_event, max_docs=max_docs)
            counts["dates-cles"] = self._import_many("dates-cles", snapshot, self.import_key_date, max_docs=max_docs)
            counts["photos"] = self._import_many("photos", snapshot, self.import_photo, max_docs=max_docs)
            counts["photo-stories"] = self._import_many("photo-stories", snapshot, self.import_photo_story, max_docs=max_docs)
            counts["photo-collections"] = self._import_many(
                "photo-collections",
                snapshot,
                self.import_photo_collection,
                max_docs=max_docs,
            )
        return counts

    def _import_many(self, collection, snapshot, importer, *, max_docs):
        docs = list(snapshot.get(collection, []))
        if max_docs is not None:
            docs = docs[:max_docs]
        imported = 0
        for doc in docs:
            if importer(doc) is not None:
                imported += 1
        return imported

    def rich_text(self, doc, collection, field_name):
        return self.converter.convert(
            doc.get(field_name),
            collection=collection,
            document_id=doc.get("id"),
            field_name=field_name,
        )

    def import_article(self, doc):
        return _upsert(
            Article,
            site=self.site,
            payload_id=doc["id"],
            defaults={
                "title": doc.get("title") or "",
                "slug": _slug(doc),
                "content_html": self.rich_text(doc, "posts", "content"),
                "content_plain": doc.get("contentPlain") or "",
                "payload_content": doc.get("content"),
                "category": doc.get("categories") or Article.Category.NEWS,
                "featured_image": _media(self.site, doc.get("featuredImage")),
                "published_at": _datetime(doc.get("publishedAt")),
                "is_published": _is_published(doc),
            },
        )

    def import_album(self, doc):
        artist = self._artist(doc.get("artist") or "Kent")
        album = _upsert(
            Album,
            site=self.site,
            payload_id=doc["id"],
            defaults={
                "title": doc.get("title") or "",
                "slug": _slug(doc),
                "artist": artist,
                "category": doc.get("category") or Album.Category.COMMERCIAL,
                "description_html": self.rich_text(doc, "albums", "description"),
                "credits_html": self.rich_text(doc, "albums", "credits"),
                "payload_description": doc.get("description"),
                "payload_credits": doc.get("credits"),
                "cover_image": _media(self.site, doc.get("coverImage")),
                "release_date": _date(doc.get("releaseDate")),
                "label": doc.get("label") or "",
                "shop_url": doc.get("shopUrl") or "",
                "bandcamp_url": doc.get("bandcampUrl") or "",
                "is_published": _is_published(doc),
            },
        )
        album.additional_images.set(
            image
            for image in (_media(self.site, item.get("image")) for item in doc.get("additionalImages") or [])
            if image
        )
        return album

    def _artist(self, name: str) -> Artist:
        slug = name.lower().replace(" ", "-")
        return Artist.objects.get_or_create(site=self.site, slug=slug, defaults={"name": name})[0]

    def import_song(self, doc):
        return _upsert(
            Song,
            site=self.site,
            payload_id=doc["id"],
            defaults={
                "title": doc.get("title") or "",
                "slug": _slug(doc),
                "written_date": _date(doc.get("writtenDate")),
                "composer": doc.get("composer") or "",
                "lyricist": doc.get("lyricist") or "",
                "publisher": doc.get("publisher") or "",
                "description_html": self.rich_text(doc, "chansons", "description"),
                "lyrics_html": self.rich_text(doc, "chansons", "lyrics"),
                "payload_description": doc.get("description"),
                "payload_lyrics": doc.get("lyrics"),
                "shop_link": doc.get("shopLink") or "",
                "streaming_links": doc.get("streamingLinks") or [],
                "is_published": _is_published(doc),
            },
        )

    def import_track(self, doc):
        album = Album.objects.filter(site=self.site, payload_id=_payload_id(doc.get("album"))).first()
        song = Song.objects.filter(site=self.site, payload_id=_payload_id(doc.get("chanson"))).first()
        if not album or not song:
            return None
        return Track.objects.update_or_create(
            payload_id=doc["id"],
            defaults={
                "album": album,
                "song": song,
                "display_title": doc.get("displayTitle") or "",
                "note": doc.get("note") or "",
                "disc_number": doc.get("discNumber") or 1,
                "track_number": doc.get("trackNumber") or 1,
                "duration": doc.get("duration") or "",
                "version_type": doc.get("versionType") or Track.VersionType.STUDIO,
            },
        )[0]

    def import_video_clip(self, doc):
        return _upsert(
            VideoClip,
            site=self.site,
            payload_id=doc["id"],
            defaults={
                "title": doc.get("title") or "",
                "slug": _slug(doc),
                "description_html": self.rich_text(doc, "video-clips", "description"),
                "payload_description": doc.get("description"),
                "video_id": doc.get("videoId") or "",
                "thumbnail": _media(self.site, doc.get("thumbnail")),
                "release_date": _date(doc.get("releaseDate")),
                "is_published": _is_published(doc),
            },
        )

    def import_book(self, doc):
        book = _upsert(
            Book,
            site=self.site,
            payload_id=doc["id"],
            defaults={
                "title": doc.get("title") or "",
                "slug": _slug(doc),
                "category": doc.get("category") or Book.Category.NOVELS,
                "author": doc.get("author") or "",
                "illustrator": doc.get("illustrator") or "",
                "short_description_html": self.rich_text(doc, "livres", "shortDescription"),
                "description_html": self.rich_text(doc, "livres", "description"),
                "payload_short_description": doc.get("shortDescription"),
                "payload_description": doc.get("description"),
                "cover_image": _media(self.site, doc.get("coverImage")),
                "editor": doc.get("editor") or "",
                "release_date": _date(doc.get("releaseDate")),
                "shop_url": doc.get("shopUrl") or "",
                "publisher_url": doc.get("publisherUrl") or "",
                "show_on_books_page": True,
                "show_on_drawings_page": doc.get("category") == Book.Category.ILLUSTRATED,
                "is_published": _is_published(doc),
            },
        )
        book.additional_images.set(
            image
            for image in (_media(self.site, item.get("image")) for item in doc.get("additionalImages") or [])
            if image
        )
        return book

    def import_bd(self, doc):
        bd = _upsert(
            BD,
            site=self.site,
            payload_id=doc["id"],
            defaults={
                "title": doc.get("title") or "",
                "slug": _slug(doc),
                "category": doc.get("category") or BD.Category.ADULT,
                "author": doc.get("author") or "",
                "illustrator": doc.get("illustrateur") or doc.get("illustrator") or "",
                "description_html": self.rich_text(doc, "bds", "description"),
                "payload_description": doc.get("description"),
                "cover_image": _media(self.site, doc.get("coverImage")),
                "editor": doc.get("editor") or "",
                "release_date": _date(doc.get("releaseDate")),
                "shop_url": doc.get("shopUrl") or "",
                "publisher_url": doc.get("publisherUrl") or "",
                "is_published": _is_published(doc),
            },
        )
        bd.additional_images.set(
            image
            for image in (_media(self.site, item.get("image")) for item in doc.get("additionalImages") or [])
            if image
        )
        return bd

    def import_drawing(self, doc):
        drawing = _upsert(
            Drawing,
            site=self.site,
            payload_id=doc["id"],
            defaults={
                "title": doc.get("title") or "",
                "slug": _slug(doc),
                "description_html": self.rich_text(doc, "dessins", "description"),
                "payload_description": doc.get("description"),
                "release_date": _date(doc.get("releaseDate")),
                "is_published": _is_published(doc),
            },
        )
        drawing.images.set(
            image
            for image in (_media(self.site, item.get("image")) for item in doc.get("images") or [])
            if image
        )
        return drawing

    def import_event(self, doc):
        return _upsert(
            Event,
            site=self.site,
            payload_id=doc["id"],
            defaults={
                "title": doc.get("title") or "",
                "slug": _slug(doc),
                "date": _datetime(doc.get("date")),
                "description_html": self.rich_text(doc, "dates", "description"),
                "payload_description": doc.get("description"),
                "cover_image": _media(self.site, doc.get("coverImage")),
                "is_published": _is_published(doc),
            },
        )

    def import_key_date(self, doc):
        return _upsert(
            KeyDate,
            site=self.site,
            payload_id=doc["id"],
            defaults={
                "title": doc.get("title") or "",
                "slug": _slug(doc),
                "date": _datetime(doc.get("date")),
                "description_html": self.rich_text(doc, "dates-cles", "description"),
                "payload_description": doc.get("description"),
                "is_published": _is_published(doc),
            },
        )

    def import_photo(self, doc):
        return _upsert(
            Photo,
            site=self.site,
            payload_id=doc["id"],
            defaults={
                "title": doc.get("title") or "",
                "slug": _slug(doc),
                "description_html": self.rich_text(doc, "photos", "description"),
                "payload_description": doc.get("description"),
                "image": _media(self.site, doc.get("image")),
                "date": _date(doc.get("date")),
                "category": doc.get("category") or "",
                "photographer": doc.get("photographer") or "",
                "is_published": _is_published(doc),
            },
        )

    def import_photo_story(self, doc):
        return _upsert(
            PhotoStory,
            site=self.site,
            payload_id=doc["id"],
            defaults={
                "title": doc.get("title") or "",
                "slug": _slug(doc),
                "image": _media(self.site, doc.get("photo") or doc.get("image")),
                "description_html": self.rich_text(doc, "photo-stories", "description"),
                "payload_description": doc.get("description"),
                "date": _date(doc.get("date")),
                "photographer": doc.get("photographer") or "",
                "is_published": _is_published(doc),
            },
        )

    def import_photo_collection(self, doc):
        collection = _upsert(
            PhotoCollection,
            site=self.site,
            payload_id=doc["id"],
            defaults={
                "title": doc.get("title") or "",
                "slug": _slug(doc),
                "subtitle": doc.get("subtitle") or "",
                "description_html": self.rich_text(doc, "photo-collections", "description"),
                "payload_description": doc.get("description"),
                "is_published": _is_published(doc),
            },
        )
        collection.items.all().delete()
        for order, item in enumerate(doc.get("photos") or []):
            photo = Photo.objects.filter(site=self.site, payload_id=_payload_id(item.get("photo"))).first()
            if photo:
                PhotoCollectionItem.objects.create(
                    collection=collection,
                    photo=photo,
                    caption=item.get("caption") or "",
                    order=order,
                )
        return collection
