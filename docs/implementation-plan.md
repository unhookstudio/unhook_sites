# Unhook Sites Implementation Plan

This project should stay intentionally small: Django, SQLite, Django templates, Django admin, filesystem media, and HTMX only where it removes friction. The first target site is Kent, but the code should be shaped so later small client sites can reuse the same domain apps without turning the system into a generic page builder.

## Guiding Decisions

- Use plain Django, not Wagtail, unless editorial workflow needs grow later.
- Use hard-coded views/templates for public pages.
- Let users edit fixed fields and domain content in Django admin.
- Use `django-prose-editor` for rich text fields.
- Store media on the server filesystem at first.
- Keep old Payload IDs during migration for traceability and relationship mapping.
- Keep original Payload rich text JSON until migration QA passes. This is not optional.
- Add an `is_published` checkbox to most public content models so editors can work on drafts. Versioning is not needed.
- Use French-first URLs and content. Kent uses root URLs, not `/fr/`, unless real multilingual content appears before launch.
- Use `pyproject.toml` and `uv` for Python dependency management.
- Add migration tests and smoke tests early; do not leave tests as post-launch cleanup.
- Avoid creating a public API until there is a real second consumer.
- Add HTMX only after the basic server-rendered pages and forms work.

## Phase 1: Project Foundation

Goal: make the new Django project production-shaped before adding domain logic.

Tasks:

- Add baseline project files:
  - `README.md`
  - `.env.example`
  - `pyproject.toml`
  - `uv.lock`
  - `docs/`
- Use `uv` for dependency management:
  - `uv add django pillow django-prose-editor django-environ pytest pytest-django`
  - avoid introducing `requirements.txt` unless deployment tooling forces it
- Install early dependencies:
  - Django
  - Pillow
  - django-prose-editor
  - django-environ
  - pytest
  - pytest-django
- Split settings enough to avoid local/production secrets in code:
  - `SECRET_KEY` from env
  - `DEBUG` from env
  - `ALLOWED_HOSTS` from env
  - SQLite database path from env, defaulting to `BASE_DIR / "db.sqlite3"`
- Decide locale and URL policy now:
  - `LANGUAGE_CODE = "fr-fr"`
  - `TIME_ZONE = "Europe/Paris"`
  - `USE_I18N = True`
  - `USE_TZ = True`
  - no `/fr/` URL prefix for Kent; French is the canonical root language
  - no per-language content fields until a concrete multilingual site requires them
- Add SEO and syndication primitives early:
  - stable URL naming conventions
  - `robots.txt`
  - `sitemap.xml`
  - RSS or Atom feed for articles/posts
  - canonical URL helper
  - metadata fields where needed (`meta_title`, `meta_description`, social image)
- Configure media/static paths:
  - `MEDIA_URL = "/media/"`
  - `MEDIA_ROOT = BASE_DIR / "media"`
  - `STATIC_URL = "/static/"`
  - `STATIC_ROOT = BASE_DIR / "staticfiles"`
- Add development media serving in `urls.py`.
- Run initial migrations.
- Create a superuser.

Deliverable:

- Fresh Django app boots locally.
- Admin is reachable.
- Static/media settings are explicit.
- No content model decisions are buried in settings.
- Locale, URL, sitemap, robots, and feed decisions are in place before templates are built.
- Test runner is configured before migration code exists.

## Phase 2: Core Tenancy And Shared Admin

Goal: establish the reusable multi-site boundary before domain models depend on it.

Create an app `sites_core`.

Models:

- `Site`
  - `name`
  - `slug`
  - `domain`
  - `is_active`
  - optional theme/display fields later
- `SiteSettings`
  - one-to-one with `Site`
  - fixed editable text for common chrome/footer/newsletter defaults
  - social links if shared across client types
- `NavigationLink`
  - `site`
  - `label`
  - `url`
  - `order`
  - `is_active`
- `Redirect`
  - `site`
  - `old_path`
  - `new_url_or_path`
  - `status_code`
  - `is_active`

Shared abstractions:

- `SiteOwnedModel`
  - abstract model with `site`, `created_at`, `updated_at`
