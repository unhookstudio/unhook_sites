from datetime import date, datetime

from django.core.files.base import ContentFile
from django.urls import reverse
from django.utils import timezone

from media_library.models import Image
from music.models import Album, Artist, Song, Track, VideoClip
from events.models import Event, KeyDate
from photos.models import Photo, PhotoCollection, PhotoCollectionItem
from public_site.models import ContactSubmission, NewsletterSubscription
from sites_core.models import Site, SiteSettings, TextSnippet
from tests.test_media_library import png_bytes
from visual_art.models import BD, Drawing
from writing.models import Article, Book


def test_public_views_resolve_templates_from_site_slug():
    from public_site.views import _template

    site = Site(slug="kent")

    assert _template(site, "home.html") == "kent_site/home.html"


def test_public_home_uses_site_from_request_host(client, db, settings):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    kent = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    other = Site.objects.create(name="Other", slug="other", domain="example.com")
    Article.objects.create(site=kent, title="Kent article", slug="kent-article", is_published=True)
    Article.objects.create(site=other, title="Other article", slug="other-article", is_published=True)

    response = client.get(reverse("home"), HTTP_HOST="kent-artiste.com")

    assert response.status_code == 200
    assert "Kent article" in response.text
    assert "Other article" not in response.text


def test_public_home_falls_back_to_kent_for_localhost(client, db):
    Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")

    response = client.get(reverse("home"), HTTP_HOST="localhost")

    assert response.status_code == 200


def test_public_base_loads_kent_scoped_stylesheet(client, db, settings):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")

    response = client.get(reverse("home"), HTTP_HOST="kent-artiste.com")

    assert response.status_code == 200
    assert 'class="site site--kent"' in response.text
    assert "/static/kent/css/site.css" in response.text


def test_public_base_loads_kent_favicon_fallbacks(client, db, settings):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")

    response = client.get(reverse("home"), HTTP_HOST="kent-artiste.com")

    assert response.status_code == 200
    assert "/static/kent/favicons/favicon.svg" in response.text
    assert "/static/kent/favicons/favicon.ico" in response.text


def test_public_footer_renders_site_social_links(client, db, settings):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    SiteSettings.objects.create(
        site=site,
        facebook_url="https://www.facebook.com/kentartiste",
        instagram_url="https://www.instagram.com/kent_artiste",
        bandcamp_url="https://kent-artiste.bandcamp.com",
        youtube_url="https://www.youtube.com/user/ChaineOfficielleKENT",
    )

    response = client.get(reverse("home"), HTTP_HOST="kent-artiste.com")

    assert response.status_code == 200
    assert "site-footer__social" in response.text
    assert "https://www.facebook.com/kentartiste" in response.text
    assert "https://www.instagram.com/kent_artiste" in response.text
    assert "https://kent-artiste.bandcamp.com" in response.text
    assert "https://www.youtube.com/user/ChaineOfficielleKENT" in response.text
    assert "site-footer__social-icon--bandcamp" in response.text


def test_editorial_text_snippets_override_public_copy(client, db, settings):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    TextSnippet.objects.create(
        site=site,
        key="home_card_music_text",
        label="Accueil - carte Musique - texte",
        text="Texte musique éditable.",
    )
    TextSnippet.objects.create(
        site=site,
        key="musique_quote_text",
        label="Musique - citation",
        text="Citation musique éditable.",
    )
    TextSnippet.objects.create(
        site=site,
        key="musique_quote_credit",
        label="Musique - auteur de la citation",
        text="Auteur éditable",
    )

    home_response = client.get(reverse("home"), HTTP_HOST="kent-artiste.com")
    musique_response = client.get(reverse("musique"), HTTP_HOST="kent-artiste.com")

    assert home_response.status_code == 200
    assert "Texte musique éditable." in home_response.text
    assert "Juste quelqu&#x27;un de bien" not in home_response.text
    assert musique_response.status_code == 200
    assert "Citation musique éditable." in musique_response.text
    assert "Auteur éditable" in musique_response.text


