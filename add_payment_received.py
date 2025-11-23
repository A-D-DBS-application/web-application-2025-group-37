"""
Migratie script om 'received' kolom toe te voegen aan payment tabel
Voor bankbetalingen: markeren of bedrag reeds ontvangen is
"""

from app import create_app
from app.extensions import db
from sqlalchemy import text

def run_migration():
    app = create_app()
    
    with app.app_context():
        try:
            # Voeg received kolom toe
            db.session.execute(text("""
                ALTER TABLE payment 
                ADD COLUMN IF NOT EXISTS received BOOLEAN DEFAULT TRUE;
            """))
            
            # Update bestaande records: cash en card zijn altijd received=True
            # bank_transfer records krijgen ook True als default (veilige aanname)
            db.session.execute(text("""
                UPDATE payment 
                SET received = TRUE 
                WHERE received IS NULL;
            """))
            
            db.session.commit()
            print("✅ Migratie succesvol! Kolom 'received' toegevoegd aan payment tabel.")
            print("   - Alle bestaande betalingen zijn gemarkeerd als 'ontvangen'")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Fout bij migratie: {e}")
            raise

if __name__ == '__main__':
    run_migration()
