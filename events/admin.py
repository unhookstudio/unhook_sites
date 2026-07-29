from django import forms
from django.contrib import admin

from unhook_sites.admin import DateOnlyFriendlySplitDateTimeField, DomainModelAdmin

from .models import Event, KeyDate


class EventAdminForm(forms.ModelForm):
    date = DateOnlyFriendlySplitDateTimeField(label="Date", required=False)
    end_date = DateOnlyFriendlySplitDateTimeField(label="Date de fin", required=False)

    class Meta:
        model = Event
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("date") and self._time_part_is_blank("date"):
            cleaned_data["hide_time"] = True
        if cleaned_data.get("end_date") and self._time_part_is_blank("end_date"):
            cleaned_data["hide_time"] = True
        return cleaned_data

    def _time_part_is_blank(self, field_name: str) -> bool:
        return not self.data.get(f"{self.add_prefix(field_name)}_1", "").strip()


@admin.register(Event)
class EventAdmin(DomainModelAdmin):
    form = EventAdminForm
    rich_text_fields = ("description_html",)
    list_display = [
        "title",
        "site",
        "date",
        "end_date",
        "hide_time",
        "location_details",
        "is_published",
        "payload_id",
    ]
    list_filter = ["site", "is_published"]
    search_fields = ["title", "slug", "location_details", "payload_id"]
    prepopulated_fields = {"slug": ["title"]}


@admin.register(KeyDate)
class KeyDateAdmin(DomainModelAdmin):
    rich_text_fields = ("description_html",)
    list_display = ["title", "site", "date", "is_published", "payload_id"]
    list_filter = ["site", "is_published"]
    search_fields = ["title", "slug", "payload_id"]
    prepopulated_fields = {"slug": ["title"]}