def test_site_settings_override_contact_and_newsletter_copy(client, db, settings):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    SiteSettings.objects.create(
        site=site,
        contact_title="Titre contact éditable",
        contact_intro_text="Première ligne\nDeuxième ligne",
        newsletter_text="Texte newsletter éditable.",
    )

    contact_response = client.get(reverse("contact"), HTTP_HOST="kent-artiste.com")
    home_response = client.get(reverse("home"), HTTP_HOST="kent-artiste.com")

    assert contact_response.status_code == 200
    assert "Titre contact éditable" in contact_response.text
    assert "Première ligne<br>Deuxième ligne" in contact_response.text
    assert home_response.status_code == 200
    assert "Texte newsletter éditable." in home_response.text


def test_home_renders_news_cards_like_original_layout(client, db, settings):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    Article.objects.create(
        site=site,
        title="Journal entry",
        slug="journal-entry",
        category=Article.Category.NEWS,
        content_plain="A readable excerpt for the news card.",
        is_published=True,
    )

    response = client.get(reverse("home"), HTTP_HOST="kent-artiste.com")

    assert response.status_code == 200
    assert 'class="news-card"' in response.text
    assert "au_fil_derniers.svg" in response.text
    assert "Actualités" in response.text
    assert "News" not in response.text
    assert "A readable excerpt for the news card." in response.text


def test_home_renders_actualites_section_with_image_left_layout(client, db, settings):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    Event.objects.create(site=site, title="Concert", slug="concert", is_published=True)

    response = client.get(reverse("home"), HTTP_HOST="kent-artiste.com")

    assert response.status_code == 200
    assert "home-dates__grid" in response.text
    assert "home-dates__image" in response.text
    assert "home-date-card" in response.text
    assert "line_horizontal_squiggly.svg" in response.text
    assert "section-title-mask section-title--dates" in response.text
    assert 'href="/dates">Actualités</a>' in response.text


def test_base_hides_actualites_nav_without_published_events(client, db, settings):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")

    response = client.get(reverse("home"), HTTP_HOST="kent-artiste.com")

    assert response.status_code == 200
    assert 'href="/dates">Actualités</a>' not in response.text


def test_dates_page_lists_published_events(client, db, settings):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    Event.objects.create(
        site=site,
        title="Published date",
        slug="published-date",
        date=timezone.make_aware(datetime(2026, 6, 1, 20, 0)),
        description_html="<p>On stage.</p>",
        is_published=True,
    )
    Event.objects.create(
        site=site,
        title="Draft date",
        slug="draft-date",
        is_published=False,
    )

    response = client.get(reverse("dates"), HTTP_HOST="kent-artiste.com")

    assert response.status_code == 200
    assert "section-title--dates" in response.text
    assert "date-card" in response.text
    assert "Published date" in response.text
    assert "On stage." in response.text
    assert "Draft date" not in response.text


def test_contact_page_renders_live_content_and_photo(client, db, settings, tmp_path):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    settings.MEDIA_ROOT = tmp_path
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    image = Image.objects.create(site=site, title="Contact photo")
    image.original.save("contact.png", ContentFile(png_bytes()), save=True)
    Photo.objects.create(
        site=site,
        title="Kent par Laurent Julliand",
        slug="kent-par-laurent-julliand",
        image=image,
        is_published=True,
    )

    response = client.get(reverse("contact"), HTTP_HOST="kent-artiste.com")

    assert response.status_code == 200
    assert "Kent est à l&#x27;écoute" in response.text
    assert "Flavie Rodriguez" in response.text
    assert "Label At(h)ome" in response.text
    assert "Editions Thoobett" in response.text
    assert "/media/sites/kent/images/originals/contact.png" in response.text
    assert 'name="company"' in response.text


def test_contact_success_replaces_form_with_inline_message(client, db, settings):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")

    response = client.get("/contact?sent=1", HTTP_HOST="kent-artiste.com")

    assert response.status_code == 200
    assert "Message envoyé" in response.text
    assert "Nous vous répondrons dès que possible" in response.text
    assert 'class="contact-form"' not in response.text
    assert "Envoyer un autre message" not in response.text


