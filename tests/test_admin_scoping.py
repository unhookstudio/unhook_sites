from django.contrib import admin
from django.contrib.auth.models import Permission
from django.test import RequestFactory
from django.urls import reverse

from sites_core.models import NavigationLink, Site, User


def test_site_admin_limits_staff_to_allowed_sites(db):
    kent = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    other = Site.objects.create(name="Other", slug="other", domain="example.com")
    user = User.objects.create_user(username="editor", is_staff=True)
    user.sites.add(kent)
    request = RequestFactory().get("/admin/sites_core/site/")
    request.user = user

    queryset = admin.site._registry[Site].get_queryset(request)

    assert list(queryset) == [kent]
    assert other not in queryset


def test_site_admin_shows_all_sites_to_superuser(db):
    kent = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    other = Site.objects.create(name="Other", slug="other", domain="example.com")
    user = User.objects.create_superuser(username="admin")
    request = RequestFactory().get("/admin/sites_core/site/")
    request.user = user

    queryset = admin.site._registry[Site].get_queryset(request)

    assert set(queryset) == {kent, other}


def test_site_scoped_admin_uses_default_site_as_initial_data(db):
    kent = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    user = User.objects.create_user(username="editor", is_staff=True, default_site=kent)
    request = RequestFactory().get("/admin/sites_core/navigationlink/add/")
    request.user = user

    model_admin = admin.site._registry[NavigationLink]
    initial = model_admin.get_changeform_initial_data(request)

    assert initial["site"] == kent.pk


def test_site_scoped_admin_does_not_set_initial_blank_default_site(db):
    user = User.objects.create_user(username="editor", is_staff=True)
    request = RequestFactory().get("/admin/sites_core/navigationlink/add/")
    request.user = user

    model_admin = admin.site._registry[NavigationLink]
    initial = model_admin.get_changeform_initial_data(request)

    assert "site" not in initial


def test_site_admin_changelist_and_detail_are_scoped_for_staff(client, db):
    kent = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    other = Site.objects.create(name="Other", slug="other", domain="example.com")
    user = User.objects.create_user(username="editor", password="password", is_staff=True)
    user.sites.add(kent)
    user.user_permissions.add(
        Permission.objects.get(codename="view_site"),
        Permission.objects.get(codename="change_site"),
    )

    client.force_login(user)

    changelist = client.get(reverse("admin:sites_core_site_changelist"))
    other_detail = client.get(reverse("admin:sites_core_site_change", args=[other.pk]))

    assert changelist.status_code == 200
    assert "Kent" in changelist.text
    assert "Other" not in changelist.text
    assert other_detail.status_code == 404


def test_site_owned_admin_changelist_and_detail_are_scoped_for_staff(client, db):
    kent = Site.objects.create(name="Kent", slug="kent", domain="kent-artiste.com")
    other = Site.objects.create(name="Other", slug="other", domain="example.com")
    kent_link = NavigationLink.objects.create(site=kent, label="Kent link", url="/kent/")
    other_link = NavigationLink.objects.create(site=other, label="Other link", url="/other/")
    user = User.objects.create_user(username="editor", password="password", is_staff=True)
    user.sites.add(kent)
    user.user_permissions.add(
        Permission.objects.get(codename="view_navigationlink"),
        Permission.objects.get(codename="change_navigationlink"),
    )

    client.force_login(user)

    changelist = client.get(reverse("admin:sites_core_navigationlink_changelist"))
    other_detail = client.get(
        reverse("admin:sites_core_navigationlink_change", args=[other_link.pk])
    )

    assert changelist.status_code == 200
    assert kent_link.label in changelist.text
    assert other_link.label not in changelist.text
    assert other_detail.status_code == 404
