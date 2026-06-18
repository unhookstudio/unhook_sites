import json
from datetime import datetime
from typing import Any
from urllib.parse import urljoin
from urllib.request import urlopen

from django.utils.dateparse import parse_datetime

from .models import Image, ImageVariant


DEFAULT_PAYLOAD_BASE_URL = "https://www.kent-artiste.com"


def fetch_payload_collection(
    collection: str,
    *,
    base_url: str = DEFAULT_PAYLOAD_BASE_URL,
    limit: int = 100,
    depth: int = 0,
) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    page = 1
    while True:
        url = f"{base_url.rstrip('/')}/api/{collection}?limit={limit}&page={page}&depth={depth}"
        with urlopen(url, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
        docs.extend(payload["docs"])
        if not payload.get("hasNextPage"):
            return docs
        page += 1


def absolute_payload_url(url: str, *, base_url: str = DEFAULT_PAYLOAD_BASE_URL) -> str:
    if not url:
        return ""
    return urljoin(f"{base_url.rstrip('/')}/", url.lstrip("/"))


def parse_payload_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return parse_datetime(value)


def upsert_payload_media_doc(
    *,
    site,
    doc: dict[str, Any],
    base_url: str = DEFAULT_PAYLOAD_BASE_URL,
) -> Image:
    image, _ = Image.objects.update_or_create(
        site=site,
        payload_id=doc["id"],
        defaults={
            "title": doc.get("alt") or doc.get("filename") or "",
            "alt_text": doc.get("alt") or "",
            "caption": "",
            "width": doc.get("width"),
            "height": doc.get("height"),
            "filesize": doc.get("filesize"),
            "mime_type": doc.get("mimeType") or "",
            "filename": doc.get("filename") or "",
            "payload_url": absolute_payload_url(doc.get("url") or "", base_url=base_url),
            "payload_thumbnail_url": absolute_payload_url(
                doc.get("thumbnailURL") or "",
                base_url=base_url,
            ),
            "payload_created_at": parse_payload_datetime(doc.get("createdAt")),
            "payload_updated_at": parse_payload_datetime(doc.get("updatedAt")),
        },
    )
    for kind, variant_data in (doc.get("sizes") or {}).items():
        if not variant_data or not variant_data.get("url"):
            continue
        ImageVariant.objects.update_or_create(
            image=image,
            kind=kind if kind in ImageVariant.Kind.values else ImageVariant.Kind.OTHER,
            defaults={
                "width": variant_data.get("width"),
                "height": variant_data.get("height"),
                "filesize": variant_data.get("filesize"),
                "mime_type": variant_data.get("mimeType") or "",
                "filename": variant_data.get("filename") or "",
                "payload_url": absolute_payload_url(variant_data.get("url") or "", base_url=base_url),
            },
        )
    return image