def test_contact_error_keeps_form_visible(client, db, settings):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")

    response = client.get("/contact?error=1", HTTP_HOST="kent-artiste.com")

    assert response.status_code == 200
    assert "Envoi impossible" in response.text
    assert 'class="contact-form"' in response.text
    assert 'name="message"' in response.text


def test_contact_post_stores_submission_sends_email_and_redirects(
    client, db, settings, mailoutbox
):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    settings.CONTACT_NOTIFICATION_TO = ["flavie@example.com"]
    settings.CONTACT_NOTIFICATION_FROM_EMAIL = "noreply@example.com"
    settings.CONTACT_NOTIFICATION_FROM_NAME = "Kent artiste"
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")

    response = client.post(
        reverse("contact"),
        {"email": "reader@example.com", "message": "Bonjour Kent, bravo pour le site."},
        HTTP_HOST="kent-artiste.com",
    )

    assert response.status_code == 302
    assert response["Location"] == "/contact?sent=1"
    submission = ContactSubmission.objects.get()
    assert submission.site == site
    assert submission.email == "reader@example.com"
    assert "Bonjour Kent" in submission.message
    assert submission.notification_sent_at is not None
    assert submission.notification_error == ""
    assert len(mailoutbox) == 1
    message = mailoutbox[0]
    assert message.to == ["flavie@example.com"]
    assert message.reply_to == ["reader@example.com"]
    assert message.from_email == "Kent artiste <noreply@example.com>"
    assert "reader@example.com" in message.body
    assert "Bonjour Kent" in message.body


def test_contact_post_keeps_submission_if_notification_fails(
    client, db, settings, monkeypatch
):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    settings.CONTACT_NOTIFICATION_TO = ["flavie@example.com"]
    Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")

    def broken_send(self, fail_silently=False):
        raise RuntimeError("smtp unavailable")

    monkeypatch.setattr("public_site.views.EmailMultiAlternatives.send", broken_send)

    response = client.post(
        reverse("contact"),
        {"email": "reader@example.com", "message": "Bonjour Kent, bravo pour le site."},
        HTTP_HOST="kent-artiste.com",
    )

    assert response.status_code == 302
    assert response["Location"] == "/contact?sent=1"
    submission = ContactSubmission.objects.get()
    assert submission.notification_sent_at is None
    assert submission.notification_error == "smtp unavailable"


def test_contact_post_records_missing_notification_recipient(client, db, settings):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    settings.CONTACT_NOTIFICATION_TO = []
    Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")

    response = client.post(
        reverse("contact"),
        {"email": "reader@example.com", "message": "Bonjour Kent, bravo pour le site."},
        HTTP_HOST="kent-artiste.com",
    )

    assert response.status_code == 302
    assert response["Location"] == "/contact?sent=1"
    submission = ContactSubmission.objects.get()
    assert submission.notification_sent_at is None
    assert submission.notification_error == "CONTACT_NOTIFICATION_TO is not configured."


def test_contact_post_rejects_invalid_message(client, db, settings):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")

    response = client.post(
        reverse("contact"),
        {"email": "not-an-email", "message": "short"},
        HTTP_HOST="kent-artiste.com",
    )

    assert response.status_code == 302
    assert response["Location"] == "/contact?error=1"
    assert ContactSubmission.objects.count() == 0


def test_mentions_legales_renders_legal_content_and_alias_redirects(client, db, settings):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")

    response = client.get(reverse("mentions_legales"), HTTP_HOST="kent-artiste.com")
    alias_response = client.get(reverse("mentions_legales_alias"), HTTP_HOST="kent-artiste.com")

    assert response.status_code == 200
    assert "Mentions Légales" in response.text
    assert "Thoobett Éditions" in response.text
    assert "Unhook Studio" in response.text
    assert "Hetzner Online GmbH" in response.text
    assert "91710 Gunzenhausen" in response.text
    assert alias_response.status_code == 302
    assert alias_response["Location"] == "/mentions-legales"


