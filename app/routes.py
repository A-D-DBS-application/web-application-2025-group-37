from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime, date
from app.extensions import db
from app.models import (
    Member, Child, User, Bike, Rental, Payment, Item,
    MEMBER_STATUSES, BIKE_TYPES, BIKE_STATUSES, ITEM_STATUSES, PAYMENT_METHODS
)
from sqlalchemy import text
from functools import wraps

main = Blueprint('main', __name__)

# ============================================
# Security Decorators - Rolgebaseerde toegangscontrole
# ============================================

def login_required(f):
    """
    Decorator die controleert of gebruiker is ingelogd.
    Redirect naar login pagina als niet ingelogd.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Je moet inloggen om deze pagina te bekijken.', 'warning')
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    """
    Decorator die controleert of gebruiker één van de toegestane rollen heeft.
    Gebruik: @role_required('depot_manager', 'admin')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Je moet inloggen om deze pagina te bekijken.', 'warning')
                return redirect(url_for('main.login'))
            
            user = User.query.get(session['user_id'])
            if not user:
                session.clear()
                flash('Gebruiker niet gevonden. Log opnieuw in.', 'error')
                return redirect(url_for('main.login'))
            
            if user.role not in allowed_roles:
                flash('Je hebt geen toegang tot deze pagina.', 'error')
                return redirect(url_for('main.dashboard'))
            
            # Store user role in session for template access
            session['user_role'] = user.role
            session['user_name'] = f"{user.first_name} {user.last_name}"
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def depot_access_required(f):
    """Shortcut decorator voor Depot Manager toegang"""
    return role_required('depot_manager', 'admin')(f)

def finance_access_required(f):
    """Shortcut decorator voor Finance Manager toegang"""
    return role_required('finance_manager', 'admin')(f)

@main.route('/bikes')
def bike_list():
    return redirect(url_for('main.inventory'))

# -----------------------
# Inventory overview
# -----------------------

@main.route('/')
def home():
    # Classic flow: show login when not authenticated, dashboard when logged in
    if session.get('user_id'):
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('main.login'))

@main.route('/inventory')
@login_required
@depot_access_required
def inventory():
    # Bikes
    bikes_all = Bike.query.filter_by(archived=False).order_by(Bike.created_at.desc()).all()
    available_bikes = [b for b in bikes_all if (b.status or '').lower() == 'available']
    rented_bikes = [b for b in bikes_all if (b.status or '').lower() == 'rented']
    repair_bikes = [b for b in bikes_all if (b.status or '').lower() == 'repair']

    # Map active rentals to show renter info
    active_rentals = Rental.query.filter_by(status='active').all()
    rental_map = {}
    for r in active_rentals:
        renter = None
        if r.member:
            renter = f"{r.member.first_name} {r.member.last_name}"
        elif r.child and r.child.member:
            renter = f"{r.child.member.first_name} {r.child.member.last_name}"
        if r.bike_id:
            rental_map[r.bike_id] = renter

    # Items (generic objects)
    items_all = Item.query.order_by(Item.created_at.desc()).all()
    def norm_item_status(s):
        s = (s or '').strip().lower()
        mapping = {
            'beschikbaar': 'available',
            'onbeschikbaar': 'unavailable',
            'verhuurd': 'rented',
            'in herstelling': 'repair'
        }
        return mapping.get(s, s)

    available_items = [i for i in items_all if norm_item_status(i.status) == 'available']
    unavailable_items = [i for i in items_all if norm_item_status(i.status) in {'unavailable', 'rented'}]
    rented_items = [i for i in items_all if norm_item_status(i.status) in {'unavailable', 'rented'}]
    repair_items = [i for i in items_all if norm_item_status(i.status) == 'repair']

    # Items currently don't have rentals; provide empty map to satisfy template
    item_rental_map = {}

    # Simple repair stats for insights card
    repair_stats = {
        'total_in_repair': len(repair_bikes),
        'avg_repair_time': 0,
        'bikes': repair_bikes
    }

    return render_template(
        'inventory.html',
        available_bikes=available_bikes,
        rented_bikes=rented_bikes,
        repair_bikes=repair_bikes,
        repair_stats=repair_stats,
        rental_map=rental_map,
        available_items=available_items,
        unavailable_items=unavailable_items,
        rented_items=rented_items,
        repair_items=repair_items,
        item_rental_map=item_rental_map,
        items_all=items_all
    )

@main.route('/inventory-public')
def inventory_public():
    # Reuse same logic as inventory without auth for testing
    bikes_all = Bike.query.filter_by(archived=False).order_by(Bike.created_at.desc()).all()
    available_bikes = [b for b in bikes_all if (b.status or '').lower() == 'available']
    rented_bikes = [b for b in bikes_all if (b.status or '').lower() == 'rented']
    repair_bikes = [b for b in bikes_all if (b.status or '').lower() == 'repair']

    active_rentals = Rental.query.filter_by(status='active').all()
    rental_map = {}
    for r in active_rentals:
        renter = None
        if r.member:
            renter = f"{r.member.first_name} {r.member.last_name}"
        elif r.child and r.child.member:
            renter = f"{r.child.member.first_name} {r.child.member.last_name}"
        if r.bike_id:
            rental_map[r.bike_id] = renter

    items_all = Item.query.order_by(Item.created_at.desc()).all()
    def norm_item_status(s):
        s = (s or '').strip().lower()
        mapping = {
            'beschikbaar': 'available',
            'onbeschikbaar': 'unavailable',
            'verhuurd': 'rented',
            'in herstelling': 'repair'
        }
        return mapping.get(s, s)

    available_items = [i for i in items_all if norm_item_status(i.status) == 'available']
    rented_items = [i for i in items_all if norm_item_status(i.status) in {'unavailable', 'rented'}]
    repair_items = [i for i in items_all if norm_item_status(i.status) == 'repair']
    item_rental_map = {}

    return render_template(
        'inventory.html',
        available_bikes=available_bikes,
        rented_bikes=rented_bikes,
        repair_bikes=repair_bikes,
        rental_map=rental_map,
        available_items=available_items,
        rented_items=rented_items,
        repair_items=repair_items,
        item_rental_map=item_rental_map,
        items_all=items_all
    )

# -----------------------
# Password reset (simplified placeholder)
# -----------------------

@main.route('/password-reset', methods=['GET','POST'])
def password_reset():
    if request.method == 'POST':
        email = request.form.get('email','')
        flash('We hebben een reset-link gemaild indien het adres bestaat.', 'info')
        return redirect(url_for('main.login'))
    return render_template('password_reset.html')

# -----------------------
# Language selection
# -----------------------

@main.route('/lang/<lang_code>')
def set_language(lang_code):
    if lang_code not in ['nl', 'fr']:
        lang_code = 'nl'
    session['lang'] = lang_code
    next_url = request.args.get('next') or url_for('main.home')
    return redirect(next_url)

