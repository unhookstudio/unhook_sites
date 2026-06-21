import json
from email.utils import formataddr
from random import choice
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db.models import F, Prefetch
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.html import escape
from django.views.decorators.http import require_http_methods, require_POST

from events.models import Event, KeyDate
from media_library.models import Image
from music.models import Album, Song, Track, VideoClip
from photos.models import Photo, PhotoCollection
from sites_core.models import SiteSettings
from visual_art.models import BD, Drawing
from writing.models import Article, Book
from .models import ContactSubmission, NewsletterSubscription


BREVO_CONTACTS_API_URL = "https://api.brevo.com/v3/contacts"


def _site(request):
    if request.site is None:
        raise Http404("Site not configured")
    return request.site


def home(request):
    site = _site(request)
    homepage_settings = (
        SiteSettings.objects.filter(site=site).select_related("homepage_hero_image").first()
    )
    latest_posts = _published(Article, site).select_related("featured_image")[:4]
    events = _published(Event, site).select_related("cover_image")[:3]
    albums = list(_published(Album, site).select_related("artist", "cover_image")[:100])
    featured_album = choice(albums) if albums else None
    return render(
        request,
        _template(site, "home.html"),
        {
            "homepage_settings": homepage_settings,
            "latest_posts": latest_posts,
            "events": events,
            "featured_album": featured_album,
        },
    )


def dates(request):
    site = _site(request)
    events = _published(Event, site).select_related("cover_image").order_by("date", "title")[:100]
    return render(request, _template(site, "dates.html"), {"events": events})


def a_propos(request):
    site = _site(request)
    key_dates = _published(KeyDate, site).order_by("date", "title")[:100]
    older_photo_items = _photo_collection_items(site, "a-propos-older")
    recent_photo_items = _photo_collection_items(site, "a-propos-recent")

    if not older_photo_items or not recent_photo_items:
        fallback_items = _photo_collection_items(site, "a-propos-droite")
        if not older_photo_items and fallback_items:
            older_photo_items = fallback_items[:1]
        if not recent_photo_items and len(fallback_items) > 1:
            recent_photo_items = fallback_items[1:2]

    return render(
        request,
        _template(site, "a_propos.html"),
        {
            "older_photo_items": older_photo_items,
            "recent_photo_items": recent_photo_items,
            "key_dates": key_dates,
        },
    )


@require_http_methods(["GET", "POST"])
def contact(request):
    site = _site(request)
    if request.method == "POST":
        return _handle_contact_submission(request, site)

    contact_image = Image.objects.filter(site=site, filename="Kent-flou.jpg").first()
    if contact_image is None:
        contact_photo = (
            _published(Photo, site)
            .select_related("image")
            .filter(title__icontains="Laurent Julliand", image__isnull=False)
            .first()
        )
        contact_image = contact_photo.image if contact_photo else None
    return render(
        request,
        _template(site, "contact.html"),
        {
            "contact_image": contact_image,
            "status": _contact_status(request),
        },
    )


def mentions_legales(request):
    site = _site(request)
    return render(request, _template(site, "mentions_legales.html"))


def mentions_legales_alias(request):
    return redirect("mentions_legales")


def musique(request):
    site = _site(request)
    albums = list(_published(Album, site).select_related("artist", "cover_image")[:100])
    kent_albums = [album for album in albums if _artist_name(album) == "kent"]
    official_albums = [
        album for album in kent_albums if album.category == Album.Category.COMMERCIAL
    ]
    intime_albums = [
        album for album in kent_albums if album.category in {"indie_collection", Album.Category.RARE}
    ]
    starshooter_albums = [
        album for album in albums if _artist_name(album) == "starshooter"
    ]
    video_clips = (
        _published(VideoClip, site)
        .select_related("thumbnail")
        .order_by(F("sort_order").asc(nulls_last=True), "-release_date", "title")[:100]
    )
    return render(
        request,
        _template(site, "musique.html"),
        {
            "official_albums": official_albums,
            "official_preview_albums": official_albums[:6],
            "official_hidden_albums": official_albums[6:],
            "intime_albums": intime_albums,
            "starshooter_albums": starshooter_albums,
            "video_clips": video_clips,
        },
    )


def album_detail(request, slug):
    site = _site(request)
    album = get_object_or_404(
        _published(Album, site).select_related("artist", "cover_image"),
        slug=slug,
    )
    tracks = (
        Track.objects.filter(album=album)
        .select_related("song")
        .order_by("disc_number", "track_number")
    )
    return render(request, _template(site, "album_detail.html"), {"album": album, "tracks": tracks})


