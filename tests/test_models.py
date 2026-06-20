import pytest
from django.core.exceptions import ValidationError

from media_library.models import Image
from sites_core.models import Redirect, Site, SiteSettings


def test_redirect_status_code_is_limited_to_redirect_codes(db):
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    redirect = Redirect(site=site, old_path="/old/", new_url_or_path="/new/", status_code=200)

    with pytest.raises(ValidationError):
        redirect.full_clean()


def test_site_settings_hero_image_must_belong_to_same_site(db):
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    other = Site.objects.create(name="Other", slug="other", domain="example.com")
    image = Image.objects.create(site=other, title="Other image")
    site_settings = SiteSettings(site=site, homepage_hero_image=image)

    with pytest.raises(ValidationError):
        site_settings.full_clean()
