from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from payload_migration.audit import audit_snapshot
from payload_migration.client import write_json
from sites_core.models import Site


class Command(BaseCommand):
    help = "Write a JSON migration audit report."

    def add_arguments(self, parser):
        parser.add_argument("--site", required=True)
        parser.add_argument("--input-dir", default=settings.BASE_DIR / "data" / "payload" / "raw")
        parser.add_argument("--log-dir", default=settings.BASE_DIR / "data" / "payload" / "logs")
        parser.add_argument(
            "--output",
            default=settings.BASE_DIR / "data" / "payload" / "logs" / "migration_report.json",
        )

    def handle(self, *args, **options):
        try:
            site = Site.objects.get(slug=options["site"])
        except Site.DoesNotExist as exc:
            raise CommandError(f"Unknown site slug: {options['site']}") from exc

        report = audit_snapshot(
            site=site,
            input_dir=Path(options["input_dir"]),
            log_dir=Path(options["log_dir"]),
        )
        write_json(Path(options["output"]), report)
        self.stdout.write(self.style.SUCCESS(f"Wrote migration report to {options['output']}"))