# -----------------------
# Auth (simple session)
# -----------------------

def login_required(view):
    def wrapper(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('main.login'))
        return view(*args, **kwargs)
    wrapper.__name__ = view.__name__
    return wrapper


@main.route('/login', methods=['GET', 'POST'])
def login():
    """
    Login route met rolgebaseerde authenticatie.
    Ondersteunt Finance Manager en Depot Manager rollen.
    """
    # Seed default users if database is empty
    if not User.query.first():
        # Create default Depot Manager
        depot_mgr = User(
            first_name='Depot',
            last_name='Manager',
            email='depot@opwielekes.be',
            role='depot_manager'
        )
        depot_mgr.set_password('depot123')
        
        # Create default Finance Manager
        finance_mgr = User(
            first_name='Finance',
            last_name='Manager',
            email='finance@opwielekes.be',
            role='finance_manager'
        )
        finance_mgr.set_password('finance123')
        
        # Create default Admin
        admin = User(
            first_name='Admin',
            last_name='User',
            email='admin@opwielekes.be',
            role='admin'
        )
        admin.set_password('admin123')
        
        db.session.add_all([depot_mgr, finance_mgr, admin])
        db.session.commit()
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        # Validatie: email en wachtwoord verplicht
        if not email or not password:
            flash('Vul alle velden in.', 'error')
            return render_template('login.html')
        
        # Zoek gebruiker
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            # Inloggen geslaagd - sla gebruikersgegevens op in sessie
            session['user_id'] = user.user_id
            session['user_role'] = user.role
            session['user_name'] = f"{user.first_name} {user.last_name}"
            session['user_email'] = user.email
            
            flash(f'Welkom, {user.first_name}!', 'success')
            
            # Iedereen gaat naar dashboard
            return redirect(url_for('main.dashboard'))
        else:
            flash('Ongeldige inloggegevens.', 'error')
    
    return render_template('login.html')


@main.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.home'))

# -----------------------
# Member management (Depot manager)
# -----------------------

@main.route('/members')
@login_required
@depot_access_required
def members_list():
    # Build a combined view: ORM + optional public tables (if present)
    all_members = Member.query.order_by(Member.last_name.asc(), Member.first_name.asc()).all()
    combined = list(all_members)
    try:
        from types import SimpleNamespace
        with db.engine.begin() as conn:
            for table_name in ['public."Members"', 'public."Member"']:
                try:
                    rows = conn.execute(text(f'SELECT member_id, first_name, last_name, email, phone, address, last_payment, status FROM {table_name} ORDER BY last_name, first_name')).mappings().all()
                    for r in rows:
                        combined.append(SimpleNamespace(
                            member_id=r.get('member_id'),
                            first_name=r.get('first_name'),
                            last_name=r.get('last_name'),
                            email=r.get('email'),
                            phone=r.get('phone'),
                            address=r.get('address'),
                            last_payment=r.get('last_payment'),
                            status=r.get('status'),
                            children=[]
                        ))
                except Exception:
                    continue
    except Exception:
        pass
    # De-duplicate by (member_id or email+phone)
    seen_ids = set()
    seen_keys = set()
    unique_members = []
    for m in combined:
        mid = getattr(m, 'member_id', None)
        key = (getattr(m, 'email', '') or '').lower(), (getattr(m, 'phone', '') or '').strip()
        if mid and mid in seen_ids:
            continue
        if key in seen_keys:
            continue
        if mid:
            seen_ids.add(mid)
        seen_keys.add(key)
        unique_members.append(m)
    all_members = unique_members
    # Normalize statuses (nl -> en) for grouping
    def norm_status(s):
        s = (s or '').strip().lower()
        mapping = {'actief':'active','inactief':'inactive','gepauzeerd':'inactive'}
        return mapping.get(s, s if s in {'active','inactive'} else 'active')

    # Group as plain Member objects for templates
    # Rules: 'actief' => active, 'inactief' or 'gepauzeerd' => inactive, anything else or empty => active
    def is_active_member(m):
        s = (getattr(m, 'status', '') or '').strip().lower()
        return s in {'active', 'actief', ''}
    def is_inactive_member(m):
        s = (getattr(m, 'status', '') or '').strip().lower()
        return s in {'inactive', 'inactief', 'gepauzeerd', 'paused'}

    active_members = [m for m in all_members if is_active_member(m)]
    inactive_members = [m for m in all_members if is_inactive_member(m)]

    # Safety fallback: if both groups are empty but there are members, show all as active
    if not active_members and not inactive_members and all_members:
        active_members = all_members

    return render_template('members.html', active_members=active_members, inactive_members=inactive_members, today=date.today())


@main.route('/members/<member_id>/children', methods=['GET'])
@login_required
@depot_access_required
def members_children(member_id):
    member = Member.query.get_or_404(member_id)
    children = Child.query.filter_by(member_id=member.member_id).all()
    # Map active rentals per child
    active_rentals = {r.child_id: r for r in Rental.query.filter_by(status='active').all()}
    # Available bikes to assign
    available_bikes = Bike.query.filter_by(status='available', archived=False).order_by(Bike.created_at.desc()).all()
    return render_template('children.html', member=member, children=children, active_rentals=active_rentals, available_bikes=available_bikes)


@main.route('/members/<member_id>/children/add', methods=['POST'])
@login_required
@depot_access_required
def members_children_add(member_id):
    member = Member.query.get_or_404(member_id)
    fn = (request.form.get('first_name') or '').strip()
    ln = (request.form.get('last_name') or '').strip()
    if fn or ln:
        db.session.add(Child(member_id=member.member_id, first_name=fn or '-', last_name=ln or '-'))
        db.session.commit()
    return redirect(url_for('main.members_children', member_id=member.member_id))


@main.route('/members/<member_id>/children/<child_id>/assign', methods=['POST'])
@login_required
@depot_access_required
def members_children_assign(member_id, child_id):
    member = Member.query.get_or_404(member_id)
    child = Child.query.get_or_404(child_id)
    bike_id = request.form.get('bike_id')
    bike = Bike.query.get_or_404(bike_id)
    # Only allow assigning available bikes
    if bike.archived or bike.status != 'available':
        flash('Fiets niet beschikbaar', 'error')
        return redirect(url_for('main.members_children', member_id=member.member_id))
    rental = Rental(bike_id=bike.bike_id, member_id=member.member_id, child_id=child.child_id)
    db.session.add(rental)
    bike.status = 'rented'
    db.session.commit()
    return redirect(url_for('main.members_children', member_id=member.member_id))


