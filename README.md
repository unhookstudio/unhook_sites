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

## Production

The preferred production workflow is Docker + Gunicorn behind a reverse proxy.

Persistent server layout:

```text
/srv/unhook_sites/
  compose.yml
  .env
  data/
    db.sqlite3
    media/
    staticfiles/
    backups/
```

The container mounts `/srv/unhook_sites/data` at `/data`, and production `.env`
should use:

```env
DATABASE_URL=sqlite:////data/db.sqlite3
MEDIA_ROOT=/data/media
STATIC_ROOT=/data/staticfiles
```

Initial server commands:

```sh
docker compose pull
docker compose run --rm web uv run --no-sync python manage.py migrate
docker compose run --rm web uv run --no-sync python manage.py collectstatic --noinput
docker compose up -d
```

For a non-Docker run, start Gunicorn directly:

```sh
uv sync --frozen
uv run python manage.py migrate
uv run python manage.py collectstatic --noinput
uv run gunicorn unhook_sites.wsgi:application \
  --bind 127.0.0.1:8000 \
  --workers 2 \
  --timeout 60
```

Recommended persistent paths on the server:

```text
/srv/unhook_sites/data/db.sqlite3
/srv/unhook_sites/data/media/
/srv/unhook_sites/data/staticfiles/
```
