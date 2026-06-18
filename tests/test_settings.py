import importlib

import pytest
from django.core.exceptions import ImproperlyConfigured


def test_production_debug_false_rejects_insecure_secret(monkeypatch):
    monkeypatch.setenv("DEBUG", "False")
    monkeypatch.setenv("SECRET_KEY", "django-insecure-local-dev-change-me")

    import unhook_sites.settings

    with pytest.raises(ImproperlyConfigured):
        importlib.reload(unhook_sites.settings)

    monkeypatch.setenv("DEBUG", "True")
    importlib.reload(unhook_sites.settings)
