from flask import Flask, g, session, request
from routes import main
from config import Config
from extensions import db
from i18n import get_translator, LANGUAGES

def create_app():
    app = Flask(__name__)
    # Load configuration
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(main)

    # Create tables in dev; for production use migrations
    with app.app_context():
        db.create_all()

    # --- i18n wiring (simple dictionary-based) ---
    @app.before_request
    def _select_language():
        lang = session.get('lang')
        if not lang:
            # Try to match browser language; fall back to NL
            best = request.accept_languages.best_match(LANGUAGES)
            lang = best or 'nl'
        g.lang = lang
        g.t = get_translator(lang)

    @app.context_processor
    def _inject_i18n():
        return {
            't': getattr(g, 't', lambda s: s),
            'current_lang': getattr(g, 'lang', 'nl'),
            'LANGUAGES': LANGUAGES,
        }

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)

