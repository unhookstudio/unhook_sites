from django import forms
from django.db import models
from django.forms.fields import from_current_timezone
from django_prose_editor.widgets import AdminProseEditorWidget

from sites_core.admin import SiteScopedAdmin


class BrowserSplitDateTimeWidget(forms.SplitDateTimeWidget):
    def __init__(self, attrs=None):
        super().__init__(
            attrs,
            date_format="%Y-%m-%d",
            time_format="%H:%M",
            date_attrs={"type": "date"},
            time_attrs={
                "type": "time",
                "step": "60",
            },
        )


class DateOnlyFriendlySplitDateTimeField(forms.SplitDateTimeField):
    def __init__(self, *args, default_time: str = "00:00", **kwargs):
        self.default_time = default_time
        kwargs.setdefault("widget", BrowserSplitDateTimeWidget())
        super().__init__(*args, **kwargs)

    def clean(self, value):
        if isinstance(value, (list, tuple)) and len(value) == 2 and value[0] and not value[1]:
            value = [value[0], self.default_time]
        cleaned = super().clean(value)
        return from_current_timezone(cleaned) if cleaned else cleaned


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
