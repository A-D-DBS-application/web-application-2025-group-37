from datetime import date, timedelta
from sqlalchemy import func, desc, or_
from app.extensions import db
from app.models import Bike, Member, Rental, Payment, Child, Item

def get_dashboard_stats():
    today = date.today()
    month_start = today.replace(day=1)
    thirty_days_ago = today - timedelta(days=30)
    seven_days_ago = today - timedelta(days=7)
    
    # --- BASIS TELLERS ---
    total_bikes = Bike.query.filter_by(archived=False).count()
    available_bikes_count = Bike.query.filter_by(status='available', archived=False).count()
    rented_bikes_count = Bike.query.filter_by(status='rented', archived=False).count()
    repair_bikes_count = Bike.query.filter_by(status='repair', archived=False).count()
    
    # Fietsen toegevoegd vandaag
    new_bikes_today = Bike.query.filter(
        Bike.archived == False, 
        func.date(Bike.created_at) == today
    ).count()
    
    # --- LEDEN STATISTIEKEN ---
    total_members = Member.query.count()
    active_members_count = Member.query.filter_by(status='active').count()
    new_members_this_month = Member.query.filter(func.date(Member.created_at) >= month_start).count()
    
    # Achterstallige leden (geen betaling in laatste jaar of nooit)
    one_year_ago = today - timedelta(days=365)
    overdue_members_count = Member.query.filter(
        Member.status == 'active',
        or_(Member.last_payment == None, Member.last_payment < one_year_ago)
    ).count()
    
    # --- KINDEREN ---
    total_children = Child.query.count()
    # Kinderen zonder actieve fiets
    children_with_rental_ids = db.session.query(Rental.child_id).filter(
        Rental.status == 'active', Rental.child_id != None
    ).distinct()
    children_without_bike = Child.query.filter(~Child.child_id.in_(children_with_rental_ids)).count()
    new_children_this_month = 0 # Placeholder
    
    # --- BETALINGEN ---
    payments_this_month = db.session.query(func.sum(Payment.amount)).filter(func.date(Payment.paid_at) >= month_start).scalar() or 0
    
    # Totalen per methode (voor grafiek)
    cash_payments = db.session.query(func.sum(Payment.amount)).filter(Payment.method == 'cash').scalar() or 0
    card_payments = db.session.query(func.sum(Payment.amount)).filter(Payment.method == 'card').scalar() or 0
    bank_payments = db.session.query(func.sum(Payment.amount)).filter(Payment.method == 'bank_transfer', Payment.received == True).scalar() or 0
    
    overdue_amount = overdue_members_count * 10 # Ruwe schatting
    last_payment = Payment.query.order_by(Payment.paid_at.desc()).first()
    
    # --- VERHURINGEN ---
    active_rentals_count = Rental.query.filter_by(status='active').count()
    rentals_today = Rental.query.filter(func.date(Rental.start_date) == today).count()
    returns_today = Rental.query.filter(func.date(Rental.end_date) == today, Rental.status == 'returned').count()
    
    # --- PERCENTAGES ---
    active_member_percentage = round((active_members_count / total_members * 100) if total_members > 0 else 0, 1)
    bike_availability_percentage = round((available_bikes_count / total_bikes * 100) if total_bikes > 0 else 0, 1)
    children_with_bike_percentage = round(((total_children - children_without_bike) / total_children * 100) if total_children > 0 else 0, 1)

    # --- REPAIR STATS (Dit miste je!) ---
    repair_stats = {
        'total_in_repair': repair_bikes_count,
        'avg_repair_time': None, # Placeholder
        'bikes': Bike.query.filter_by(status='repair', archived=False).limit(5).all()
    }

    # --- GRAFIEK DATA (Lijsten opbouwen) ---
    # 1. Rental Activity (laatste 7 dagen)
    rental_chart_labels = []
    rental_chart_rentals = []
    rental_chart_returns = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        rental_chart_labels.append(day.strftime('%d/%m'))
        rental_chart_rentals.append(Rental.query.filter(func.date(Rental.start_date) == day).count())
        rental_chart_returns.append(Rental.query.filter(func.date(Rental.end_date) == day, Rental.status == 'returned').count())

    # 2. Wekelijkse omzet (laatste 8 weken)
    payment_weeks = []
    payment_amounts = []
    start_of_week = today - timedelta(days=today.weekday())
    for i in range(7, -1, -1):
        week_start = start_of_week - timedelta(weeks=i)
        week_end = week_start + timedelta(days=7)
        amt = db.session.query(func.sum(Payment.amount)).filter(Payment.paid_at >= week_start, Payment.paid_at < week_end).scalar() or 0
        payment_weeks.append(f"{week_start.strftime('%d/%m')}")
        payment_amounts.append(float(amt))

    # 3. Categorieën
    bike_categories = []
    # Simpele groepering op type
    types = db.session.query(Bike.type).distinct().all()
    for t in types:
        t_name = t[0] or "Onbekend"
        total = Bike.query.filter_by(type=t_name, archived=False).count()
        avail = Bike.query.filter_by(type=t_name, status='available', archived=False).count()
        rented = Bike.query.filter_by(type=t_name, status='rented', archived=False).count()
        bike_categories.append({'name': t_name.title(), 'total': total, 'available': avail, 'rented': rented})

    # --- RETURN CONTEXT ---
    return {
        'now': today,
        
        # Fietsen
        'total_bikes': total_bikes,
        'available_bikes_count': available_bikes_count,
        'rented_bikes_count': rented_bikes_count,
        'repair_bikes_count': repair_bikes_count,
        'missing_bikes_count': 0,
        'new_bikes_today': new_bikes_today,
        'bike_availability_percentage': bike_availability_percentage,
        
        # Leden
        'active_members_count': active_members_count,
        'total_members': total_members,
        'new_members_this_month': new_members_this_month,
        'overdue_members_count': overdue_members_count,
        'active_member_percentage': active_member_percentage,
        
        # Kinderen
        'total_children': total_children,
        'children_without_bike': children_without_bike,
        'new_children_this_month': new_children_this_month,
        'children_with_bike_percentage': children_with_bike_percentage,
        
        # Betalingen
        'payments_this_month': payments_this_month,
        'cash_payments': float(cash_payments),
        'card_payments': float(card_payments),
        'bank_payments': float(bank_payments),
        'overdue_amount': overdue_amount,
        
        # Verhuringen
        'active_rentals_count': active_rentals_count,
        'rentals_today': rentals_today,
        'returns_today': returns_today,
        'rentals_due_tomorrow': 0,
        
        # ONDERHOUD / REPAIR STATS (De oplossing voor je error)
        'repair_stats': repair_stats,
        
        # Grafieken & Lijsten
        'rental_chart_labels': rental_chart_labels,
        'rental_chart_rentals': rental_chart_rentals,
        'rental_chart_returns': rental_chart_returns,
        'payment_weeks': payment_weeks,
        'payment_amounts': payment_amounts,
        'bike_categories': bike_categories,
        'item_categories': [], # Leeg laten om fouten te voorkomen
        
        # Pie chart placeholders
        'member_pie_labels': ['Actief', 'Inactief'],
        'member_pie_values': [active_members_count, total_members - active_members_count],
        'inventory_chart_labels': [c['name'] for c in bike_categories],
        'inventory_chart_available': [c['available'] for c in bike_categories],
        'inventory_chart_rented': [c['rented'] for c in bike_categories],
        
        # Overige placeholders
        'todo_items': [],
        'recent_activity': [],
        'achievements': [],
        'top_debtors': [],
        'unused_bikes': [],
        'popular_models': [],
        'rental_hours': [0]*24,
        'avg_rental_duration': 0
    }

def get_rental_activity_data():
    """API helper"""
    today = date.today()
    labels = []
    data = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        labels.append(day.strftime('%d/%m'))
        count = Rental.query.filter(func.date(Rental.start_date) == day).count()
        data.append(count)
    return {'labels': labels, 'rentals': data}