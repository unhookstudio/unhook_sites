from django.contrib.auth.models import Permission
from django.urls import reverse

from media_library.models import Image
from sites_core.models import Site, User
from visual_art.models import BD, Drawing
from writing.models import Article, Book


def test_publishable_domain_model_sets_publish_state_without_saving(db):
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    article = Article.objects.create(site=site, title="News", slug="news")

    article.publish()

    assert article.is_published is True
    assert article.published_at is not None
    article.refresh_from_db()
    assert article.is_published is False


def test_book_keeps_specific_model_with_flexible_page_placement(db):
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")

    book = Book.objects.create(
        site=site,
        title="Illustrated Book",
        slug="illustrated-book",
        category=Book.Category.ILLUSTRATED,
        show_on_books_page=True,
        show_on_drawings_page=True,
    )

    assert book.show_on_books_page is True
    assert book.show_on_drawings_page is True


def test_bd_drawing_and_book_are_separate_models(db):
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")

    book = Book.objects.create(site=site, title="Book", slug="book")
    bd = BD.objects.create(site=site, title="BD", slug="bd")
    drawing = Drawing.objects.create(site=site, title="Drawing", slug="drawing")

    assert str(book) == "Book"
    assert str(bd) == "BD"
    assert str(drawing) == "Drawing"


def test_payload_rich_text_json_is_preserved_alongside_html(db):
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    payload_content = {"root": {"children": [{"type": "paragraph"}]}}

    article = Article.objects.create(
        site=site,
        title="News",
        slug="news",
        content_html="<p>News</p>",
        payload_content=payload_content,
    )

    assert article.content_html == "<p>News</p>"
    assert article.payload_content == payload_content


def test_domain_model_can_reference_media_library_image(db):
    site = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    image = Image.objects.create(site=site, title="Cover")

    book = Book.objects.create(site=site, title="Book", slug="book", cover_image=image)

    assert book.cover_image == image


def test_domain_admin_changelist_and_detail_are_scoped_for_staff(client, db):
    kent = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    other = Site.objects.create(name="Other", slug="other", domain="example.com")
    kent_article = Article.objects.create(site=kent, title="Kent article", slug="kent-article")
    other_article = Article.objects.create(site=other, title="Other article", slug="other-article")
    user = User.objects.create_user(username="editor", password="password", is_staff=True)
    user.sites.add(kent)
    user.user_permissions.add(
        Permission.objects.get(codename="view_article"),
        Permission.objects.get(codename="change_article"),
    )

    client.force_login(user)

    changelist = client.get(reverse("admin:writing_article_changelist"))
    other_detail = client.get(reverse("admin:writing_article_change", args=[other_article.pk]))

    assert changelist.status_code == 200
    assert kent_article.title in changelist.text
    assert other_article.title not in changelist.text
    assert other_detail.status_code == 404
