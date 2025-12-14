from app import create_app
from app.extensions import db

app = create_app()

with app.app_context():
    try:
        # Voeg role kolom toe
        db.session.execute(db.text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS role VARCHAR(50) DEFAULT \'depot_manager\';'))
        print("✓ Role column added")
        
        # Verwijder oude constraint
        db.session.execute(db.text('ALTER TABLE "user" DROP CONSTRAINT IF EXISTS user_role_check;'))
        print("✓ Old constraint removed")
        
        # Voeg nieuwe constraint toe
        db.session.execute(db.text('ALTER TABLE "user" ADD CONSTRAINT user_role_check CHECK (role IN (\'depot_manager\', \'finance_manager\', \'admin\'));'))
        print("✓ New constraint added")
        
        # Maak index
        db.session.execute(db.text('CREATE INDEX IF NOT EXISTS idx_user_role ON "user"(role);'))
        print("✓ Index created")
        
        db.session.commit()
        print("\n✅ Migration completed successfully!")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error: {e}")