@main.route('/rentals')
@login_required
@finance_access_required
def rentals_list():
    """Rentals overview page with filters"""
    from sqlalchemy import func
    from datetime import timedelta
    
    # Calculate date for overdue payments (30 days ago)
    thirty_days_ago = date.today() - timedelta(days=30)
    
    # Get filter parameters
    status_filter = request.args.get('status', 'all')
    bike_type = request.args.get('bike_type', '')
    search_query = request.args.get('search', '').strip()
    
    # Base query with joins
    query = db.session.query(
        Rental,
        Bike,
        Child,
        Member
    ).join(Bike, Rental.bike_id == Bike.bike_id)\
     .join(Child, Rental.child_id == Child.child_id)\
     .join(Member, Child.member_id == Member.member_id)
    
    # Apply status filter
    if status_filter == 'active':
        query = query.filter(Rental.status == 'active')
    elif status_filter == 'returned':
        query = query.filter(Rental.status == 'returned')
    
    # Apply bike type filter
    if bike_type:
        query = query.filter(Bike.type == bike_type)
    
    # Apply search filter
    if search_query:
        search_pattern = f'%{search_query}%'
        query = query.filter(
            (Child.first_name.ilike(search_pattern)) |
            (Child.last_name.ilike(search_pattern)) |
            (Member.first_name.ilike(search_pattern)) |
            (Member.last_name.ilike(search_pattern))
        )
    
    # Get results
    rentals_data = query.order_by(Rental.start_date.desc()).all()
    
    # Calculate stats - simple counts
    total_active = db.session.query(func.count(Rental.rental_id))\
        .filter(Rental.status == 'active').scalar() or 0
    
    total_returned = db.session.query(func.count(Rental.rental_id))\
        .filter(Rental.status == 'returned').scalar() or 0
    
    # Calculate overdue in Python to avoid SQL issues
    overdue_count = 0
    for rental, bike, child, member in rentals_data:
        if rental.status == 'active' and member.last_payment:
            days_since_payment = (date.today() - member.last_payment).days
            if days_since_payment > 30:
                overdue_count += 1
    
    # Get unique bike types for filter
    bike_types = db.session.query(Bike.type)\
        .filter(Bike.type.isnot(None))\
        .distinct()\
        .order_by(Bike.type)\
        .all()
    bike_types = [t[0] for t in bike_types if t[0]]
    
    return render_template('rentals.html',
        rentals_data=rentals_data,
        total_active=total_active,
        total_returned=total_returned,
        overdue_count=overdue_count,
        bike_types=bike_types,
        status_filter=status_filter,
        bike_type=bike_type,
        search_query=search_query,
        now=date.today(),
        thirty_days_ago=thirty_days_ago
    )

# New rental creation page
@main.route('/rentals/new', methods=['GET','POST'])
@login_required
@depot_access_required
def rental_new():
    if request.method == 'POST':
        member_id = request.form.get('member_id')
        bike_id = request.form.get('bike_id')
        child_id = request.form.get('child_id') or None
        start_date_raw = request.form.get('start_date')
        end_date_raw = request.form.get('end_date')
        # Safe parse ISO dates (yyyy-mm-dd); fallback to today/None
        start_date = None
        end_date = None
        try:
            start_date = date.fromisoformat(start_date_raw) if start_date_raw else date.today()
        except Exception:
            start_date = date.today()
        try:
            end_date = date.fromisoformat(end_date_raw) if end_date_raw else None
        except Exception:
            end_date = None

        bike = Bike.query.get_or_404(bike_id)
        if bike.archived or (bike.status or '').lower() != 'available':
            flash('Geselecteerde fiets is niet beschikbaar.', 'error')
            return redirect(url_for('main.rental_new'))

        rental = Rental(bike_id=bike.bike_id, member_id=member_id, child_id=child_id, start_date=start_date, end_date=end_date)
        db.session.add(rental)
        bike.status = 'rented'
        db.session.commit()
        flash('Verhuring aangemaakt.', 'success')
        return redirect(url_for('main.rentals_list'))

    members = Member.query.order_by(Member.last_name.asc(), Member.first_name.asc()).all()
    available_bikes = Bike.query.filter_by(status='available', archived=False).order_by(Bike.created_at.desc()).all()
    # Children list can be filtered client-side when a member is selected; provide all with member mapping
    children = Child.query.all()
    return render_template('rent_new.html', members=members, available_bikes=available_bikes, children=children, today=date.today().strftime('%Y-%m-%d'))


# Simple in-memory cache for dashboard data to reduce load
_dashboard_cache = {
    'timestamp': None,
    'data': None
}

