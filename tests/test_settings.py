import pytest
from django.core.exceptions import ImproperlyConfigured

from unhook_sites.config import validate_secret_key


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