- `SiteScopedAdmin`
  - superuser sees all sites
  - staff users see only allowed sites
  - non-superuser saves default to their site
- Custom `User` model now, before serious migrations:
  - `sites = ManyToManyField(Site)`
  - `default_site = ForeignKey(Site)`

Recommendation:

- Add the custom user model before the first serious migration. It is much cheaper now than later, and this project is still early enough.

Deliverable:

- Core `Site` exists.
- Admin can manage a Kent site row.
- Staff/site access pattern is in place before content imports begin.

## Phase 3: Media Library

Goal: define local media storage before importing Payload content that references images.

Create `media_library`.

Models:

- `Image`
  - `site`
  - `title`
  - `alt_text`
  - `caption`
  - `original`
  - `width`
  - `height`
  - `payload_id`
  - `payload_url`
  - `created_at`
  - `updated_at`
- `ImageVariant`
  - `image`
  - `kind` (`thumbnail`, `small`, `medium`, `large`, etc.)
  - `file`
  - `width`
  - `height`
  - `filesize`
- `Document`, only if needed.

When to download images:

- Do not download images before the `Image` and `ImageVariant` models exist.
- First import media metadata from Payload into the media tables.
- Then run a separate download command that fetches originals and selected variants.
- Keep the download command idempotent:
  - skip files already present with matching size
  - retry failed downloads
  - record failures

Initial policy:

- Download originals and the variants already referenced by the existing site.
- Do not regenerate all variants until the templates prove what sizes are actually needed.
- Store files under a site-aware path such as:
  - `media/sites/kent/images/originals/...`
  - `media/sites/kent/images/variants/...`

Deliverable:

- Media records exist locally.
- Files can be downloaded from live Payload API/media routes.
- Admin can inspect images.

## Phase 4: Domain Models

Goal: create clean Django models that represent the site, not Payload internals.

Start with the models needed by Kent's current public pages. Add fields only when the migration or templates need them.

Recommended app split:

- `events`
  - `Event`
- `people`
  - `Person`
  - `Credit`
- `music`
  - `Artist`
  - `Album`
  - `Song`
  - `Track`
  - `SongAppearance`
  - `VideoClip`
- `writing`
  - `Article`
  - `Book`
  - `Publication` if needed
- `visual_art`
  - `Artwork`
  - `Series`
  - `Exhibition` if needed
- `photos`
  - `Photo`
  - `PhotoStory`
  - `PhotoCollection`
- `pages`
  - fixed-page settings models only if needed
  - avoid a generic block/page builder

Cross-cutting model conventions:

- Add `site` to client-owned models.
- Add `payload_id` to migrated models.
- Add `slug` where public URLs need it.
- Add `is_published` to most public content models for draft/unpublish workflows.
- Add `published_at` where ordering or feeds need publication dates.
- Add date fields as nullable until import proves all records have them.
- Prefer explicit relationships over generic foreign keys.
- Store rich text as sanitized HTML in `ProseEditorField`.
- Keep original Payload rich text JSON in `payload_rich_text` until import QA passes.

Kent-specific first pass:

- `music.Artist`
- `music.Album`
- `music.Song`
- `music.Track`
- `music.VideoClip`
- `writing.Article`
- `writing.Book`
- `visual_art.Artwork` or separate `BD`/`Drawing` models if that reads cleaner
- `events.Event`
- `photos.Photo`, `PhotoStory`, `PhotoCollection`
- `sites.SiteSettings` or `pages.KentHomeSettings` for fixed homepage text

Deliverable:

- Domain schema exists and migrates cleanly.
- Admin can create/edit representative records manually.
- Models are still simple enough to change before bulk import.

## Phase 5: Pilot Import And Admin Iteration

Goal: import a small real subset before polishing admin forms, so model and admin decisions are based on actual Kent records.

Tasks:

- Build a minimal importer that can fetch and load a small subset:
  - a few media records
  - a few posts/articles
  - one album with tracks
  - one book/BD/drawing record
  - one event/date
