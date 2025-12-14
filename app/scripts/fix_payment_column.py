from app import create_app, db

app = create_app()
with app.app_context():
    db.session.execute(db.text("ALTER TABLE payment ADD COLUMN IF NOT EXISTS method VARCHAR(20) DEFAULT 'cash'"))
    db.session.commit()
    print("✓ Payment method column added successfully")
