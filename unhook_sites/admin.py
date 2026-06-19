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
