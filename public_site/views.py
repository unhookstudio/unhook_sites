from random import choice

from django.http import Http404
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, render

from events.models import Event
from music.models import Album, Song, Track, VideoClip
from visual_art.models import BD, Drawing
from writing.models import Article, Book


def _site(request):
    if request.site is None:
        raise Http404("Site not configured")
    return request.site


def home(request):
    site = _site(request)
    latest_posts = _published(Article, site).select_related("featured_image")[:4]
    events = _published(Event, site).select_related("cover_image")[:3]
    albums = list(_published(Album, site).select_related("artist", "cover_image")[:100])
    featured_album = choice(albums) if albums else None
    return render(
        request,
        "public_site/home.html",
        {
            "latest_posts": latest_posts,
            "events": events,
            "featured_album": featured_album,
        },
    )


def musique(request):
    site = _site(request)
    albums = list(_published(Album, site).select_related("artist", "cover_image")[:100])
    kent_albums = [album for album in albums if str(album.artist or "").lower() == "kent"]
    starshooter_albums = [
        album for album in albums if str(album.artist or "").lower() == "starshooter"
    ]
    other_albums = [album for album in albums if album not in kent_albums and album not in starshooter_albums]
    video_clips = _published(VideoClip, site).select_related("thumbnail")[:100]
    return render(
        request,
        "public_site/musique.html",
        {
            "kent_albums": kent_albums,
            "starshooter_albums": starshooter_albums,
            "other_albums": other_albums,
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
    return render(request, "public_site/album_detail.html", {"album": album, "tracks": tracks})


def song_detail(request, slug):
    site = _site(request)
    song = get_object_or_404(_published(Song, site), slug=slug)
    tracks = (
        Track.objects.filter(song=song, album__site=site, album__is_published=True)
        .select_related("album", "album__cover_image")
        .order_by("album__release_date", "track_number")
    )
    return render(request, "public_site/song_detail.html", {"song": song, "tracks": tracks})


def livres(request):
    site = _site(request)
    books = list(_published(Book, site).select_related("cover_image").filter(show_on_books_page=True))
    sections = [
        ("Romans", [book for book in books if book.category == Book.Category.NOVELS]),
        ("Divers", [book for book in books if book.category == Book.Category.OTHER]),
        ("Livres illustrés", [book for book in books if book.category == Book.Category.ILLUSTRATED]),
        ("Livres jeunesse", [book for book in books if book.category == Book.Category.CHILDREN]),
    ]
    return render(request, "public_site/livres.html", {"sections": sections, "books": books})


def book_detail(request, slug):
    site = _site(request)
    book = get_object_or_404(
        _published(Book, site).select_related("cover_image").prefetch_related("additional_images"),
        slug=slug,
    )
    return render(request, "public_site/book_detail.html", {"book": book})


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
        "public_site/dessins.html",
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
        return render(request, "public_site/bd_detail.html", {"bd": bd})

    drawing = get_object_or_404(
        _published(Drawing, site).prefetch_related("images"),
        slug=slug,
    )
    return render(request, "public_site/drawing_detail.html", {"drawing": drawing})


def posts(request):
    site = _site(request)
    articles = _published(Article, site).select_related("featured_image")[:100]
    return render(request, "public_site/posts.html", {"articles": articles})


def post_detail(request, slug):
    site = _site(request)
    article = get_object_or_404(
        _published(Article, site).select_related("featured_image"),
        slug=slug,
    )
    return render(request, "public_site/post_detail.html", {"article": article})


def _published(model, site):
    return model.objects.filter(site=site, is_published=True)
