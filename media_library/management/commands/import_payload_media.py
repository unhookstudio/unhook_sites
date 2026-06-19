from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from media_library.payload import (
    DEFAULT_PAYLOAD_BASE_URL,
    fetch_payload_collection,
    upsert_payload_media_doc,
)
from sites_core.models import Site


class Command(BaseCommand):
    help = "Import Payload media metadata into the local media library."

    def add_arguments(self, parser):
        parser.add_argument("--site", required=True, help="Site slug to attach media to.")
        parser.add_argument("--base-url", default=DEFAULT_PAYLOAD_BASE_URL)
        parser.add_argument("--limit", type=int, default=100)
        parser.add_argument(
            "--atomic",
            action="store_true",
            help="Roll back the whole import if any media record fails.",
        )

    def handle(self, *args, **options):
        try:
            site = Site.objects.get(slug=options["site"])
        except Site.DoesNotExist as exc:
            raise CommandError(f"Unknown site slug: {options['site']}") from exc

        docs = fetch_payload_collection(
            "media",
            base_url=options["base_url"],
            limit=options["limit"],
            depth=0,
        )
        if options["atomic"]:
            imported = self._import_atomic(site=site, docs=docs, base_url=options["base_url"])
            self.stdout.write(
                self.style.SUCCESS(f"Imported {imported} of {len(docs)} fetched media records.")
            )
            return

        imported = 0
        failures = []
        for doc in docs:
            try:
                with transaction.atomic():
                    upsert_payload_media_doc(site=site, doc=doc, base_url=options["base_url"])
                imported += 1
            except Exception as exc:  # noqa: BLE001 - import should continue and summarize.
                failures.append((doc.get("id", "unknown"), str(exc)))

        self.stdout.write(
            self.style.SUCCESS(f"Imported {imported} of {len(docs)} fetched media records.")
        )
        if failures:
            self.stderr.write(self.style.ERROR(f"Failed to import {len(failures)} media records:"))
            for payload_id, error in failures:
                self.stderr.write(f"- payload_id:{payload_id}: {error}")
            raise CommandError(f"Failed to import {len(failures)} media records.")

    def _import_atomic(self, *, site, docs, base_url):
        imported = 0
        with transaction.atomic():
            for doc in docs:
                upsert_payload_media_doc(site=site, doc=doc, base_url=base_url)
                imported += 1
        return imported
