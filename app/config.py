import os
from dotenv import load_dotenv

# Load env vars from .env; if missing, fall back to .env.example so a fresh clone still links to Supabase
load_dotenv()
if not os.getenv('DATABASE_URL'):
    # Auto-load defaults for teammates who didn't create a local .env yet
    load_dotenv('.env.example')


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret')
    # Always prefer env var; now that we auto-load .env.example, this should resolve to Supabase on a fresh clone
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    # Normalize Heroku-style postgres URL
    if SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql+psycopg2://', 1)
    SQLALCHEMY_TRACK_MODIFICATIONS = False


