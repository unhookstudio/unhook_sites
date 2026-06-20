# Static Public Layer Strategy

The Django app should remain the source of truth: admin, imports, previews, media metadata, domain relations, drafts, and site settings all stay in Django.

The public site, however, can be served as mostly static output once the frontend port and content QA are complete. Kent is an especially good fit because almost every public page can be cached aggressively. The only content that changes regularly is the dates/events surface, and even that can be regenerated cheaply.

## Goals

- Keep Django as the editing and migration system.
- Serve public pages as fast, cacheable HTML whenever practical.
- Keep admin, preview, import, audit, and rebuild workflows dynamic.
- Support exporting one site at a time, so future sites in the project can deploy independently.
- Avoid coupling the deployment model to Kent-specific assumptions.

## Recommended Path

### 1. Django First

Finish the public Django templates normally.

This keeps development simple while content models, imports, admin editing, and visual QA are still moving.

Public routes continue to work as normal Django views:

- `/`
- `/musique`
- `/album/<slug>`
- `/chanson/<slug>`
- `/livres`
- `/livres/<slug>`
- `/dessins`
- `/dessins/<slug>`
- `/posts`
- `/post/<slug>`
- `/sitemap.xml`
- `/robots.txt`

### 2. Add HTTP/Reverse-Proxy Caching

Before building a static exporter, a reverse-proxy cache is the simplest performance upgrade.

Recommended behavior:

- Cache public `GET` and `HEAD` responses.
- Bypass cache for `/admin/`, authenticated users, previews, imports, and management endpoints.
- Serve `/static/` and `/media/` directly from the web server or CDN.
- Purge affected URLs after publishing changes, or use short cache TTLs during the first deployment.

This can be done with Caddy, Nginx, Cloudflare, Fastly, or similar.

### 3. Add Static Export

Once the frontend and content are stable, add a management command that renders public Django URLs into static files.

Suggested command:

```bash
python manage.py export_static_site --site kent --output var/static_export/kent
```

Useful options:

```bash
python manage.py export_static_site --site kent
python manage.py export_static_site --site kent --output /srv/www/kent-artiste.com
python manage.py export_static_site --site kent --changed-only
python manage.py export_static_site --site kent --include-events-only
python manage.py export_static_site --site kent --fail-on-broken-links
```

The command should resolve the `Site` by slug, render with that site's domain/host context, and write each public URL to `index.html` style paths:

- `/` -> `index.html`
- `/musique` -> `musique/index.html`
- `/album/hail-hail-rock-n-roll` -> `album/hail-hail-rock-n-roll/index.html`

Assets remain separate:

- static assets from `collectstatic`
- media files from `MEDIA_ROOT`, ideally served directly or synced beside the export

## Per-Site Export

Every export command should require an explicit site.

Good:

```bash
python manage.py export_static_site --site kent
python manage.py export_static_site --site another-client
```

Avoid:

```bash
python manage.py export_static_site
```

The explicit `--site` flag matters because this project is intended to host several small sites. Each site can have separate domains, routes, theme assets, deployment targets, and rebuild schedules.

Later, if needed, add a convenience command:

```bash
python manage.py export_all_static_sites
```

That should internally call the same per-site exporter for each enabled `Site`.

## URL Inventory

The exporter should not crawl blindly as its primary source of truth. It should build a deterministic URL list from models and route definitions.

For Kent, initial exported URLs should include:

- fixed pages: home, musique, livres, dessins, posts, robots, sitemap
- published albums
- published songs
- published books
- published B.D.s and drawings
- published articles

Events/dates can be handled in the same full export because the site is small. If this becomes slow, add a partial export path that regenerates only:

- homepage
- any future event index/detail pages
- sitemap

## Cache Invalidation

The simplest model is full rebuild on publish.

For Kent, this is likely fast enough and much safer than clever invalidation.

Later, partial rebuild rules can be added:

- Article changed: article detail, posts index, homepage, sitemap
- Album changed: album detail, musique index, homepage if featured album uses it, sitemap
- Song changed: song detail, related album pages, musique index, sitemap
- Book changed: book detail, livres index, dessins index if illustrated placement applies, sitemap
- BD/Drawing changed: detail page, dessins index, sitemap
- Event changed: homepage, event pages if added, sitemap
- SiteSettings changed: homepage and any page that consumes the changed setting

## Dynamic Exceptions

Keep these dynamic:

- `/admin/`
- login/logout/password flows
- import/export/audit commands
- preview routes if added
- newsletter POST handling

For newsletter signup, prefer posting to Django or directly to MailerLite. Static pages can still contain a normal form whose `action` targets a dynamic Django endpoint or an external service.

## Deployment Shape

One practical deployment layout:

```text
/srv/unhook_sites/
  app/                  # Django project
  media/                # filesystem media
  staticfiles/          # collectstatic output
  exports/
    kent/
      index.html
      musique/index.html
      ...
```

The web server serves:

- public HTML from `exports/<site>/`
- `/static/` from `staticfiles/`
- `/media/` from `media/`
- `/admin/` and dynamic endpoints through Django

This keeps public traffic off Django for normal page views while preserving Django as the content system.

## When To Build This

Do not build the static exporter before the public templates and imported content are mostly stable.

Good timing:

1. Finish the frontend port.
2. Complete content QA in Django admin.
3. Confirm URLs, slugs, media, sitemap, and redirects.
4. Add `export_static_site --site kent`.
5. Deploy behind static serving or a reverse-proxy cache.

Until then, normal Django views are easier to debug and change.
