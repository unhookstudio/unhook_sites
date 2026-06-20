from django.urls import path

from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("dates", views.dates, name="dates"),
    path("a-propos", views.a_propos, name="a_propos"),
    path("musique", views.musique, name="musique"),
    path("album/<slug:slug>", views.album_detail, name="album_detail"),
    path("chanson/<slug:slug>", views.song_detail, name="song_detail"),
    path("livres", views.livres, name="livres"),
    path("livres/<slug:slug>", views.book_detail, name="book_detail"),
    path("dessins", views.dessins, name="dessins"),
    path("dessins/<slug:slug>", views.dessin_detail, name="dessin_detail"),
    path("posts", views.posts, name="posts"),
    path("post/<slug:slug>", views.post_detail, name="post_detail"),
    path("newsletter", views.newsletter_signup, name="newsletter_signup"),
]