@main.route('/dashboard')
@login_required
def dashboard():
    from time import perf_counter
    t0 = perf_counter()
    # Serve cached data for up to 30 seconds to avoid heavy recomputation
    try:
        from datetime import datetime, timedelta
        if _dashboard_cache['timestamp'] and _dashboard_cache['data']:
            if datetime.utcnow() - _dashboard_cache['timestamp'] < timedelta(seconds=30):
                ctx = _dashboard_cache['data']
                ctx['now'] = date.today()  # update volatile value
                return render_template('dashboard.html', **ctx)
    except Exception:
        # If cache fails, continue without cache
        pass
    from datetime import timedelta
    from sqlalchemy import func, and_, case, desc
    
    today = date.today()
    month_start = today.replace(day=1)
    thirty_days_ago = today - timedelta(days=30)
    seven_days_ago = today - timedelta(days=7)
    tomorrow = today + timedelta(days=1)
    
    # === CARD 1: Totale fietsen (uitgebreid) ===
    total_bikes = Bike.query.filter_by(archived=False).count()
    available_bikes_count = Bike.query.filter_by(status='available', archived=False).count()
    rented_bikes_count = Bike.query.filter_by(status='rented', archived=False).count()
    repair_bikes_count = Bike.query.filter_by(status='repair', archived=False).count()
    # Missing/lost bikes placeholder (would need a new status field)
    missing_bikes_count = 0
    new_bikes_today = Bike.query.filter(
        Bike.archived == False,
        func.date(Bike.created_at) == today
    ).count()
    
    # === CARD 2: Actieve leden (uitgebreid) ===
    total_members = Member.query.count()
    active_members_count = Member.query.filter_by(status='active').count()
    new_members_this_month = Member.query.filter(
        func.date(Member.created_at) >= month_start
    ).count()
    
    # Members with overdue payments
    one_year_ago = today - timedelta(days=365)
    overdue_members_count = Member.query.filter(
        Member.status == 'active',
        db.or_(
            Member.last_payment == None,
            Member.last_payment < one_year_ago
        )
    ).count()
    
    # === CARD 3: Kinderen ===
    total_children = Child.query.count()
    new_children_this_month = Child.query.join(Member).filter(
        func.date(Child.created_at) >= month_start if hasattr(Child, 'created_at') else True
    ).count() if hasattr(Child, 'created_at') else 0
    
    # Children without assigned bike (no active rental)
    children_with_rental = db.session.query(Rental.child_id).filter(
        Rental.status == 'active',
        Rental.child_id != None
    ).distinct().subquery()
    children_without_bike = Child.query.filter(
        ~Child.child_id.in_(db.session.query(children_with_rental))
    ).count()
    
    # === CARD 4: Betalingen (uitgebreid) ===
    payments_this_month = db.session.query(func.sum(Payment.amount)).filter(
        func.date(Payment.paid_at) >= month_start
    ).scalar() or 0
    
    # Total payments count this month
    payments_count_this_month = Payment.query.filter(
        func.date(Payment.paid_at) >= month_start
    ).count()
    
    # Payments today
    payments_today = db.session.query(func.sum(Payment.amount)).filter(
        func.date(Payment.paid_at) == today
    ).scalar() or 0
    
    payments_count_today = Payment.query.filter(
        func.date(Payment.paid_at) == today
    ).count()
    
    # Payment method breakdown this month
    cash_payments = db.session.query(func.sum(Payment.amount)).filter(
        func.date(Payment.paid_at) >= month_start,
        Payment.method == 'cash'
    ).scalar() or 0
    
    card_payments = db.session.query(func.sum(Payment.amount)).filter(
        func.date(Payment.paid_at) >= month_start,
        Payment.method == 'card'
    ).scalar() or 0
    
    bank_payments = db.session.query(func.sum(Payment.amount)).filter(
        func.date(Payment.paid_at) >= month_start,
        Payment.method == 'bank_transfer'
    ).scalar() or 0
    
    # Outstanding amount (mock - would need better tracking)
    overdue_amount = overdue_members_count * 10  # placeholder €10 per member
    
    # Last payment
    last_payment = Payment.query.order_by(Payment.paid_at.desc()).first()
    
    # === CARD 5: Verhuringen (uitgebreid) ===
    active_rentals_count = Rental.query.filter_by(status='active').count()
    
    # Rentals started today
    rentals_today = Rental.query.filter(
        func.date(Rental.start_date) == today
    ).count()
    
    # Rentals ended today
    returns_today = Rental.query.filter(
        func.date(Rental.end_date) == today,
        Rental.status == 'returned'
    ).count()
    
    # Rentals due tomorrow (if we tracked due dates - placeholder)
    rentals_due_tomorrow = 0
    
    # === CARD 4: Reparaties ===
    bikes_in_repair = repair_bikes_count
    # Average repair time (mock for now - would need repair history)
    avg_repair_days = 7  # placeholder
    
    # === CHART DATA: Rental activity (last 7 days) ===
    rental_chart_labels = []
    rental_chart_rentals = []
    rental_chart_returns = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        rental_chart_labels.append(day.strftime('%d/%m'))

        # Rentals started on this day (use start_date for accuracy)
        rentals_count = Rental.query.filter(
            Rental.start_date == day
        ).count()
        rental_chart_rentals.append(rentals_count)

        # Returns on this day (end_date = day and status returned)
        returns_count = Rental.query.filter(
            Rental.end_date == day,
            Rental.status == 'returned'
        ).count()
        rental_chart_returns.append(returns_count)
    
    # === CHART DATA: Member activity (pie chart) ===
    inactive_members = Member.query.filter_by(status='inactive').count()
    paused_members = Member.query.filter_by(status='paused').count()
    new_members_last_30 = Member.query.filter(
        func.date(Member.created_at) >= thirty_days_ago
    ).count()
    
    member_pie_labels = ['Actief', 'Inactief', 'Gepauzeerd', 'Nieuw (30d)']
    member_pie_values = [active_members_count, inactive_members, paused_members, new_members_last_30]
    
    # === BIKE CATEGORIES (normalized, title-cased, with repair) ===
    bikes_all = Bike.query.filter_by(archived=False).all()
    bike_cat_map = {}
    for b in bikes_all:
        raw = (b.type or 'Onbekend').strip()
        key = raw.lower()
        name = raw.title()
        if key not in bike_cat_map:
            bike_cat_map[key] = {'name': name, 'total': 0, 'available': 0, 'rented': 0, 'repair': 0}
        cat = bike_cat_map[key]
        cat['total'] += 1
        status = (b.status or '').strip().lower()
        if status == 'available':
            cat['available'] += 1
        elif status == 'rented':
            cat['rented'] += 1
        elif status == 'repair':
            cat['repair'] += 1
    bike_categories = list(bike_cat_map.values())

    # === ITEM CATEGORIES (normalized, title-cased, with repair) ===
    items_all = Item.query.all()
    item_cat_map = {}
    def norm_item_status(s):
        s = (s or '').strip().lower()
        mapping = {
            'beschikbaar': 'available',
            'onbeschikbaar': 'unavailable',
            'verhuurd': 'rented',
            'in herstelling': 'repair'
        }
        return mapping.get(s, s)
    for i in items_all:
        raw = (i.type or 'Onbekend').strip()
        key = raw.lower()
        name = raw.title()
        if key not in item_cat_map:
            item_cat_map[key] = {'name': name, 'total': 0, 'available': 0, 'rented': 0, 'repair': 0}
        cat = item_cat_map[key]
        cat['total'] += 1
        status = norm_item_status(i.status)
        if status == 'available':
            cat['available'] += 1
        elif status in {'rented', 'unavailable'}:
            cat['rented'] += 1
        elif status == 'repair':
            cat['repair'] += 1
    item_categories = list(item_cat_map.values())
    
    # === ALERTS / TO-DO ===
    alerts = []
    
    # Overdue payments
    if overdue_members_count > 0:
        alerts.append({
            'type': 'warning',
            'icon': '💳',
            'message': f'{overdue_members_count} lid(en) met achterstallige betaling'
        })
    
    # Long-term rentals (> 90 days)
    ninety_days_ago = today - timedelta(days=90)
    long_rentals = Rental.query.filter(
        Rental.status == 'active',
        Rental.start_date < ninety_days_ago
    ).count()
    if long_rentals > 0:
        alerts.append({
            'type': 'info',
            'icon': '⏰',
            'message': f'{long_rentals} fiets(en) langer dan 90 dagen uitgeleend'
        })
    
    # Bikes in repair
    if bikes_in_repair > 0:
        alerts.append({
            'type': 'danger',
            'icon': '🔧',
            'message': f'{bikes_in_repair} fiets(en) in onderhoud'
        })
    
    # === RECENT ACTIVITY ===
    recent_activity = []
    
    # Recent rentals
    recent_rentals_raw = Rental.query.order_by(Rental.created_at.desc()).limit(3).all()
    for r in recent_rentals_raw:
        renter_name = ''
        if r.member:
            renter_name = f'{r.member.first_name} {r.member.last_name}'
        elif r.child:
            renter_name = f'{r.child.first_name} {r.child.last_name}'
        
        recent_activity.append({
            'type': 'rental',
            'icon': '🚲',
            'title': f'Verhuur: {r.bike.name if r.bike else "Onbekend"}',
            'subtitle': f'Aan {renter_name}',
            'time': r.created_at
        })
    
    # Recent members
    recent_members_raw = Member.query.order_by(Member.created_at.desc()).limit(2).all()
    for m in recent_members_raw:
        recent_activity.append({
            'type': 'member',
            'icon': '👤',
            'title': f'Nieuw lid: {m.first_name} {m.last_name}',
            'subtitle': m.email or m.phone or '',
            'time': m.created_at
        })
    
    # Recent payments
    recent_payments = Payment.query.order_by(Payment.created_at.desc()).limit(2).all()
    for p in recent_payments:
        member = Member.query.get(p.member_id)
        recent_activity.append({
            'type': 'payment',
            'icon': '💳',
            'title': f'Betaling ontvangen: €{p.amount:.2f}',
            'subtitle': f'{member.first_name} {member.last_name}' if member else '',
            'time': p.created_at
        })
    
    # Sort all activity by time
    recent_activity.sort(key=lambda x: x['time'], reverse=True)
    recent_activity = recent_activity[:8]  # Top 8
    
    # === INVENTORY BAR CHART DATA ===
    inventory_chart_labels = [cat['name'] for cat in bike_categories]
    inventory_chart_available = [cat['available'] for cat in bike_categories]
    inventory_chart_rented = [cat['rented'] for cat in bike_categories]
    
    # === TO-DO LIST ITEMS ===
    todo_items = []
    
    # Overdue payments
    if overdue_members_count > 0:
        overdue_list = Member.query.filter(
            Member.status == 'active',
            db.or_(Member.last_payment == None, Member.last_payment < one_year_ago)
        ).limit(5).all()
        for m in overdue_list:
            days_overdue = (today - m.last_payment).days if m.last_payment else 365
            todo_items.append({
                'type': 'payment',
                'priority': 'high',
                'title': f'{m.first_name} {m.last_name}',
                'message': f'Betaling {days_overdue} dagen achterstallig'
            })
    
    # Long rentals (> 7 days)
    long_rentals_list = Rental.query.filter(
        Rental.status == 'active',
        Rental.start_date < seven_days_ago
    ).limit(5).all()
    for r in long_rentals_list:
        days = (today - r.start_date).days
        renter = r.member.first_name if r.member else r.child.first_name if r.child else 'Onbekend'
        todo_items.append({
            'type': 'rental',
            'priority': 'medium',
            'title': f'{r.bike.name if r.bike else "Fiets"}',
            'message': f'{days} dagen uit bij {renter}'
        })
    
    # Bikes in repair
    repair_list = Bike.query.filter_by(status='repair', archived=False).limit(3).all()
    for bike in repair_list:
        todo_items.append({
            'type': 'repair',
            'priority': 'medium',
            'title': bike.name,
            'message': 'In reparatie'
        })
    
    # Children without bike
    if children_without_bike > 0:
        children_list = Child.query.filter(
            ~Child.child_id.in_(db.session.query(children_with_rental))
        ).limit(3).all()
        for child in children_list:
            todo_items.append({
                'type': 'child',
                'priority': 'low',
                'title': f'{child.first_name} {child.last_name}',
                'message': 'Geen actieve fiets'
            })
    
    # === POPULAR MODELS (Most rented) ===
    popular_models = db.session.query(
        Bike.type,
        func.count(Rental.rental_id).label('rental_count')
    ).join(Rental, Bike.bike_id == Rental.bike_id)\
     .group_by(Bike.type)\
     .order_by(desc('rental_count'))\
     .limit(5).all()
    
    popular_models_list = [{'name': m.type or 'Onbekend', 'count': m.rental_count} for m in popular_models]
    
    # === REPAIR INSIGHTS ===
    repair_stats = {
        'total_in_repair': repair_bikes_count,
        'avg_repair_time': 7,  # placeholder
        'bikes': Bike.query.filter_by(status='repair', archived=False).limit(5).all()
    }
    
    # === BIKES WITHOUT RENTAL IN 30+ DAYS ===
    thirty_days_rentals = db.session.query(Rental.bike_id).filter(
        Rental.created_at >= thirty_days_ago
    ).distinct().subquery()
    
    unused_bikes = Bike.query.filter(
        Bike.archived == False,
        ~Bike.bike_id.in_(db.session.query(thirty_days_rentals))
    ).limit(10).all()
    
    # === PAYMENT INSIGHTS (Weekly) ===
    # Weekly payments for chart (last 8 weeks)
    payment_weeks = []
    payment_amounts = []
    # Determine start of current week (Monday)
    start_of_week = today - timedelta(days=today.weekday())
    for i in range(7, -1, -1):
        week_start = start_of_week - timedelta(weeks=i)
        week_end = week_start + timedelta(days=7)
        amount = db.session.query(func.sum(Payment.amount)).filter(
            Payment.paid_at >= week_start,
            Payment.paid_at < week_end
        ).scalar() or 0
        payment_weeks.append(f"{week_start.strftime('%d/%m')} - {(week_end - timedelta(days=1)).strftime('%d/%m')}")
        payment_amounts.append(float(amount))
    
    # Biggest debtors
    top_debtors = Member.query.filter(
        Member.status == 'active',
        db.or_(Member.last_payment == None, Member.last_payment < one_year_ago)
    ).order_by(Member.last_payment.asc().nullsfirst()).limit(5).all()
    
    # === RENTAL HEATMAP DATA (by hour - mock) ===
    rental_hours = [0] * 24
    hourly_rentals = db.session.query(
        func.extract('hour', Rental.created_at).label('hour'),
        func.count(Rental.rental_id).label('count')
    ).group_by('hour').all()
    for hr in hourly_rentals:
        if hr.hour is not None:
            rental_hours[int(hr.hour)] = hr.count
    
    # === RENTAL DURATION STATS ===
    completed_rentals = Rental.query.filter(
        Rental.status == 'returned',
        Rental.end_date != None
    ).all()
    
    if completed_rentals:
        durations = [(r.end_date - r.start_date).days for r in completed_rentals if r.start_date and r.end_date]
        avg_rental_duration = sum(durations) / len(durations) if durations else 0
    else:
        avg_rental_duration = 0
    
    # === ACHIEVEMENTS ===
    achievements = []
    
    # Rentals this month
    rentals_this_month = Rental.query.filter(
        func.date(Rental.created_at) >= month_start
    ).count()
    if rentals_this_month >= 50:
        achievements.append({'icon': '🏆', 'text': f'{rentals_this_month} verhuringen deze maand'})
    
    # All payments up to date
    if overdue_members_count == 0:
        achievements.append({'icon': '💯', 'text': '100% betalingen up-to-date'})
    
    # No bikes in repair
    if repair_bikes_count == 0:
        achievements.append({'icon': '✅', 'text': 'Alle fietsen operationeel'})
    
    # Calculate percentages
    active_member_percentage = round((active_members_count / total_members * 100) if total_members > 0 else 0, 1)
    bike_availability_percentage = round((available_bikes_count / total_bikes * 100) if total_bikes > 0 else 0, 1)
    children_with_bike_percentage = round(((total_children - children_without_bike) / total_children * 100) if total_children > 0 else 0, 1)
    
    ctx = dict(
        # Card 1: Bikes (extended)
        total_bikes=total_bikes,
        available_bikes_count=available_bikes_count,
        rented_bikes_count=rented_bikes_count,
        repair_bikes_count=repair_bikes_count,
        missing_bikes_count=missing_bikes_count,
        new_bikes_today=new_bikes_today,
        bike_availability_percentage=bike_availability_percentage,
        # Card 2: Members (extended)
        active_members_count=active_members_count,
        total_members=total_members,
        new_members_this_month=new_members_this_month,
        overdue_members_count=overdue_members_count,
        active_member_percentage=active_member_percentage,
        # Card 3: Children (NEW)
        total_children=total_children,
        new_children_this_month=new_children_this_month,
        children_without_bike=children_without_bike,
        children_with_bike_percentage=children_with_bike_percentage,
        # Card 4: Payments (extended)
        payments_this_month=payments_this_month,
        payments_count_this_month=payments_count_this_month,
        payments_today=payments_today,
        payments_count_today=payments_count_today,
        cash_payments=cash_payments,
        card_payments=card_payments,
        bank_payments=bank_payments,
        overdue_members=overdue_members_count,
        overdue_amount=overdue_amount,
        last_payment=last_payment,
        # Card 5: Rentals (NEW)
        active_rentals_count=active_rentals_count,
        rentals_today=rentals_today,
        returns_today=returns_today,
        rentals_due_tomorrow=rentals_due_tomorrow,
        # Charts
        rental_chart_labels=rental_chart_labels,
        rental_chart_rentals=rental_chart_rentals,
        rental_chart_returns=rental_chart_returns,
        member_pie_labels=member_pie_labels,
        member_pie_values=member_pie_values,
        inventory_chart_labels=inventory_chart_labels,
        inventory_chart_available=inventory_chart_available,
        inventory_chart_rented=inventory_chart_rented,
        payment_weeks=payment_weeks,
        payment_amounts=payment_amounts,
        # Categories
        bike_categories=bike_categories,
        item_categories=item_categories,
        # To-do list
        todo_items=todo_items,
        # Popular models
        popular_models=popular_models_list,
        # Repair insights
        repair_stats=repair_stats,
        # Unused bikes
        unused_bikes=unused_bikes,
        # Top debtors
        top_debtors=top_debtors,
        # Rental heatmap
        rental_hours=rental_hours,
        # Rental duration
        avg_rental_duration=avg_rental_duration,
        # Achievements
        achievements=achievements,
        # Recent activity
        recent_activity=recent_activity,
        # Current datetime for debtors calculation
        now=today
    )

    # Store cache safely
    try:
        from datetime import datetime
        _dashboard_cache['timestamp'] = datetime.utcnow()
        _dashboard_cache['data'] = ctx.copy()
    except Exception:
        pass

    t1 = perf_counter()
    ctx['render_time_ms'] = int((t1 - t0) * 1000)
    return render_template('dashboard.html', **ctx)


