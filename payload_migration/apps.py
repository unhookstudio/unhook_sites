from django.apps import AppConfig


class PayloadMigrationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "payload_migration"
    verbose_name = "Migration Payload"
