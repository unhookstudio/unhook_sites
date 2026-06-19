from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from payload_migration.client import (
    DEFAULT_COLLECTIONS,
    DEFAULT_GLOBALS,
    DEFAULT_PAYLOAD_BASE_URL,
    fetch_payload_collection,
    fetch_payload_global,
    write_json,
)


class Command(BaseCommand):
    help = "Export raw Payload API JSON snapshots."

    def add_arguments(self, parser):
        parser.add_argument("--base-url", default=DEFAULT_PAYLOAD_BASE_URL)
        parser.add_argument("--output-dir", default=settings.BASE_DIR / "data" / "payload" / "raw")
        parser.add_argument("--collection", action="append", dest="collections")
        parser.add_argument("--skip-globals", action="store_true")
        parser.add_argument("--limit", type=int, default=100)
        parser.add_argument("--depth", type=int, default=1)
        parser.add_argument("--max-docs", type=int)
        parser.add_argument("--pilot", action="store_true", help="Export only a small pilot subset.")

    def handle(self, *args, **options):
        output_dir = Path(options["output_dir"])
        collections = options["collections"] or DEFAULT_COLLECTIONS
        max_docs = options["max_docs"]
        if options["pilot"] and max_docs is None:
            max_docs = 3

        for collection in collections:
            payload = fetch_payload_collection(
                collection,
                base_url=options["base_url"],
                limit=options["limit"],
                depth=options["depth"],
                max_docs=max_docs,
            )
            write_json(output_dir / f"{collection}.json", payload)
            self.stdout.write(f"Exported {collection}: {len(payload['docs'])} docs")

        if options["skip_globals"]:
            return

        for slug in DEFAULT_GLOBALS:
            payload = fetch_payload_global(slug, base_url=options["base_url"])
            write_json(output_dir / "globals" / f"{slug}.json", payload)
            self.stdout.write(f"Exported global {slug}")
