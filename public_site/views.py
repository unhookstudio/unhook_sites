from random import choice

from django.http import Http404
from django.db.models import F, Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from events.models import Event
from music.models import Album, Song, Track, VideoClip
from sites_core.models import SiteSettings
from visual_art.models import BD, Drawing
from writing.models import Article, Book


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
    return redirect("/?newsletter=success#newsletter")


def _published(model, site):
    return model.objects.filter(site=site, is_published=True)


def _template(site, name: str) -> str:
    return f"{site.slug}_site/{name}"


def _artist_name(album: Album) -> str:
    return str(album.artist or "").lower()


def _is_kent_credit(value: str) -> bool:
    return value.strip().casefold() == "kent"
