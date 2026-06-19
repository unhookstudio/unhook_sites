from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from payload_migration.client import DEFAULT_COLLECTIONS, read_json, write_json
from payload_migration.importers import PayloadSnapshotImporter
from sites_core.models import Site


class Command(BaseCommand):
    help = "Import a raw Payload snapshot into Django models."

    def add_arguments(self, parser):
        parser.add_argument("--site", required=True)
        parser.add_argument("--input-dir", default=settings.BASE_DIR / "data" / "payload" / "raw")
        parser.add_argument("--log-dir", default=settings.BASE_DIR / "data" / "payload" / "logs")
        parser.add_argument("--collection", action="append", dest="collections")
        parser.add_argument("--max-docs", type=int)
        parser.add_argument("--pilot", action="store_true", help="Import only a small pilot subset.")

    def handle(self, *args, **options):
        try:
            site = Site.objects.get(slug=options["site"])
        except Site.DoesNotExist as exc:
            raise CommandError(f"Unknown site slug: {options['site']}") from exc

        input_dir = Path(options["input_dir"])
        collections = options["collections"] or DEFAULT_COLLECTIONS
        max_docs = options["max_docs"]
        if options["pilot"] and max_docs is None:
            max_docs = 3

        snapshot = {}
        for collection in collections:
            path = input_dir / f"{collection}.json"
            if not path.exists():
                continue
            payload = read_json(path)
            snapshot[collection] = payload.get("docs", payload)

        importer = PayloadSnapshotImporter(site=site)
        counts = importer.import_snapshot(snapshot, max_docs=max_docs)
        for collection, count in counts.items():
            if count:
                self.stdout.write(f"Imported {collection}: {count}")

        unknown_nodes = importer.converter.unknown_as_dicts()
        if unknown_nodes:
            log_path = Path(options["log_dir"]) / "unknown_lexical_nodes.json"
            write_json(log_path, unknown_nodes)
            self.stderr.write(self.style.WARNING(f"Logged {len(unknown_nodes)} unknown Lexical nodes to {log_path}"))
