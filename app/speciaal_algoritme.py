from datetime import date, timedelta
from typing import List, Dict, Any

from app.extensions import db
from app.models import Rental, Member, Child, Bike


def _days_until(target: date) -> int:
    """Return number of days from today until target (negative if past)."""
    if not target:
      return 10**9
    return (target - date.today()).days


def get_upcoming_rentals(days_threshold: int = 30) -> List[Dict[str, Any]]:
    """
    Speciaal algoritme: vind verhuringen die binnen `days_threshold` dagen aflopen.

    Returns a list of dictionaries with keys:
      - rental_id
      - end_date
      - days_left
      - parent_name
      - parent_email
      - child_name
      - bike_name
      - bike_type
    """
    # Query active rentals that have an end date
    q = db.session.query(Rental, Child, Member, Bike) \
        .join(Child, Rental.child_id == Child.child_id) \
        .join(Member, Child.member_id == Member.member_id) \
        .join(Bike, Rental.bike_id == Bike.bike_id) \
        .filter(Rental.status == 'active')

    results: List[Dict[str, Any]] = []
    for rental, child, member, bike in q.all():
        if not rental.end_date:
            # Skip if no end date (should be rare after migrations)
            continue
        days_left = _days_until(rental.end_date)
        if 0 <= days_left <= days_threshold:
            results.append({
                'rental_id': rental.rental_id,
                'end_date': rental.end_date,
                'days_left': days_left,
                'parent_name': f"{member.first_name} {member.last_name}",
                'parent_email': member.email,
                'child_name': f"{child.first_name} {child.last_name}",
                'bike_name': bike.name or (bike.model or bike.brand),
                'bike_type': bike.type,
            })

    # Sort soonest first
    results.sort(key=lambda r: r['days_left'])
    return results


def get_upcoming_rentals_for_popup(days_threshold: int = 30) -> Dict[str, Any]:
    """
    Helper payload tailored for a dashboard popup.
    Returns minimal fields; email copy action should copy the parent's email address only.
    """
    upcoming = get_upcoming_rentals(days_threshold)
    return {
        'generated_at': date.today().isoformat(),
        'days_threshold': days_threshold,
        'count': len(upcoming),
        'items': upcoming,
    }
