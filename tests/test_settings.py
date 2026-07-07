import pytest
from django.core.exceptions import ImproperlyConfigured
from environ import Env

from unhook_sites.config import validate_secret_key
from unhook_sites.settings import STATICFILES_STORAGE_BACKEND


@pytest.mark.parametrize(
    "secret_key",
    ["", "change-me", "change-me-in-production", "django-insecure-local-dev-change-me"],
)
def test_production_debug_false_rejects_insecure_secret(secret_key):
    with pytest.raises(ImproperlyConfigured):
        validate_secret_key(debug=False, secret_key=secret_key)


def test_debug_true_allows_local_insecure_secret():
    validate_secret_key(debug=True, secret_key="django-insecure-local-dev-change-me")


def test_production_debug_false_allows_real_secret():
    validate_secret_key(debug=False, secret_key="not-a-placeholder-secret")


def test_secure_proxy_ssl_header_parses_as_tuple(monkeypatch):
    monkeypatch.setenv("SECURE_PROXY_SSL_HEADER", "HTTP_X_FORWARDED_PROTO,https")
    env = Env()

    assert env.tuple("SECURE_PROXY_SSL_HEADER", default=None) == (
        "HTTP_X_FORWARDED_PROTO",
        "https",
    )


def test_staticfiles_storage_is_plain_in_debug():
    assert STATICFILES_STORAGE_BACKEND == "django.contrib.staticfiles.storage.StaticFilesStorage"