@main.route('/members/new', methods=['GET', 'POST'])
@login_required
@depot_access_required
def members_new():
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        street = request.form.get('street','').strip()
        house_number = request.form.get('house_number','').strip()
        postcode = request.form.get('postcode','').strip()
        city = request.form.get('city','').strip()
        address = ''
        if street or house_number or postcode or city:
            left = ' '.join([street, house_number]).strip()
            right = ' '.join([postcode, city]).strip()
            address = ', '.join([p for p in [left, right] if p])
        last_payment_raw = request.form.get('last_payment')
        raw_status = (request.form.get('status', 'active') or 'active').strip().lower()
        status_map = {'actief':'active','inactief':'inactive','gepauzeerd':'paused'}
        status = status_map.get(raw_status, raw_status if raw_status in {'active','inactive','paused'} else 'active')

        last_payment = None
        if last_payment_raw:
            try:
                last_payment = datetime.strptime(last_payment_raw, '%Y-%m-%d').date()
            except ValueError:
                last_payment = None

        member = Member(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            address=address,
            street=street or None,
            house_number=house_number or None,
            postcode=postcode or None,
            city=city or None,
            last_payment=last_payment,
            status=status,
        )
        db.session.add(member)
        db.session.flush()  # ensure member_id for children

        # Children arrays
        c_first = request.form.getlist('child_first_name[]')
        c_last = request.form.getlist('child_last_name[]')
        for fn, ln in zip(c_first, c_last):
            fn, ln = fn.strip(), ln.strip()
            if fn or ln:
                db.session.add(Child(member_id=member.member_id, first_name=fn or '-', last_name=ln or '-'))

        # Mirror this member into Supabase public.Users (best-effort, isolated from the current transaction)
        # Use a separate engine connection so any error here doesn't poison the active ORM session.
        try:
            with db.engine.begin() as conn:
                try:
                    # Prefer table "Users" (common naming in Supabase)
                    conn.execute(
                        text('INSERT INTO public."Users" (first_name, last_name, email) VALUES (:fn, :ln, :em)'),
                        {"fn": first_name, "ln": last_name, "em": email or None}
                    )
                except Exception as e1:
                    try:
                        # Fallback to table "User" if your schema uses that name
                        conn.execute(
                            text('INSERT INTO public."User" (first_name, last_name, email) VALUES (:fn, :ln, :em)'),
                            {"fn": first_name, "ln": last_name, "em": email or None}
                        )
                    except Exception as e2:
                        print(f"Supabase mirror insert failed (non-blocking): {e1} / {e2}")
        except Exception as e:
            # Any unexpected engine/connection error — keep non-blocking
            print(f"Supabase mirror engine error (non-blocking): {e}")

        db.session.commit()
        return redirect(url_for('main.members_list'))

    return render_template('member_form.html', mode='new', member=None, member_statuses=MEMBER_STATUSES)


