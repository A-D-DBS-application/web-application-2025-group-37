from flask import Flask
from routes import main
from config import Config
from extensions import db

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

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)

