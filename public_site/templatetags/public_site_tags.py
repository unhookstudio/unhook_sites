import re
from html import unescape

from django import template
from django.utils import formats, timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from media_library.models import Image


register = template.Library()

LINK_OPEN_RE = re.compile(r"<a(?P<attrs>\s[^>]*)?>", re.IGNORECASE)
FRENCH_MONTH_BADGES = {
    1: "janv.",
    2: "févr.",
    3: "mars",
    4: "avr.",
    5: "mai",
    6: "juin",
    7: "juil.",
    8: "août",
    9: "sept.",
    10: "oct.",
    11: "nov.",
    12: "déc.",
}


@register.filter
def year(value):
    if not value:
        return ""
    return value.year


@register.filter
def rich(value):
    return value or ""


@register.filter
def html_unescape(value):
    if value is None:
        return ""
    return unescape(str(value))


@register.filter
def links_new_tab(value):
    if not value:
        return ""

    def replace_link(match):
        attrs = match.group("attrs") or ""
        lower_attrs = attrs.lower()
        if "target=" not in lower_attrs:
            attrs += ' target="_blank"'
        if "rel=" not in lower_attrs:
            attrs += ' rel="noopener noreferrer"'
        return f"<a{attrs}>"

    return mark_safe(LINK_OPEN_RE.sub(replace_link, str(value)))


@register.filter
def article_category_label(value: str) -> str:
    labels = {
        "journal": "Journal",
        "news": "Actualités",
        "press": "Presse",
        "coup-de-coeur": "Coup de cœur",
        "coups-de-coeur": "Coup de cœur",
        "other": "Autre",
    }
    return labels.get(value, value)


@register.simple_tag
def event_date_label(event) -> str:
    if not event.date:
        return ""

    start = timezone.localtime(event.date)
    end = timezone.localtime(event.end_date) if event.end_date else None
    show_time = not event.hide_time

    if end and end.date() != start.date():
        start_label = formats.date_format(start, "l j F")
        end_format = "l j F Y" if end.year == start.year else "l j F Y"
        end_label = formats.date_format(end, end_format)
        return f"Du {start_label} au {end_label}"

    date_label = formats.date_format(start, "l j F Y")
    if show_time:
        time_label = formats.time_format(start, "H:i")
        return f"{date_label} à {time_label}"
    return date_label


@register.simple_tag
def event_date_badge(event) -> dict[str, str | bool]:
    if not event.date:
        return {"day": "", "month": "", "is_range": False}

    start = timezone.localtime(event.date)
    end = timezone.localtime(event.end_date) if event.end_date else None

    if end and end.date() != start.date() and end.month == start.month and end.year == start.year:
        return {
            "day": f"{start.day}-{end.day}",
            "month": FRENCH_MONTH_BADGES[start.month],
            "is_range": True,
        }

    return {
        "day": formats.date_format(start, "j"),
        "month": FRENCH_MONTH_BADGES[start.month],
        "is_range": False,
    }


@register.simple_tag
def image_url(image: Image | None, kind: str = "") -> str:
    if not image:
        return ""

    if kind:
        variant = image.variants.filter(kind=kind).first()
        if variant and variant.file:
            return variant.file.url

    if image.original:
        return image.original.url
    return ""


@register.simple_tag
def image_tag(image: Image | None, alt: str = "", css_class: str = "", kind: str = ""):
    url = image_url(image, kind)
    if not url:
        return ""
    return format_html('<img src="{}" alt="{}" class="{}" />', url, alt, css_class)