@main.route('/members/<member_id>/edit', methods=['GET', 'POST'])
@login_required
@depot_access_required
def members_edit(member_id):
    member = Member.query.get_or_404(member_id)
    if request.method == 'POST':
        member.first_name = request.form.get('first_name', '').strip()
        member.last_name = request.form.get('last_name', '').strip()
        member.email = request.form.get('email', '').strip()
        member.phone = request.form.get('phone', '').strip()
        street = request.form.get('street','').strip()
        house_number = request.form.get('house_number','').strip()
        postcode = request.form.get('postcode','').strip()
        city = request.form.get('city','').strip()
        # Persist fields
        member.street = street or None
        member.house_number = house_number or None
        member.postcode = postcode or None
        member.city = city or None
        if street or house_number or postcode or city:
            left = ' '.join([street, house_number]).strip()
            right = ' '.join([postcode, city]).strip()
            member.address = ', '.join([p for p in [left, right] if p])
        else:
            member.address = ''
        last_payment_raw = request.form.get('last_payment')
        raw_status = (request.form.get('status', 'active') or 'active').strip().lower()
        status_map = {'actief':'active','inactief':'inactive','gepauzeerd':'paused'}
        status = status_map.get(raw_status, raw_status if raw_status in {'active','inactive','paused'} else 'active')

        if last_payment_raw:
            try:
                member.last_payment = datetime.strptime(last_payment_raw, '%Y-%m-%d').date()
            except ValueError:
                member.last_payment = None
        else:
            member.last_payment = None
        member.status = status

        # Replace children with submitted set (simple approach)
        member.children.clear()
        db.session.flush()
        c_first = request.form.getlist('child_first_name[]')
        c_last = request.form.getlist('child_last_name[]')
        for fn, ln in zip(c_first, c_last):
            fn, ln = fn.strip(), ln.strip()
            if fn or ln:
                db.session.add(Child(member_id=member.member_id, first_name=fn or '-', last_name=ln or '-'))

        db.session.commit()
        return redirect(url_for('main.members_list'))

    return render_template('member_form.html', mode='edit', member=member, member_statuses=MEMBER_STATUSES)


