# Unhook Sites

Plain Django + SQLite rebuild for small content sites, starting with kent-artiste.com.

## Development

Install dependencies and run Django commands through `uv`:

```sh
uv sync
uv run python manage.py check
uv run python manage.py migrate
```

Copy `.env.example` to `.env` for local overrides.

