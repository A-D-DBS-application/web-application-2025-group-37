from app import create_app, db
from sqlalchemy import text

app = create_app()
ctx = app.app_context()
ctx.push()

def run_sql_migration(path: str, success_message: str):
    with open(path, 'r') as f:
        sql = f.read()
    with db.engine.connect() as conn:
        conn.execute(text(sql))
        conn.commit()
    print(success_message)

def run_python_migration(func, success_message: str):
    updated = func()
    print(f"{success_message} (updated: {updated})")

if __name__ == '__main__':
    # Example SQL migration
    try:
        run_sql_migration('migrations/add_address_components.sql', '✓ SQL migration applied: address columns added')
    except Exception as e:
        print(f"SQL migration skipped or failed: {e}")

    # Backfill rental end dates for existing rentals
    try:
        from app.scripts.fix_rental_end_dates import backfill_end_dates
        run_python_migration(backfill_end_dates, '✓ Backfilled rental end dates to +1 year from start')
    except Exception as e:
        print(f"Python migration skipped or failed: {e}")