def test_a_propos_renders_random_photo_pools_stories_and_key_dates(
    client, db, settings, tmp_path
):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    settings.MEDIA_ROOT = tmp_path
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    first_image = Image.objects.create(site=site, title="First about photo")
    second_image = Image.objects.create(site=site, title="Second about photo")
    first_image.original.save("about-1.png", ContentFile(png_bytes()), save=True)
    second_image.original.save("about-2.png", ContentFile(png_bytes()), save=True)
    first_photo = Photo.objects.create(
        site=site,
        title="First about photo",
        slug="first-about-photo",
        photographer="First Photographer",
        description_html="<p>Older story.</p>",
        image=first_image,
        is_published=True,
    )
    second_photo = Photo.objects.create(
        site=site,
        title="Second about photo",
        slug="second-about-photo",
        photographer="Second Photographer",
        description_html="<p>Recent story.</p>",
        image=second_image,
        is_published=True,
    )
    older_collection = PhotoCollection.objects.create(
        site=site,
        title="A propos older",
        slug="a-propos-older",
        is_published=True,
    )
    recent_collection = PhotoCollection.objects.create(
        site=site,
        title="A propos recent",
        slug="a-propos-recent",
        is_published=True,
    )
    PhotoCollectionItem.objects.create(
        collection=older_collection,
        photo=first_photo,
        caption="Older caption.",
        order=1,
    )
    PhotoCollectionItem.objects.create(
        collection=recent_collection,
        photo=second_photo,
        caption="Recent caption.",
        order=1,
    )
    KeyDate.objects.create(
        site=site,
        title="Premier album",
        slug="premier-album",
        date=timezone.make_aware(datetime(1978, 1, 1, 12, 0)),
        description_html="<p>Starshooter.</p>",
        is_published=True,
    )

    response = client.get(reverse("a_propos"), HTTP_HOST="kent-artiste.com")

    assert response.status_code == 200
    assert "À propos" in response.text
    assert "quote--about" in response.text
    assert "Difficile de trouver artiste plus accompli que Kent" in response.text
    assert "Olivier Nuc, Le Figaro" in response.text
    assert "Une de ses chansons s'intitule" in response.text
    assert "Kent entamera sa carrière solo dès 1983" in response.text
    assert "about-photo-rail" in response.text
    assert 'data-about-photo-pool="older"' in response.text
    assert 'data-about-photo-pool="recent"' in response.text
    assert "data-about-story-trigger" in response.text
    assert "data-about-story-modal" in response.text
    assert "lire l'histoire -&gt;" in response.text
    assert "Older story." in response.text
    assert "Recent story." in response.text
    assert "/media/sites/kent/images/originals/about-1.png" in response.text
    assert "/media/sites/kent/images/originals/about-2.png" in response.text
    assert "about-photo-rail__credit" in response.text
    assert "Photo : First Photographer" in response.text
    assert "Dates clés" in response.text
    assert "about-timeline__item--left" in response.text
    assert "Premier album" in response.text
    assert "Starshooter." in response.text


def test_home_does_not_render_hero_without_site_setting_checkbox(client, db, settings):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    SiteSettings.objects.create(site=site, show_homepage_hero=False)

    response = client.get(reverse("home"), HTTP_HOST="kent-artiste.com")

    assert response.status_code == 200
    assert '<section class="home-hero"' not in response.text


def test_home_renders_hero_when_site_setting_checkbox_is_enabled(client, db, settings):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    SiteSettings.objects.create(
        site=site,
        show_homepage_hero=True,
        homepage_hero_text="Custom hero",
        homepage_hero_button_text="Découvrir",
        homepage_hero_button_url="/a-propos",
    )

    response = client.get(reverse("home"), HTTP_HOST="kent-artiste.com")

    assert response.status_code == 200
    assert "home-hero" in response.text
    assert "kent_cut.webp" in response.text
    assert "Custom hero" in response.text
    assert "Découvrir" in response.text


def test_home_renders_newsletter_and_quick_links(client, db, settings):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")

    response = client.get(reverse("home"), HTTP_HOST="kent-artiste.com")

    assert response.status_code == 200
    assert 'id="newsletter"' in response.text
    assert "actualite.svg" in response.text
    assert "kent_gauche.jpg" in response.text
    assert "Oui, je veux la newslettre" in response.text
    assert "line_horizontal_straight.svg" in response.text
    assert "quick-link-card--music" in response.text
    assert "quick-link-card--drawings" in response.text
    assert "quick-link-card--books" in response.text


