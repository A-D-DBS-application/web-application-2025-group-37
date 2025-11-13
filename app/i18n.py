# Simple in-app i18n helper without external dependencies
# Usage in templates: {{ t('Home') }}
# Add new keys as Dutch source strings; provide FR translations below.

from typing import Callable

LANGUAGES = ['nl', 'fr']

TRANSLATIONS = {
    'fr': {
        # Navbar
        'Home': 'Accueil',
        'Dashboard': 'Tableau de bord',
        'Fietsen': 'Vélos',
        'Leden': 'Membres',
        'Over': 'À propos',
        'Logout': 'Déconnexion',
        'Login': 'Connexion',
        # Home page
        'Welkom bij OpWielekes': 'Bienvenue chez OpWielekes',
        'Huur, bekijk en beheer fietsen eenvoudig. Ontdek onze collectie en vind de fiets die bij jou past!': 'Louez, consultez et gérez des vélos facilement. Découvrez notre collection et trouvez le vélo qui vous convient !',
        'Bekijk Fietsen': 'Voir les vélos',
    # Image alt texts
    'Family cycling': 'Famille à vélo',
    'Kids with bicycles': 'Enfants avec des vélos',
    'Parents and children with bikes': 'Parents et enfants avec des vélos',
    'Happy cycling': 'Cyclisme heureux',
    'Bike in park': 'Vélo dans le parc',
    'Family cycling together': 'Famille à vélo ensemble',
    'Kids with helmets': 'Enfants avec des casques',
    # USP / About teaser
    'Waarom OpWielekes?': 'Pourquoi OpWielekes ?',
    'Samen maken we fietsen toegankelijk, leuk en duurzaam voor elk gezin.': 'Ensemble, nous rendons le vélo accessible, amusant et durable pour chaque famille.',
    'Betaalbaar': 'Abordable',
    'Lage kosten en eerlijke formules zodat iedereen kan fietsen.': 'Coûts bas et formules équitables pour que tout le monde puisse faire du vélo.',
    'Duurzaam': 'Durable',
    'Tweedehands en circulair: minder afval, meer rijplezier.': 'Seconde main et circulaire : moins de déchets, plus de plaisir à rouler.',
    'Gemeenschap': 'Communauté',
    'Vrijwilligers, ouders en kinderen bouwen samen aan mobiliteit.': 'Bénévoles, parents et enfants construisent ensemble la mobilité.',
    'Veiligheid': 'Sécurité',
    'We letten op onderhoud, helmgebruik en veilige routes.': 'Nous veillons à l’entretien, au port du casque et aux itinéraires sûrs.',
    'Meer over ons': 'En savoir plus',
        # Generic
        'Nieuwe fiets': 'Nouveau vélo',
        'Opslaan': 'Enregistrer',
        'Verhuren': 'Louer',
        'Bewerken': 'Modifier',
        'Archiveren': 'Archiver',
    'Verwijderen': 'Supprimer',
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
        # Depot Manager / Login
        'Depot Manager': 'Gestionnaire du dépôt',
        'Beheer fietsen, leden en verhuur vanuit één overzichtelijk dashboard.': 'Gérez vélos, membres et locations depuis un tableau de bord clair.',
        'Snel leden zoeken en bewerken': 'Recherche et modification rapides des membres',
        'Fietsen toevoegen, verhuren en archiveren': 'Ajouter, louer et archiver des vélos',
        'Betalingen registreren en opvolgen': 'Enregistrer et suivre les paiements',
        'Inloggen': 'Se connecter',
        'E-mail': 'E-mail',
        'Wachtwoord': 'Mot de passe',
        'Standaard: admin@example.com / admin': 'Par défaut : admin@example.com / admin',
        'Werkplaats met fietsen': 'Atelier avec vélos',
        'OpWielekes logo': 'Logo OpWielekes',
        'Wachtwoord vergeten?': 'Mot de passe oublié ?'
        ,
        'We sturen je een link om je wachtwoord te resetten.': 'Nous vous envoyons un lien pour réinitialiser votre mot de passe.',
        'Stuur reset-link': 'Envoyer le lien de réinitialisation',
        'Terug naar inloggen': 'Retour à la connexion',
        # Members
        'Nieuw lid': 'Nouveau membre',
        'Betaling': 'Paiement',
        'No payment': 'Pas de paiement',
        # Dashboard specific
        'Actieve leden': 'Membres actifs',
        'Beschikbare fietsen': 'Vélos disponibles',
        'Bekijk leden →': 'Voir les membres →',
        'Bekijk fietsen →': 'Voir les vélos →',
        'Geen actieve leden.': 'Aucun membre actif.',
        'Geen beschikbare fietsen.': 'Aucun vélo disponible.',
        'actief': 'actif',
        'beschikbaar': 'disponible',
        'verhuurd': 'loué',
        'in herstelling': 'en réparation',
    },
    'nl': {}
}


def get_translator(lang: str) -> Callable[[str], str]:
    mapping = TRANSLATIONS.get(lang, {})

    def t(s: str) -> str:
        return mapping.get(s, s)

    return t