- Convert a representative set of Payload Lexical rich text fields to HTML.
- Log all unknown Lexical node types instead of silently flattening them.
- Preserve original rich text JSON on imported records.
- Review imported records in Django admin and adjust model fields before full import.
- Register all models in admin.
- Apply `SiteScopedAdmin` everywhere site-owned data appears.
- Add useful list displays, filters, search fields, ordering, and fieldsets.
- Add inline models where they match editing workflows:
  - album tracks under albums
  - image variants under images
  - navigation links under site/settings if convenient
- Configure `django-prose-editor` consistently.
- Keep admin UX boring and predictable.

Deliverable:

- A small real Kent subset imports successfully.
- Unknown rich text node types are logged and reviewed.
- A client/user can edit Kent content without seeing unrelated site data.
- Superuser can manage all sites and migration troubleshooting fields.

## Phase 6: Payload Export And Transform Pipeline

Goal: export clean content from the live Payload API and transform it into Django-ready JSON.

Use the live public Payload API where possible:

- `https://www.kent-artiste.com/api/posts`
- `https://www.kent-artiste.com/api/albums`
- `https://www.kent-artiste.com/api/chansons`
- `https://www.kent-artiste.com/api/album-tracks`
- `https://www.kent-artiste.com/api/video-clips`
- `https://www.kent-artiste.com/api/bds`
- `https://www.kent-artiste.com/api/dessins`
- `https://www.kent-artiste.com/api/livres`
- `https://www.kent-artiste.com/api/dates`
- `https://www.kent-artiste.com/api/dates-cles`
- `https://www.kent-artiste.com/api/photos`
- `https://www.kent-artiste.com/api/photo-stories`
- `https://www.kent-artiste.com/api/photo-collections`
- `https://www.kent-artiste.com/api/mais-encore-items`
- `https://www.kent-artiste.com/api/media`
- globals such as `site_texts`, `a-propos`, `contact`, `mentions-legales`, `mais-encore`

Export command design:

- Create a Django management command or standalone script:
  - `python manage.py export_payload_snapshot`
  - or `python scripts/export_payload_snapshot.py`
- Save raw API responses under:
  - `data/payload/raw/{collection}.json`
  - `data/payload/raw/globals/{slug}.json`
- Paginate until all docs are fetched.
- Keep raw exports out of git if they include large or sensitive content.

Transform command design:

- Create `python manage.py import_payload_snapshot --site kent`.
- Read raw JSON snapshots.
- Convert Payload Lexical rich text to HTML.
- Preserve original Payload Lexical JSON until QA passes.
- Log unsupported/unknown Lexical nodes with enough context to fix or manually review them.
- Map Payload media IDs to Django `Image` rows.
- Upsert by `payload_id`.
- Import in dependency order:
  1. Site and site settings
  2. Media metadata
  3. People/artists/base lookup records
  4. Albums, books, visual works, photos, events, articles
  5. Relationship/through records such as tracks and appearances
  6. Navigation and redirects
  7. Download media files

Rich text migration:

- Convert Payload Lexical JSON to conservative HTML.
- Support:
  - paragraphs
  - headings
  - bold/italic/underline/strike
  - links
  - unordered/ordered lists
  - blockquotes
  - line breaks
- Do not silently flatten unsupported nodes.
- For unknown nodes:
  - log collection, document ID, field name, node type, and a short JSON excerpt
  - preserve original JSON in `payload_rich_text`
  - render a conservative text fallback only after logging
  - manually review the small set of misses before launch

Deliverable:

- Raw Payload snapshot can be generated repeatedly.
- Import can be rerun without creating duplicates.
- Django database contains usable Kent content.
- Import tests cover counts, idempotency, key relationships, and unknown rich text node reporting.

## Phase 7: Public Frontend Without HTMX

Goal: build the public site server-rendered first.

Start with static routing and templates:

- base layout
- header/navigation
- footer
- homepage
- about page
- music landing
- album detail
- writing/articles list and detail
- books page/detail
- visual art page/detail
- events/dates page
- contact page

Template approach:

- Use Django templates.
- Keep page structure hard-coded.
- Pull editable text from settings/domain models.
- Use template partials for repeated cards/lists.
- Render rich text safely from `django-prose-editor` fields.

CSS approach:

- Start simple.
- Either use plain CSS or add a lightweight build step only when necessary.
- Avoid creating a frontend app unless there is a real interactive need.

