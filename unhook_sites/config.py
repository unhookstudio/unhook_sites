from django.core.exceptions import ImproperlyConfigured


INSECURE_SECRET_KEYS = {
    "",
    "change-me",
    "change-me-in-production",
    "django-insecure-local-dev-change-me",
}


def validate_secret_key(debug: bool, secret_key: str) -> None:
    if debug:
        return
    if secret_key in INSECURE_SECRET_KEYS or secret_key.startswith("django-insecure"):
        raise ImproperlyConfigured("Set a strong SECRET_KEY when DEBUG is False.")
