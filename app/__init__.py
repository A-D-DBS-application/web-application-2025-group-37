from flask import Flask, g, session, request, url_for
import os
from app.routes import main
from app.config import Config
from app.extensions import db
from app.i18n import get_translator, LANGUAGES

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
        # Be resilient: don't crash the app if the target DB (e.g., Supabase pooler) rejects DDL
        try:
            db.create_all()
        except Exception as e:
            print(f"create_all skipped due to error: {e}")
        # Log a safe summary of the active DB connection (no secrets)
        try:
            url = db.engine.url
            driver = getattr(url, 'drivername', 'unknown')
            host = getattr(url, 'host', None)
            database = getattr(url, 'database', None)
            print(f"SQLAlchemy connected: driver={driver} host={host} db={database}")
        except Exception:
            pass

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
        def static_or(filename: str, fallback_url: str):
            """Return url_for('static', filename) if file exists, else fallback_url.
            Allows using local images when provided, with network fallback otherwise.
            """
            try:
                path = os.path.join(app.static_folder, filename.replace('/', os.sep))
                if os.path.isfile(path):
                    # Cache-bust with file mtime to avoid stale images
                    mtime = int(os.path.getmtime(path))
                    return url_for('static', filename=filename, v=mtime)
            except Exception:
                pass
            return fallback_url

        def static_first(filenames, fallback_url: str = None):
            """Return the first existing static file URL from a list, else fallback_url.
            Example: static_first(['img/home/logo-nl.svg','img/logo-nl.svg'], url_for('static', filename='img/logo.svg'))
            """
            for name in filenames or []:
                try:
                    path = os.path.join(app.static_folder, name.replace('/', os.sep))
                    if os.path.isfile(path):
                        mtime = int(os.path.getmtime(path))
                        return url_for('static', filename=name, v=mtime)
                except Exception:
                    continue
            return fallback_url
        return {
            't': getattr(g, 't', lambda s: s),
            'current_lang': getattr(g, 'lang', 'nl'),
            'LANGUAGES': LANGUAGES,
            'static_or': static_or,
            'static_first': static_first,
        }

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)