@main.route('/members/<member_id>/status', methods=['POST'])
@login_required
@depot_access_required
def members_status(member_id):
    member = Member.query.get_or_404(member_id)
    raw_status = (request.form.get('status', 'active') or 'active').strip().lower()
    status_map = {'actief':'active','inactief':'inactive','gepauzeerd':'paused'}
    new_status = status_map.get(raw_status, raw_status)
    member.status = new_status if new_status in {'active','inactive','paused'} else 'active'
    db.session.commit()
    return redirect(url_for('main.members_list'))


# -----------------------
# Bikes CRUD and status
# -----------------------

@main.route('/bikes/new', methods=['GET','POST'])
@login_required
@depot_access_required
def bikes_new():
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        btype = request.form.get('type','').strip().lower()
        if btype not in {'elektrisch','gewoon'}:
            btype = 'gewoon'
        status = request.form.get('status','available')
        bike = Bike(name=name or 'Fiets', type=btype, status=status)
        db.session.add(bike)
        db.session.commit()
        return redirect(url_for('main.inventory'))
    return render_template('bike_form.html', mode='new', bike=None, bike_types=BIKE_TYPES, bike_statuses=BIKE_STATUSES)


@main.route('/bikes/<bike_id>/edit', methods=['GET','POST'])
@login_required
@depot_access_required
def bikes_edit(bike_id):
    bike = Bike.query.get_or_404(bike_id)
    if request.method == 'POST':
        bike.name = request.form.get('name','').strip() or bike.name
        _t = request.form.get('type','').strip().lower()
        if _t in {'elektrisch','gewoon'}:
            bike.type = _t
        bike.status = request.form.get('status','available')
        db.session.commit()
        return redirect(url_for('main.inventory'))
    return render_template('bike_form.html', mode='edit', bike=bike, bike_types=BIKE_TYPES, bike_statuses=BIKE_STATUSES)


@main.route('/bikes/<bike_id>/status', methods=['POST'])
@login_required
@depot_access_required
def bikes_status(bike_id):
    bike = Bike.query.get_or_404(bike_id)
    new_status = request.form.get('status','available')
    bike.status = new_status
    db.session.commit()
    return redirect(url_for('main.inventory'))


@main.route('/bikes/<bike_id>/archive', methods=['POST'])
@login_required
@depot_access_required
def bikes_archive(bike_id):
    bike = Bike.query.get_or_404(bike_id)
    bike.archived = True
    db.session.commit()
    return redirect(url_for('main.inventory'))

@main.route('/bikes/<bike_id>/delete', methods=['POST'])
@login_required
@depot_access_required
def bikes_delete(bike_id):
    bike = Bike.query.get_or_404(bike_id)
    # Remove dependent rentals to avoid FK constraint issues
    Rental.query.filter_by(bike_id=bike.bike_id).delete(synchronize_session=False)
    db.session.delete(bike)
    db.session.commit()
    flash('Fiets verwijderd', 'info')
    return redirect(url_for('main.inventory'))


# -----------------------
# Rentals
# -----------------------

@main.route('/rent/<bike_id>', methods=['GET','POST'])
@login_required
@depot_access_required
def rent_bike_action(bike_id):
    bike = Bike.query.get_or_404(bike_id)
    if request.method == 'POST':
        member_id = request.form.get('member_id')
        child_id = request.form.get('child_id') or None
        start_date_raw = request.form.get('start_date')
        start = date.fromisoformat(start_date_raw) if start_date_raw else date.today()
        rental = Rental(bike_id=bike.bike_id, member_id=member_id, child_id=child_id, start_date=start)
        db.session.add(rental)
        bike.status = 'rented'
        db.session.commit()
        return redirect(url_for('main.inventory'))
    members = Member.query.order_by(Member.last_name).all()
    return render_template('rent.html', bike=bike, members=members)

# -----------------------
# Items (generic inventory objects)
# -----------------------

@main.route('/items/new', methods=['GET','POST'])
@login_required
@depot_access_required
def items_new():
    if request.method == 'POST':
        name = request.form.get('name','').strip() or 'Object'
        itype = request.form.get('type','').strip().lower() or 'algemeen'
        raw_status = (request.form.get('status','available') or 'available').strip().lower()
        status_map = {
            'beschikbaar': 'available',
            'onbeschikbaar': 'unavailable',
            'verhuurd': 'rented',
            'in herstelling': 'repair'
        }
        status = status_map.get(raw_status, raw_status if raw_status in {'available','unavailable','rented','repair'} else 'available')
        item = Item(name=name, type=itype, status=status)
        db.session.add(item)
        db.session.commit()
        return redirect(url_for('main.inventory'))
    return render_template('item_form.html', mode='new', item=None, item_statuses=ITEM_STATUSES)

# Unified object creation (Bike or generic Item)
@main.route('/objects/new', methods=['GET','POST'])
@login_required
@depot_access_required
def objects_new():
    if request.method == 'POST':
        # New flexible form: type_category selects 'fiets' or 'object'
        type_category = (request.form.get('type_category') or '').strip().lower()
        name = (request.form.get('name') or '').strip() or 'Object'
        raw_status = (request.form.get('status') or 'available').strip().lower()
        status_map = {
            'beschikbaar': 'available',
            'onbeschikbaar': 'unavailable',
            'verhuurd': 'rented',
            'in herstelling': 'repair'
        }
        status = status_map.get(raw_status, raw_status if raw_status in {'available','unavailable','rented','repair'} else 'available')
        if type_category == 'fiets':
            btype = (request.form.get('bike_specific_type') or 'gewoon').strip().lower()
            bike = Bike(name=name, type=btype in {'gewoon','elektrisch'} and btype or 'gewoon', status=status or 'available')
            db.session.add(bike)
        else:
            extra_type = (request.form.get('object_extra_type') or '').strip().lower() or None
            item = Item(name=name, type=extra_type, status=status or 'available')
            db.session.add(item)
        db.session.commit()
        flash(f"{'Fiets' if type_category == 'fiets' else 'Object'} '{name}' aangemaakt.", 'success')
        return redirect(url_for('main.inventory'))
    return render_template('object_form.html')