def song_detail(request, slug):
    site = _site(request)
    song = get_object_or_404(_published(Song, site), slug=slug)
    tracks = (
        Track.objects.filter(song=song, album__site=site, album__is_published=True)
        .select_related("album", "album__cover_image")
        .order_by("album__release_date", "track_number")
    )
    return render(request, _template(site, "song_detail.html"), {"song": song, "tracks": tracks})


def livres(request):
    site = _site(request)
    books = list(_published(Book, site).select_related("cover_image").filter(show_on_books_page=True))
    sections = [
        ("Romans", [book for book in books if book.category == Book.Category.NOVELS]),
        (
            "Divers",
            [
                book
                for book in books
                if book.category in {Book.Category.MISC, Book.Category.OTHER}
            ],
        ),
        (
            "Livres illustrés",
            [
                book
                for book in books
                if book.category == Book.Category.ILLUSTRATED and _is_kent_credit(book.author)
            ],
        ),
        ("Livres jeunesse", [book for book in books if book.category == Book.Category.CHILDREN]),
    ]
    return render(request, _template(site, "livres.html"), {"sections": sections, "books": books})


def book_detail(request, slug):
    site = _site(request)
    book = get_object_or_404(
        _published(Book, site).select_related("cover_image").prefetch_related("additional_images"),
        slug=slug,
    )
    return render(request, _template(site, "book_detail.html"), {"book": book})


def dessins(request):
    site = _site(request)
    bds = list(_published(BD, site).select_related("cover_image"))
    drawings = list(
        _published(Drawing, site).prefetch_related(
            Prefetch("images"),
        )
    )
    illustrated_books = list(
        _published(Book, site)
        .select_related("cover_image")
        .filter(category=Book.Category.ILLUSTRATED, show_on_drawings_page=True)
    )
    return render(
        request,
        _template(site, "dessins.html"),
        {
            "adult_bds": [bd for bd in bds if bd.category == BD.Category.ADULT],
            "youth_bds": [bd for bd in bds if bd.category == BD.Category.YOUTH],
            "drawings": drawings,
            "illustrated_books": illustrated_books,
        },
    )


def dessin_detail(request, slug):
    site = _site(request)
    bd = (
        _published(BD, site)
        .select_related("cover_image")
        .prefetch_related("additional_images")
        .filter(slug=slug)
        .first()
    )
    if bd is not None:
        return render(request, _template(site, "bd_detail.html"), {"bd": bd})

    drawing = get_object_or_404(
        _published(Drawing, site).prefetch_related("images"),
        slug=slug,
    )
    return render(request, _template(site, "drawing_detail.html"), {"drawing": drawing})


def posts(request):
    site = _site(request)
    articles = _published(Article, site).select_related("featured_image")[:100]
    return render(request, _template(site, "posts.html"), {"articles": articles})


def post_detail(request, slug):
    site = _site(request)
    article = get_object_or_404(
        _published(Article, site).select_related("featured_image"),
        slug=slug,
    )
    return render(request, _template(site, "post_detail.html"), {"article": article})


@require_POST
def newsletter_signup(request):
    site = _site(request)
    email = request.POST.get("email", "").strip().lower()
    company = request.POST.get("company", "").strip()

    if company:
        return redirect("/?newsletter=success#newsletter")

    if not _is_valid_email(email):
        return redirect("/?newsletter=error#newsletter")

    subscription, _ = NewsletterSubscription.objects.update_or_create(
        site=site,
        email=email,
        defaults={
            "source": "homepage",
            "status": NewsletterSubscription.Status.SUBSCRIBED,
            "last_error": "",
        },
    )

    try:
        _sync_brevo_newsletter_contact(email)
    except NewsletterSyncError as exc:
        subscription.status = NewsletterSubscription.Status.ERROR
        subscription.last_error = str(exc)
        subscription.save(update_fields=["status", "last_error", "updated_at"])
        return redirect("/?newsletter=error#newsletter")

    subscription.status = NewsletterSubscription.Status.SUBSCRIBED
    subscription.last_synced_at = timezone.now()
    subscription.last_error = ""
    subscription.save(update_fields=["status", "last_synced_at", "last_error", "updated_at"])
    return redirect("/?newsletter=success#newsletter")