Deliverable:

- Public pages render from Django data.
- The site works with regular links and regular forms.
- SEO-critical pages are server-rendered.
- `sitemap.xml`, `robots.txt`, canonical URLs, and article feed work against real routes.

## Phase 8: Add HTMX Where It Helps

Goal: enhance small interactions after the baseline site works.

Install HTMX when there is an actual endpoint to improve, not at project start.

Good first HTMX use cases:

- newsletter signup response
- contact form response
- article search/filter
- "load more" lists
- media/gallery filtering

Implementation approach:

- Include HTMX script in the base template.
- Build normal Django views first.
- Return partial templates for HTMX requests.
- Keep every interaction functional without JavaScript where reasonable.

Deliverable:

- A few targeted interactions feel smoother.
- No separate Svelte/API frontend exists.

## Phase 9: Automated Tests, Validation, And Content QA

Goal: prove the Django site matches the existing site closely enough to switch.

Automated tests:

- Import snapshot tests:
  - collection counts match raw Payload exports
  - importer is idempotent
  - relationships resolve
  - media references resolve
  - unknown Lexical node logs fail the test unless explicitly allowlisted
- View smoke tests:
  - homepage
  - about page
  - article list/detail
  - music landing
  - album detail
  - books/visual art/events/contact pages
  - sitemap
  - robots
  - feed
- Admin smoke tests for core model changelists as superuser.

Manual/content checks:

- Count records per domain against Payload exports.
- Check missing media files.
- Check broken internal links.
- Check redirects from old URLs.
- Check representative pages visually.
- Verify rich text conversions.
- Verify accents and French typography, with locale configured from Phase 1.
- Verify dates/time zones.
- Verify media dimensions and file sizes.

Suggested scripts:

- `python manage.py audit_import --site kent`
- `python manage.py check_links --site kent`
- `python manage.py report_missing_media --site kent`

Deliverable:

- A written migration report with counts and known gaps.
- No silent import failures.
- Test suite catches import regressions before model/admin tweaks ship.

## Phase 10: Deployment

Goal: deploy a small, boring Django app.

Server shape:

- Gunicorn or Uvicorn behind Nginx.
- SQLite database on disk.
- Media files on disk.
- Nginx serves `/static/` and `/media/`.
- Systemd service for the Django app.

Backup policy:

- Enable SQLite WAL mode for production unless there is a specific reason not to.
- Daily SQLite backup using an online-safe method:
  - `sqlite3 db.sqlite3 ".backup 'backup.sqlite3'"`
  - or `VACUUM INTO 'backup.sqlite3'`
  - do not rely on raw file copies while the app may be writing
- Daily media folder backup.
- Offsite backup with restic, rclone, S3/R2, Backblaze, or similar.
- Test restore before switching DNS.

Deployment tasks:

- Configure production env.
- Run migrations.
- Run import.
- Run media download.
- Run `collectstatic`.
- Create admin user.
- Configure Nginx.
- Add HTTPS.
- Switch DNS when validated.

Deliverable:

- New Django site is live.
- Payload site remains available as rollback until confidence is high.

## Phase 11: Cleanup After Launch

Goal: remove migration scaffolding only after the site has run successfully.

Tasks:

- Keep raw Payload backup and exports archived.
- Remove or archive `payload_rich_text` fields only after automated and manual QA passes.
- Remove or hide `payload_id` fields from non-superuser admin screens.
- Add client docs for editing common content.
- Add a simple maintenance checklist.

Deliverable:

- The project is clean enough to reuse for the next small site.

## Open Questions

These decisions can wait, but they should be answered before implementation goes too far:

- Should the repo root stay at `unhook_sites/unhook_sites`, or should we flatten it so `manage.py` lives directly in `/Users/mrks/Code/kent/unhook_sites`? Recommendation: flatten now if the nested layout bothers us at all.
- Should `BDs`, `Dessins`, and books be separate Django models, or unified under a broader visual/writing model with categories?
- Which old PHP URLs need redirects?
- Do we need unpublished/draft Payload records? If yes, live public API is not enough and we should export from the local Payload app or database.
- Do newsletter/contact submissions need to be migrated, or can those start fresh?
