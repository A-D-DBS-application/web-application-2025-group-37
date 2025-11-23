from app import create_app, db
from sqlalchemy import text

app = create_app()
ctx = app.app_context()
ctx.push()

with open('migrations/add_address_components.sql', 'r') as f:
    sql = f.read()

with db.engine.connect() as conn:
    conn.execute(text(sql))
    conn.commit()

print('✓ Migration completed successfully - address columns added to member table')
