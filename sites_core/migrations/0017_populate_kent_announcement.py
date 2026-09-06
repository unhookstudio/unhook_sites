from django.db import migrations


def populate_announcement(apps, schema_editor):
    Site = apps.get_model("sites_core", "Site")
    SiteSettings = apps.get_model("sites_core", "SiteSettings")
    database = schema_editor.connection.alias
    site = Site.objects.using(database).filter(slug="kent").first()
    if site is None:
        return
    settings, _ = SiteSettings.objects.using(database).get_or_create(site=site)
    if settings.announcement_title or settings.announcement_body:
        return
    settings.announcement_title = "CECI EST UNE ENQUÊTE"
    settings.announcement_body = (
        "<p>Le 30 avril 2014, je participais à la soirée Léo Ferré à l’Européen (Paris). "
        "J’ai chanté quatre chansons du Monsieur et deux des miennes, accompagné au piano "
        "par Marc Haussmann. Je souhaite sortir l’enregistrement dans l’Intime Collection.</p>"
        "<p>MAIS ! Ma prestation ne durant que 20 minutes, plutôt qu’éditer un CD, nous "
        "songeons, puisque la durée s’y prête, produire un vinyle en 25 cm. furieusement 50’s !</p>"
        "<p>Cependant, avant de nous lancer, nous voudrions savoir combien de personnes "
        "seraient intéressées par un tel disque. Si c’est votre cas, dites-le nous à "
        "l’adresse suivante : <a href=\"mailto:thoobett@gmail.com\">thoobett@gmail.com</a></p>"
        "<p>Le projet se réalisera en fonction de la demande.</p>"
    )
    settings.announcement_button_text = "Je suis intéressé"
    settings.announcement_button_url = "mailto:thoobett@gmail.com?subject=Vinyle%20L%C3%A9o%20Ferr%C3%A9"
    settings.save(using=database, update_fields=[
        "announcement_title", "announcement_body",
        "announcement_button_text", "announcement_button_url",
    ])


class Migration(migrations.Migration):
    dependencies = [("sites_core", "0016_sitesettings_announcement_body_and_more")]
    operations = [migrations.RunPython(populate_announcement, migrations.RunPython.noop)]
