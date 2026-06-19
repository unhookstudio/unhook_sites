from pathlib import Path
from typing import Any

from events.models import Event, KeyDate
from media_library.models import Image
from music.models import Album, Song, Track, VideoClip
from photos.models import Photo, PhotoCollection, PhotoStory
from visual_art.models import BD, Drawing
from writing.models import Article, Book

from .client import DEFAULT_COLLECTIONS, read_json


COLLECTION_MODELS = {
    "media": Image,
    "posts": Article,
    "albums": Album,
    "chansons": Song,
    "album-tracks": Track,
    "video-clips": VideoClip,
    "livres": Book,
    "bds": BD,
    "dessins": Drawing,
    "dates": Event,
    "dates-cles": KeyDate,
    "photos": Photo,
    "photo-stories": PhotoStory,
    "photo-collections": PhotoCollection,
}


def payload_id(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, dict):
        return value.get("id")
    return value


def load_snapshot(input_dir: Path, collections: list[str] | None = None) -> dict[str, list[dict[str, Any]]]:
    snapshot = {}
    for collection in collections or DEFAULT_COLLECTIONS:
        path = input_dir / f"{collection}.json"
        if not path.exists():
            continue
        payload = read_json(path)
        snapshot[collection] = payload.get("docs", payload)
    return snapshot


def audit_snapshot(*, site, input_dir: Path, log_dir: Path, collections: list[str] | None = None) -> dict[str, Any]:
    snapshot = load_snapshot(input_dir, collections)
    return {
        "counts": audit_counts(site=site, snapshot=snapshot),
        "unresolved_media": audit_media_references(site=site, snapshot=snapshot),
        "unresolved_tracks": audit_track_references(site=site, snapshot=snapshot),
        "unknown_lexical_nodes": load_unknown_lexical_nodes(log_dir),
    }


def audit_counts(*, site, snapshot: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows = []
    for collection, docs in snapshot.items():
        model = COLLECTION_MODELS.get(collection)
        if not model:
            continue
        qs = model.objects.all()
        if hasattr(model, "site"):
            qs = qs.filter(site=site)
        elif collection == "album-tracks":
            qs = qs.filter(album__site=site)
        rows.append(
            {
                "collection": collection,
                "snapshot": len(docs),
                "imported": qs.filter(payload_id__in=[doc["id"] for doc in docs]).count(),
            }
        )
    return rows


def audit_media_references(*, site, snapshot: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    missing = []

    def check(collection, doc, field_name, value):
        media_id = payload_id(value)
        if media_id is None:
            return
        if not Image.objects.filter(site=site, payload_id=media_id).exists():
            missing.append(
                {
                    "collection": collection,
                    "document_id": doc.get("id"),
                    "field": field_name,
                    "media_payload_id": media_id,
                }
            )

    for collection, docs in snapshot.items():
        for doc in docs:
            for field_name in ["featuredImage", "coverImage", "thumbnail", "image", "photo"]:
                check(collection, doc, field_name, doc.get(field_name))
            for item in doc.get("additionalImages") or []:
                check(collection, doc, "additionalImages.image", item.get("image"))
            for item in doc.get("images") or []:
                check(collection, doc, "images.image", item.get("image"))

    return missing


def audit_track_references(*, site, snapshot: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    missing = []
    for doc in snapshot.get("album-tracks", []):
        album_id = payload_id(doc.get("album"))
        song_id = payload_id(doc.get("chanson"))
        if album_id is not None and not Album.objects.filter(site=site, payload_id=album_id).exists():
            missing.append(
                {
                    "document_id": doc.get("id"),
                    "field": "album",
                    "payload_id": album_id,
                }
            )
        if song_id is not None and not Song.objects.filter(site=site, payload_id=song_id).exists():
            missing.append(
                {
                    "document_id": doc.get("id"),
                    "field": "chanson",
                    "payload_id": song_id,
                }
            )
    return missing


def load_unknown_lexical_nodes(log_dir: Path) -> list[dict[str, Any]]:
    path = log_dir / "unknown_lexical_nodes.json"
    if not path.exists():
        return []
    return read_json(path)
