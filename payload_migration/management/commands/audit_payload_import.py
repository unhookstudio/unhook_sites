from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from payload_migration.audit import audit_snapshot
from sites_core.models import Site


class Command(BaseCommand):
    help = "Audit imported Payload snapshot coverage and unresolved references."

    def add_arguments(self, parser):
        parser.add_argument("--site", required=True)
        parser.add_argument("--input-dir", default=settings.BASE_DIR / "data" / "payload" / "raw")
        parser.add_argument("--log-dir", default=settings.BASE_DIR / "data" / "payload" / "logs")
        parser.add_argument("--collection", action="append", dest="collections")

    def handle(self, *args, **options):
        try:
            site = Site.objects.get(slug=options["site"])
        except Site.DoesNotExist as exc:
            raise CommandError(f"Unknown site slug: {options['site']}") from exc

        report = audit_snapshot(
            site=site,
            input_dir=Path(options["input_dir"]),
            log_dir=Path(options["log_dir"]),
            collections=options["collections"],
        )

        self.stdout.write("Counts:")
        for row in report["counts"]:
            self.stdout.write(f"- {row['collection']}: imported {row['imported']} / snapshot {row['snapshot']}")

        self.stdout.write(f"Unresolved media references: {len(report['unresolved_media'])}")
        for row in report["unresolved_media"][:20]:
            self.stdout.write(
                f"- {row['collection']}:{row['document_id']} {row['field']} -> media {row['media_payload_id']}"
            )

        self.stdout.write(f"Unresolved track references: {len(report['unresolved_tracks'])}")
        for row in report["unresolved_tracks"][:20]:
            self.stdout.write(
                f"- album-track:{row['document_id']} {row['field']} -> {row['payload_id']}"
            )

        self.stdout.write(f"Unknown Lexical nodes: {len(report['unknown_lexical_nodes'])}")