def test_newsletter_signup_stores_subscription_and_syncs_brevo(
    client, db, settings, monkeypatch
):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    synced_emails = []

    def sync(email):
        synced_emails.append(email)

    monkeypatch.setattr("public_site.views._sync_brevo_newsletter_contact", sync)

    response = client.post(
        reverse("newsletter_signup"),
        {"email": " Reader@Example.COM "},
        HTTP_HOST="kent-artiste.com",
    )

    assert response.status_code == 302
    assert response["Location"] == "/?newsletter=success#newsletter"
    subscription = NewsletterSubscription.objects.get()
    assert subscription.email == "reader@example.com"
    assert subscription.status == NewsletterSubscription.Status.SUBSCRIBED
    assert subscription.source == "homepage"
    assert subscription.last_synced_at is not None
    assert subscription.last_error == ""
    assert synced_emails == ["reader@example.com"]


def test_newsletter_signup_rejects_invalid_email(client, db, settings, monkeypatch):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    monkeypatch.setattr(
        "public_site.views._sync_brevo_newsletter_contact",
        lambda email: (_ for _ in ()).throw(AssertionError("Brevo should not be called")),
    )

    response = client.post(
        reverse("newsletter_signup"),
        {"email": "not-an-email"},
        HTTP_HOST="kent-artiste.com",
    )

    assert response.status_code == 302
    assert response["Location"] == "/?newsletter=error#newsletter"
    assert NewsletterSubscription.objects.count() == 0


def test_newsletter_signup_honeypot_pretends_success(client, db, settings, monkeypatch):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    monkeypatch.setattr(
        "public_site.views._sync_brevo_newsletter_contact",
        lambda email: (_ for _ in ()).throw(AssertionError("Brevo should not be called")),
    )

    response = client.post(
        reverse("newsletter_signup"),
        {"email": "reader@example.com", "company": "Spam Ltd"},
        HTTP_HOST="kent-artiste.com",
    )

    assert response.status_code == 302
    assert response["Location"] == "/?newsletter=success#newsletter"
    assert NewsletterSubscription.objects.count() == 0


def test_musique_lists_only_published_site_albums(client, db, settings):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    artist = Artist.objects.create(site=site, name="Kent", slug="kent")
    Album.objects.create(
        site=site,
        artist=artist,
        title="Published album",
        slug="published-album",
        is_published=True,
    )
    Album.objects.create(
        site=site,
        artist=artist,
        title="Draft album",
        slug="draft-album",
        is_published=False,
    )

    response = client.get(reverse("musique"), HTTP_HOST="kent-artiste.com")

    assert response.status_code == 200
    assert "Published album" in response.text
    assert "Draft album" not in response.text


def test_musique_shows_album_preview_disclosure_and_video_cards(client, db, settings):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    artist = Artist.objects.create(site=site, name="Kent", slug="kent")
    for index in range(8):
        Album.objects.create(
            site=site,
            artist=artist,
            title=f"Album {index}",
            slug=f"album-{index}",
            is_published=True,
            category=Album.Category.COMMERCIAL,
        )
    VideoClip.objects.create(
        site=site,
        title="Clip",
        slug="clip",
        video_id="abc123",
        is_published=True,
    )

    response = client.get(reverse("musique"), HTTP_HOST="kent-artiste.com")

    assert response.status_code == 200
    assert "quote--musique" in response.text
    assert "music-disclosure" in response.text
    assert "data-music-albums-expand" in response.text
    assert "data-music-albums-collapse" in response.text
    assert "Voir tout (8 albums)" in response.text
    assert "Voir moins" in response.text
    assert 'class="music-album-grid music-album-grid--continued" hidden' in response.text
    assert "music-video-card" in response.text
    assert "data-video-modal-trigger" in response.text
    assert 'data-video-id="abc123"' in response.text
    assert "data-video-modal" in response.text
    assert "https://img.youtube.com/vi/abc123/hqdefault.jpg" in response.text
    assert "music-video-card__play" in response.text


