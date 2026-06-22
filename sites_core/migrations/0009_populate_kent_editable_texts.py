from django.db import migrations


SITE_COPY = {
    "contact_title": "Kent est à l'écoute !",
    "contact_intro_text": (
        "Pour engager Kent, exprimer votre admiration, ou simplement dire Bonjour,\n"
        "vous pouvez utiliser ce formulaire."
    ),
    "newsletter_text": (
        "Environ une fois par mois, Kent envoie une newslettre remplie de ses états d'âme, "
        "de recommandations de films et musiques et bien plus encore."
    ),
}


TEXT_SNIPPETS = {
    "musique_quote_text": (
        "Du jeune punk rocker du groupe Starshooter à sa carrière solo d’auteur-compositeur "
        "reconnu, Kent s’est inventé mille vies et autant de pseudos. Mieux vaut changer "
        "pour ne jamais tourner en rond, et devenir un autre pour rester, en fait, "
        "au plus près de soi-même."
    ),
    "musique_quote_credit": "Thomas Boujut",
    "livres_quote_text": (
        "Entre chanson, bande dessinée et romans, l'homme déborde de créativité depuis "
        "quatre décennies. Il est rare de croiser le chemin d'un homme aussi épanoui."
    ),
    "livres_quote_credit": "Olivier Nuc, Le Figaro",
    "dessins_quote_text": (
        "Son coup de crayon est un mélange de sécheresse et d'amour.\n"
        "De sécheresse parce qu'il n'y a pas un trait de trop et d'amour du dessin."
    ),
    "dessins_quote_credit": "Jean-Pierre Dionnet",
    "home_card_about_title": "Chanteur, écrivain, illustrateur",
    "home_card_about_text": (
        "Une de ses chansons s'intitule : « En route vers de nouvelles aventures... » "
        "Autant de découvertes proposées, autant de perspectives qu'il se plaît à explorer."
    ),
    "home_card_music_title": "Musique",
    "home_card_music_text": (
        "Juste quelqu'un de bien, Betsy Party, J'aime un pays... La musique de Kent "
        "est marquée par un inépuisable esprit d'explorateur."
    ),
    "home_card_drawings_title": "Dessins",
    "home_card_drawings_text": (
        "Métal Hurlant, biographie d'Elvis Presley, l'histoire de Dada... "
        "Et toujours avec son trait caractéristique."
    ),
    "home_card_books_title": "Livres",
    "home_card_books_text": "Romans, poésie, essais et livres pour enfants.",
}


TEXT_SNIPPET_LABELS = {
    "musique_quote_text": "Musique - citation",
    "musique_quote_credit": "Musique - auteur de la citation",
    "livres_quote_text": "Livres - citation",
    "livres_quote_credit": "Livres - auteur de la citation",
    "dessins_quote_text": "Dessins - citation",
    "dessins_quote_credit": "Dessins - auteur de la citation",
    "home_card_about_title": "Accueil - carte À propos - titre",
    "home_card_about_text": "Accueil - carte À propos - texte",
    "home_card_music_title": "Accueil - carte Musique - titre",
    "home_card_music_text": "Accueil - carte Musique - texte",
    "home_card_drawings_title": "Accueil - carte Dessins - titre",
    "home_card_drawings_text": "Accueil - carte Dessins - texte",
    "home_card_books_title": "Accueil - carte Livres - titre",
    "home_card_books_text": "Accueil - carte Livres - texte",
}


def populate_kent_editable_texts(apps, schema_editor):
    Site = apps.get_model("sites_core", "Site")
    SiteSettings = apps.get_model("sites_core", "SiteSettings")
    TextSnippet = apps.get_model("sites_core", "TextSnippet")
    site = Site.objects.filter(slug="kent").first()
    if site is None:
        return

    settings = SiteSettings.objects.filter(site=site).first()
    if settings is not None:
        updated_fields = []
        for field_name, value in SITE_COPY.items():
            if not getattr(settings, field_name):
                setattr(settings, field_name, value)
                updated_fields.append(field_name)
        if updated_fields:
            settings.save(update_fields=updated_fields)

    for key, text in TEXT_SNIPPETS.items():
        TextSnippet.objects.get_or_create(
            site=site,
            key=key,
            defaults={
                "label": TEXT_SNIPPET_LABELS[key],
                "text": text,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("sites_core", "0008_sitesettings_contact_intro_text_and_more"),
    ]

    operations = [
        migrations.RunPython(populate_kent_editable_texts, migrations.RunPython.noop),
    ]
