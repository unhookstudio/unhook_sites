from django.db import models
from django_prose_editor.widgets import AdminProseEditorWidget

from sites_core.admin import SiteScopedAdmin


class RichTextAdminMixin:
    rich_text_fields: tuple[str, ...] = ()

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if isinstance(db_field, models.TextField) and db_field.name in self.rich_text_fields:
            kwargs["widget"] = AdminProseEditorWidget
        return super().formfield_for_dbfield(db_field, request, **kwargs)


class DomainModelAdmin(RichTextAdminMixin, SiteScopedAdmin):
    readonly_fields = ["payload_id", "created_at", "updated_at"]
    admin_field_labels = {
        "is_published": "Publié",
        "published_at": "Publié le",
        "payload_id": "ID Payload",
        "payload_description": "description Payload",
        "created_at": "Créé le",
        "updated_at": "Modifié le",
    }

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in self.admin_field_labels:
            kwargs.setdefault("label", self.admin_field_labels[db_field.name])
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if request.user.is_superuser:
            return readonly_fields
        payload_fields = [
            field.name
            for field in self.model._meta.fields
            if field.name.startswith("payload_") and field.name not in readonly_fields
        ]
        return [*readonly_fields, *payload_fields]