def test_musique_orders_videos_by_sort_order_then_current_fallback(client, db, settings):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    VideoClip.objects.create(
        site=site,
        title="Newest unordered",
        slug="newest-unordered",
        video_id="newest",
        release_date=date(2024, 1, 1),
        is_published=True,
    )
    VideoClip.objects.create(
        site=site,
        title="Older unordered",
        slug="older-unordered",
        video_id="older",
        release_date=date(2020, 1, 1),
        is_published=True,
    )
    VideoClip.objects.create(
        site=site,
        title="Ordered clip",
        slug="ordered-clip",
        video_id="ordered",
        release_date=date(2010, 1, 1),
        sort_order=1,
        is_published=True,
    )

    response = client.get(reverse("musique"), HTTP_HOST="kent-artiste.com")

    assert response.status_code == 200
    assert response.text.index("Ordered clip") < response.text.index("Newest unordered")
    assert response.text.index("Newest unordered") < response.text.index("Older unordered")


def test_home_renders_featured_album_panel(client, db, settings):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    artist = Artist.objects.create(site=site, name="Kent", slug="kent")
    Album.objects.create(
        site=site,
        artist=artist,
        title="Featured album",
        slug="featured-album",
        is_published=True,
        label="Label",
    )

    response = client.get(reverse("home"), HTTP_HOST="kent-artiste.com")

    assert response.status_code == 200
    assert "featured-album" in response.text
    assert "Voir la discographie" in response.text
    assert "Featured album" in response.text
    assert "section-title-mask section-title--album" in response.text


def test_album_detail_shows_tracks(client, db, settings):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    artist = Artist.objects.create(site=site, name="Kent", slug="kent")
    album = Album.objects.create(
        site=site,
        artist=artist,
        title="Album",
        slug="album",
        is_published=True,
    )
    song = Song.objects.create(site=site, title="Song", slug="song", is_published=True)
    Track.objects.create(album=album, song=song, track_number=1)

    response = client.get(reverse("album_detail", args=["album"]), HTTP_HOST="kent-artiste.com")

    assert response.status_code == 200
    assert "Album" in response.text
    assert "Song" in response.text


def test_song_detail_preserves_lyrics_breaks_and_uses_compact_album_panel(client, db, settings):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    artist = Artist.objects.create(site=site, name="Kent", slug="kent")
    album = Album.objects.create(
        site=site,
        artist=artist,
        title="Album",
        slug="album",
        is_published=True,
    )
    song = Song.objects.create(
        site=site,
        title="Song",
        slug="song",
        is_published=True,
        lyrics_html="<p>Line one\nLine two</p>",
    )
    Track.objects.create(album=album, song=song, track_number=1)

    response = client.get(reverse("song_detail", args=["song"]), HTTP_HOST="kent-artiste.com")

    assert response.status_code == 200
    assert "song-lyrics" in response.text
    assert "Line one\nLine two" in response.text
    assert "song-albums-panel" in response.text
    assert "album-appearance" in response.text


def test_livres_uses_book_page_placement_flag(client, db, settings):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    Book.objects.create(
        site=site,
        title="Visible book",
        slug="visible-book",
        short_description_html="<p>Une chanson vue de l&#x27;intérieur.</p>",
        is_published=True,
        show_on_books_page=True,
    )
    Book.objects.create(
        site=site,
        title="Drawings only book",
        slug="drawings-only-book",
        is_published=True,
        show_on_books_page=False,
        show_on_drawings_page=True,
    )
    Book.objects.create(
        site=site,
        title="Misc book",
        slug="misc-book",
        category=Book.Category.MISC,
        is_published=True,
        show_on_books_page=True,
    )
    Book.objects.create(
        site=site,
        title="Kent illustrated book",
        slug="kent-illustrated-book",
        author="Kent",
        category=Book.Category.ILLUSTRATED,
        is_published=True,
        show_on_books_page=True,
        show_on_drawings_page=True,
    )
    Book.objects.create(
        site=site,
        title="Other illustrated book",
        slug="other-illustrated-book",
        author="Other Author",
        category=Book.Category.ILLUSTRATED,
        is_published=True,
        show_on_books_page=True,
        show_on_drawings_page=True,
    )

    response = client.get(reverse("livres"), HTTP_HOST="kent-artiste.com")

    assert response.status_code == 200
    assert "quote--livres" in response.text
    assert "Divers" in response.text
    assert "Misc book" in response.text
    assert "Visible book" in response.text
    assert "Kent illustrated book" in response.text
    assert "Other illustrated book" not in response.text
    assert "l&#x27;intérieur" in response.text
    assert "l&amp;#x27;intérieur" not in response.text
    assert "Drawings only book" not in response.text

    drawings_response = client.get(reverse("dessins"), HTTP_HOST="kent-artiste.com")

    assert drawings_response.status_code == 200
    assert "Kent illustrated book" in drawings_response.text
    assert "Other illustrated book" in drawings_response.text


