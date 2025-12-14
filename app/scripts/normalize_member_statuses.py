from app import create_app
from app.extensions import db
from app.models import Member

# Map localized/legacy statuses to canonical
STATUS_MAP = {
    None: 'active',
    '': 'active',
    'actief': 'active',
    'inactief': 'inactive',
    'gepauzeerd': 'paused',
}

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        total = 0
        updated = 0
        members = Member.query.all()
        for m in members:
            s = (m.status or '').strip().lower()
            canonical = STATUS_MAP.get(s, s if s in {'active','inactive','paused'} else 'active')
            total += 1
            if m.status != canonical:
                m.status = canonical
                updated += 1
        db.session.commit()
        print(f"Members scanned: {total}, updated: {updated}")
