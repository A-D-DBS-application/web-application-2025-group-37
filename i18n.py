# Simple in-app i18n helper without external dependencies
# Usage in templates: {{ t('Home') }}
# Add new keys as Dutch source strings; provide FR translations below.

from typing import Callable

LANGUAGES = ['nl', 'fr']

TRANSLATIONS = {
    'fr': {
        # Navbar
        'Home': 'Accueil',
        'Fietsen': 'Vélos',
        'Leden': 'Membres',
        'Over': 'À propos',
        'Logout': 'Déconnexion',
        'Login': 'Connexion',
        # Home page
        'Welkom bij OpWielekes': 'Bienvenue chez OpWielekes',
        'Huur, bekijk en beheer fietsen eenvoudig. Ontdek onze collectie en vind de fiets die bij jou past!': 'Louez, consultez et gérez des vélos facilement. Découvrez notre collection et trouvez le vélo qui vous convient !',
        'Bekijk Fietsen': 'Voir les vélos',
        # Generic
        'Nieuwe fiets': 'Nouveau vélo',
        'Opslaan': 'Enregistrer',
        'Verhuren': 'Louer',
        'Bewerken': 'Modifier',
        'Archiveren': 'Archiver',
        'Naam': 'Nom',
        'Type': 'Type',
        'Status': 'Statut',
        'Acties': 'Actions',
        'Beschikbare Items': 'Articles disponibles',
        'Fietsen': 'Vélos',
        'Geen fietsen. Voeg een nieuwe fiets toe.': 'Pas de vélos. Ajoutez un nouveau vélo.',
        # Footer
        '© 2025 OpWielekes – Alle rechten voorbehouden': '© 2025 OpWielekes – Tous droits réservés',
        # Language banner
        'Kies je taal': 'Choisissez votre langue',
        'Nederlands': 'Néerlandais',
        'Français': 'Français',
    },
    'nl': {}
}


def get_translator(lang: str) -> Callable[[str], str]:
    mapping = TRANSLATIONS.get(lang, {})

    def t(s: str) -> str:
        return mapping.get(s, s)

    return t
