import json
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen


DEFAULT_PAYLOAD_BASE_URL = "https://www.kent-artiste.com"

DEFAULT_COLLECTIONS = [
    "media",
    "posts",
    "albums",
    "chansons",
    "album-tracks",
    "video-clips",
    "livres",
    "bds",
    "dessins",
    "dates",
    "dates-cles",
    "photos",
    "photo-stories",
    "photo-collections",
]

DEFAULT_GLOBALS = [
    "a-propos",
    "contact",
    "mentions-legales",
    "site_texts",
    "mais-encore",
]


def fetch_payload_page(
    collection: str,
    *,
    base_url: str = DEFAULT_PAYLOAD_BASE_URL,
    limit: int = 100,
    page: int = 1,
    depth: int = 1,
) -> dict[str, Any]:
    query = urlencode({"limit": limit, "page": page, "depth": depth})
    url = f"{base_url.rstrip('/')}/api/{collection}?{query}"
    with urlopen(url, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_payload_collection(
    collection: str,
    *,
    base_url: str = DEFAULT_PAYLOAD_BASE_URL,
    limit: int = 100,
    depth: int = 1,
    max_docs: int | None = None,
) -> dict[str, Any]:
    docs = []
    page = 1
    last_payload: dict[str, Any] = {}
    while True:
        payload = fetch_payload_page(
            collection,
            base_url=base_url,
            limit=limit,
            page=page,
            depth=depth,
        )
        last_payload = payload
        docs.extend(payload.get("docs", []))
        if max_docs is not None and len(docs) >= max_docs:
            docs = docs[:max_docs]
            break
        if not payload.get("hasNextPage"):
            break
        page += 1

    return {
        "docs": docs,
        "totalDocs": last_payload.get("totalDocs", len(docs)),
        "sourceCollection": collection,
    }


def fetch_payload_global(
    slug: str,
    *,
    base_url: str = DEFAULT_PAYLOAD_BASE_URL,
) -> dict[str, Any]:
    url = f"{base_url.rstrip('/')}/api/globals/{slug}"
    with urlopen(url, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))
