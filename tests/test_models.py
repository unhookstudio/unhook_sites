import pytest
from django.core.exceptions import ValidationError

from sites_core.models import Redirect, Site


def test_redirect_status_code_is_limited_to_redirect_codes(db):
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    redirect = Redirect(site=site, old_path="/old/", new_url_or_path="/new/", status_code=200)

    with pytest.raises(ValidationError):
        redirect.full_clean()
