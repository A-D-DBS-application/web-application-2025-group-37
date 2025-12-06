from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # Add code column to bike table
        with db.engine.begin() as conn:
            conn.execute(text('ALTER TABLE bike ADD COLUMN code VARCHAR(50)'))
        print('✓ Code column added successfully to bike table')
    except Exception as e:
        print(f'Column might already exist or error: {e}')
