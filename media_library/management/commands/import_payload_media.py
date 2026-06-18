from django.core.management.base import BaseCommand, CommandError

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
        for doc in docs:
            upsert_payload_media_doc(site=site, doc=doc, base_url=options["base_url"])

        self.stdout.write(self.style.SUCCESS(f"Imported {len(docs)} media records."))