def test_dessins_decodes_list_descriptions_and_renders_drawing_grid(
    client, db, settings, tmp_path
):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    settings.MEDIA_ROOT = tmp_path
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    BD.objects.create(
        site=site,
        title="BD",
        slug="bd",
        description_html="<p>L&#x27;encre et l&#x27;acrylique.</p>",
        is_published=True,
    )
    first_image = Image.objects.create(site=site, title="First drawing image")
    second_image = Image.objects.create(site=site, title="Second drawing image")
    first_image.original.save("drawing-1.png", ContentFile(png_bytes()), save=True)
    second_image.original.save("drawing-2.png", ContentFile(png_bytes()), save=True)
    drawing = Drawing.objects.create(
        site=site,
        title="Drawing",
        slug="drawing",
        description_html="<p>L&#x27;atelier à l&#x27;encre.</p>",
        is_published=True,
    )
    drawing.images.add(first_image, second_image)

    response = client.get(reverse("dessins"), HTTP_HOST="kent-artiste.com")

    assert response.status_code == 200
    assert "quote--dessins" in response.text
    assert "drawing-grid" in response.text
    assert "drawing-card--wide" in response.text
    assert "drawing-card__description" in response.text
    assert "/media/sites/kent/images/originals/drawing-1.png" in response.text
    assert "/media/sites/kent/images/originals/drawing-2.png" in response.text
    assert "L&#x27;encre et l&#x27;acrylique." in response.text
    assert "L&#x27;atelier à l&#x27;encre." in response.text
    assert "L&amp;#x27;encre" not in response.text
    assert "L&amp;#x27;atelier" not in response.text


def test_bd_detail_renders_dessins_back_link_and_gallery(client, db, settings, tmp_path):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    settings.MEDIA_ROOT = tmp_path
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    cover = Image.objects.create(site=site, title="Cover")
    first_gallery_image = Image.objects.create(site=site, title="First gallery image")
    second_gallery_image = Image.objects.create(site=site, title="Second gallery image")
    cover.original.save("cover.png", ContentFile(png_bytes()), save=True)
    first_gallery_image.original.save("gallery-1.png", ContentFile(png_bytes()), save=True)
    second_gallery_image.original.save("gallery-2.png", ContentFile(png_bytes()), save=True)
    bd = BD.objects.create(
        site=site,
        title="BD",
        slug="bd",
        cover_image=cover,
        is_published=True,
    )
    bd.additional_images.add(first_gallery_image, second_gallery_image)

    response = client.get(reverse("dessin_detail", args=["bd"]), HTTP_HOST="kent-artiste.com")

    assert response.status_code == 200
    assert "back-link--dessins" in response.text
    assert "Galerie" in response.text
    assert "detail-gallery" in response.text
    assert "/media/sites/kent/images/originals/gallery-1.png" in response.text
    assert "/media/sites/kent/images/originals/gallery-2.png" in response.text


def test_post_detail_404s_for_drafts(client, db, settings):
    settings.ALLOWED_HOSTS = ["kent-artiste.com"]
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    Article.objects.create(site=site, title="Draft", slug="draft", is_published=False)

    response = client.get(reverse("post_detail", args=["draft"]), HTTP_HOST="kent-artiste.com")

    assert response.status_code == 404
