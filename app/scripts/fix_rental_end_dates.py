from datetime import timedelta
from app.extensions import db
from app.models import Rental


def backfill_end_dates():
    count = 0
    rentals = Rental.query.all()
    for r in rentals:
        try:
            if r.start_date and not r.end_date:
                r.end_date = r.start_date + timedelta(days=365)
                count += 1
        except Exception:
            continue
    db.session.commit()
    return count

if __name__ == '__main__':
    # This script expects to be run within the Flask app context.
    # Use run_migration.py to execute it.
    print("Start backfilling rental end dates...")
    updated = backfill_end_dates()
    print(f"Updated rentals: {updated}")
