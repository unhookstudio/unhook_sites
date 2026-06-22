from django.db import migrations


KENT_SOCIAL_URLS = {
    "facebook_url": "https://www.facebook.com/kentartiste",
    "instagram_url": "https://www.instagram.com/kent_artiste",
    "bandcamp_url": "https://kent-artiste.bandcamp.com",
    "youtube_url": "https://www.youtube.com/user/ChaineOfficielleKENT",
}


def populate_kent_social_urls(apps, schema_editor):
    SiteSettings = apps.get_model("sites_core", "SiteSettings")
    settings = SiteSettings.objects.filter(site__slug="kent").first()
    if settings is None:
        return

    updated_fields = []
    for field_name, url in KENT_SOCIAL_URLS.items():
        if not getattr(settings, field_name):
            setattr(settings, field_name, url)
            updated_fields.append(field_name)

    if updated_fields:
        settings.save(update_fields=updated_fields)


class Migration(migrations.Migration):

    dependencies = [
        ("sites_core", "0006_sitesettings_bandcamp_url"),
    ]

    operations = [
        migrations.RunPython(populate_kent_social_urls, migrations.RunPython.noop),
    ]
