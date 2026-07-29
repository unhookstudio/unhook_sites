from django.db import migrations


ABOUT_TEXT_SNIPPETS = {
    "about_quote": (
        "Difficile de trouver artiste plus accompli que Kent. Entre chanson, bande dessinée "
        "et romans, l’homme déborde de créativité depuis quatre décennies. Il est rare de "
        "croiser le chemin d’un homme aussi épanoui."
    ),
    "about_quote_author": "Olivier Nuc, Le Figaro",
    "about_biography": (
        "<p>Une de ses chansons s'intitule « En route vers de nouvelles aventures ».</p>"
        "<p>Si l'on voulait présenter Kent en quelques mots, c'est une devise qui lui irait "
        "bien. Autant de découvertes proposées, autant de perspectives qu'il se plaît à "
        "explorer et qui, suivant l'instant, la rencontre, deviennent une chanson, un dessin "
        "ou un livre.</p>"
        "<p>Né à la Croix-Rousse, Lyon 4ème, dans une famille ouvrière. Tout gamin, il tombe "
        "dans la bande dessinée et dès 13 ans, il découvre le rock et plaque ses premiers "
        "accords de guitare. Ces deux passions seront désormais deux rêves à aboutir et le "
        "moteur d'une vie.</p>"
        "<p>Sur les bancs du lycée, il rencontre trois autres garçons. Ils se feront connaître "
        "sous le nom de Starshooter. Le groupe enregistrera 4 albums entre 1977 et 1982.</p>"
        "<p>Kent entamera sa carrière solo dès 1983. Il a publié à ce jour 16 albums studio "
        "sous son nom, ainsi que 10 albums live.</p>"
        "<p>Mû par une curiosité musicale et un besoin de se renouveler, il s'aventure et "
        "propose un répertoire allant du rock électro au piano/voix.</p>"
        "<p>Kent, artiste atypique, artiste aux multiples casquettes, artiste tout court, "
        "voyage une guitare et un crayon à la main et revient là où on ne l'attend pas.</p>"
    ),
}


ABOUT_TEXT_LABELS = {
    "about_quote": "À propos - citation",
    "about_quote_author": "À propos - auteur de la citation",
    "about_biography": "À propos - biographie",
}


def populate_kent_about_texts(apps, schema_editor):
    Site = apps.get_model("sites_core", "Site")
    TextSnippet = apps.get_model("sites_core", "TextSnippet")
    site = Site.objects.filter(slug="kent").first()
    if site is None:
        return

    for key, text in ABOUT_TEXT_SNIPPETS.items():
        TextSnippet.objects.get_or_create(
            site=site,
            key=key,
            defaults={
                "label": ABOUT_TEXT_LABELS[key],
                "text": text,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("sites_core", "0012_sitesettings_dates_secondary_title"),
    ]

    operations = [
        migrations.RunPython(populate_kent_about_texts, migrations.RunPython.noop),
    ]
