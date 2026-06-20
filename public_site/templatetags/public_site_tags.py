from django import template
from django.utils.html import format_html

from media_library.models import Image


register = template.Library()


@register.filter
def year(value):
    if not value:
        return ""
    return value.year


@register.filter
def rich(value):
    return value or ""


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