def _handle_contact_submission(request, site):
    email = request.POST.get("email", "").strip().lower()
    message = request.POST.get("message", "").strip()
    company = request.POST.get("company", "").strip()

    if company:
        return redirect("/contact?sent=1")

    if not _is_valid_contact_message(email, message):
        return redirect("/contact?error=1")

    submission = ContactSubmission.objects.create(site=site, email=email, message=message)
    _send_contact_notification(submission)
    return redirect("/contact?sent=1")


def _is_valid_contact_message(email: str, message: str) -> bool:
    if not _is_valid_email(email):
        return False
    return 10 <= len(message) <= 5000


def _is_valid_email(email: str) -> bool:
    try:
        validate_email(email)
    except ValidationError:
        return False
    return True


def _send_contact_notification(submission: ContactSubmission) -> None:
    recipients = [email.strip() for email in settings.CONTACT_NOTIFICATION_TO if email.strip()]
    if not recipients:
        submission.notification_error = "CONTACT_NOTIFICATION_TO is not configured."
        submission.save(update_fields=["notification_error", "updated_at"])
        return

    from_email = _contact_notification_from_email()
    text_body = (
        "A new message was submitted on the website contact form.\n\n"
        f"From: {submission.email}\n\n"
        f"Message:\n{submission.message}"
    )
    html_body = (
        "<p>A new message was submitted on the website contact form.</p>"
        f"<p><strong>From:</strong> {escape(submission.email)}</p>"
        "<p><strong>Message:</strong></p>"
        f"<p>{escape(submission.message).replace(chr(10), '<br>')}</p>"
    )
    message = EmailMultiAlternatives(
        subject=f"New contact form submission from {submission.email}",
        body=text_body,
        from_email=from_email,
        to=recipients,
        reply_to=[submission.email],
    )
    message.attach_alternative(html_body, "text/html")

    try:
        message.send(fail_silently=False)
    except Exception as exc:
        submission.notification_error = str(exc)
        submission.save(update_fields=["notification_error", "updated_at"])
        return

    submission.notification_sent_at = timezone.now()
    submission.notification_error = ""
    submission.save(update_fields=["notification_sent_at", "notification_error", "updated_at"])


def _contact_notification_from_email() -> str:
    email = settings.CONTACT_NOTIFICATION_FROM_EMAIL.strip() or settings.EMAIL_HOST_USER
    name = settings.CONTACT_NOTIFICATION_FROM_NAME.strip()
    if name and email:
        return formataddr((name, email))
    return email


class NewsletterSyncError(RuntimeError):
    pass


def _sync_brevo_newsletter_contact(email: str) -> None:
    api_key = settings.BREVO_API_KEY.strip()
    try:
        list_id = int(str(settings.BREVO_LIST_ID).strip())
    except ValueError as exc:
        raise NewsletterSyncError("Brevo list id is not configured.") from exc

    if not api_key or list_id <= 0:
        raise NewsletterSyncError("Brevo API credentials are not configured.")

    payload = json.dumps(
        {
            "email": email,
            "listIds": [list_id],
            "updateEnabled": True,
            "emailBlacklisted": False,
        }
    ).encode("utf-8")
    request = Request(
        BREVO_CONTACTS_API_URL,
        data=payload,
        method="POST",
        headers={
            "accept": "application/json",
            "api-key": api_key,
            "content-type": "application/json",
        },
    )

    try:
        with urlopen(request, timeout=10):
            return
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise NewsletterSyncError(f"Brevo returned HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise NewsletterSyncError(f"Brevo request failed: {exc.reason}") from exc


def _contact_status(request) -> str:
    if request.GET.get("sent") == "1":
        return "sent"
    if request.GET.get("error") == "1":
        return "error"
    return ""


def _published(model, site):
    return model.objects.filter(site=site, is_published=True)


def _photo_collection_items(site, slug: str):
    collection = (
        _published(PhotoCollection, site)
        .filter(slug=slug)
        .prefetch_related("items__photo__image")
        .first()
    )
    if collection is None:
        return []
    return [item for item in collection.items.all() if item.photo.is_published and item.photo.image_id]


def _template(site, name: str) -> str:
    return f"{site.slug}_site/{name}"


def _artist_name(album: Album) -> str:
    return str(album.artist or "").lower()


def _is_kent_credit(value: str) -> bool:
    return value.strip().casefold() == "kent"