@main.route('/items/<item_id>/status', methods=['POST'])
@login_required
@depot_access_required
def items_status(item_id):
    item = Item.query.get_or_404(item_id)
    raw_status = (request.form.get('status','available') or 'available').strip().lower()
    status_map = {
        'beschikbaar': 'available',
        'onbeschikbaar': 'unavailable',
        'verhuurd': 'rented',
        'in herstelling': 'repair'
    }
    item.status = status_map.get(raw_status, raw_status if raw_status in {'available','unavailable','rented','repair'} else 'available')
    db.session.commit()
    return redirect(url_for('main.inventory'))

@main.route('/items/<item_id>/delete', methods=['POST'])
@login_required
@depot_access_required
def items_delete(item_id):
    item = Item.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash('Object verwijderd', 'info')
    return redirect(url_for('main.inventory'))


# -----------------------
# Payments
# -----------------------

@main.route('/members/<member_id>/payment', methods=['GET','POST'])
@login_required
@finance_access_required
def members_payment(member_id):
    member = Member.query.get_or_404(member_id)
    if request.method == 'POST':
        amount = float(request.form.get('amount','0') or 0)
        paid_at_raw = request.form.get('paid_at')
        paid_at = date.fromisoformat(paid_at_raw) if paid_at_raw else date.today()
        payment = Payment(member_id=member.member_id, amount=amount, paid_at=paid_at)
        member.last_payment = paid_at
        db.session.add(payment)
        db.session.commit()
        return redirect(url_for('main.members_list'))
    return render_template('payment_form.html', member=member, payment_methods=PAYMENT_METHODS)

@main.route('/members/<member_id>/delete', methods=['POST'])
@login_required
@depot_access_required
def members_delete(member_id):
    member = Member.query.get_or_404(member_id)
    # Remove dependent rentals and payments first
    Rental.query.filter_by(member_id=member.member_id).delete(synchronize_session=False)
    Payment.query.filter_by(member_id=member.member_id).delete(synchronize_session=False)
    db.session.delete(member)
    db.session.commit()
    flash('Lid verwijderd', 'info')
    return redirect(url_for('main.members_list'))

@main.route('/payments')
@login_required
@finance_access_required
def payments_list():
    """Payments overview page with filters"""
    from sqlalchemy import func
    from datetime import timedelta
    
    # Get filter parameters
    method_filter = request.args.get('method', 'all')
    period_filter = request.args.get('period', 'all')
    search_query = request.args.get('search', '').strip()
    
    # Base query with joins
    query = db.session.query(Payment, Member)\
        .join(Member, Payment.member_id == Member.member_id)
    
    # Apply method filter
    if method_filter != 'all':
        query = query.filter(Payment.method == method_filter)
    
    # Apply period filter
    today = date.today()
    if period_filter == 'today':
        query = query.filter(Payment.paid_at == today)
    elif period_filter == 'week':
        week_start = today - timedelta(days=today.weekday())
        query = query.filter(Payment.paid_at >= week_start)
    elif period_filter == 'month':
        month_start = today.replace(day=1)
        query = query.filter(Payment.paid_at >= month_start)
    
    # Apply search filter
    if search_query:
        search_pattern = f'%{search_query}%'
        query = query.filter(
            (Member.first_name.ilike(search_pattern)) |
            (Member.last_name.ilike(search_pattern))
        )
    
    # Get results
    payments_data = query.order_by(Payment.paid_at.desc()).all()
    
    # Calculate stats - alleen ontvangen betalingen meetellen
    # Voor cash en card: altijd ontvangen (received = True by default)
    # Voor bank: alleen als received = True
    total_payments = db.session.query(func.sum(Payment.amount))\
        .filter(Payment.received == True).scalar() or 0
    
    cash_payments = db.session.query(func.sum(Payment.amount))\
        .filter(Payment.method == 'cash', Payment.received == True).scalar() or 0
    
    card_payments = db.session.query(func.sum(Payment.amount))\
        .filter(Payment.method == 'card', Payment.received == True).scalar() or 0
    
    bank_payments = db.session.query(func.sum(Payment.amount))\
        .filter(Payment.method == 'bank_transfer', Payment.received == True).scalar() or 0
    
    return render_template('payments.html',
        payments_data=payments_data,
        total_payments=total_payments,
        cash_payments=cash_payments,
        card_payments=card_payments,
        bank_payments=bank_payments,
        method_filter=method_filter,
        period_filter=period_filter,
        search_query=search_query
    )

@main.route('/payments/new', methods=['GET', 'POST'])
@login_required
@finance_access_required
def payment_new():
    """New payment form"""
    if request.method == 'POST':
        member_id = request.form.get('member_id')
        amount = float(request.form.get('amount', 0))
        method = request.form.get('method', 'cash')
        paid_at_str = request.form.get('paid_at')
        received = request.form.get('received') == 'true'  # Checkbox waarde
        
        # Voor cash en card is received altijd True, voor bank_transfer hangt het af van checkbox
        if method in ['cash', 'card']:
            received = True
        
        payment = Payment(
            member_id=member_id,
            amount=amount,
            method=method,
            paid_at=datetime.strptime(paid_at_str, '%Y-%m-%d').date() if paid_at_str else date.today(),
            received=received
        )
        
        # Update member's last_payment date
        member = Member.query.get(member_id)
        if member:
            member.last_payment = payment.paid_at
        
        db.session.add(payment)
        db.session.commit()
        flash('Betaling geregistreerd', 'success')
        return redirect(url_for('main.payments_list'))
    
    members = Member.query.filter_by(status='active').order_by(Member.last_name).all()
    return render_template('payment_form_new.html', members=members, today=date.today().strftime('%Y-%m-%d'))

@main.route('/payments/<payment_id>/toggle-received', methods=['POST'])
@login_required
@finance_access_required
def payment_toggle_received(payment_id):
    """Toggle received status for bank transfer payment"""
    payment = Payment.query.get_or_404(payment_id)
    
    # Alleen voor bank transfers
    if payment.method == 'bank_transfer':
        payment.received = not payment.received
        db.session.commit()
        
        if payment.received:
            flash('Betaling gemarkeerd als ontvangen', 'success')
        else:
            flash('Betaling gemarkeerd als niet-ontvangen', 'info')
    
    return redirect(url_for('main.payments_list'))

@main.route('/payments/<payment_id>/delete', methods=['POST'])
@login_required
@finance_access_required
def payment_delete(payment_id):
    """Delete a payment"""
    payment = Payment.query.get_or_404(payment_id)
    db.session.delete(payment)
    db.session.commit()
    flash('Betaling verwijderd', 'info')
    return redirect(url_for('main.payments_list'))

