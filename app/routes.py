from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime, date
from app.extensions import db
from app.models import (
    Member, Child, User, Bike, Rental, Payment, Item,
    MEMBER_STATUSES, BIKE_TYPES, BIKE_STATUSES, ITEM_STATUSES, PAYMENT_METHODS
)
from functools import wraps
from sqlalchemy import func

# Definieer de blueprint
main = Blueprint('main', __name__)

# --- AUTH DECORATORS ---

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Je moet inloggen om deze pagina te bekijken.', 'warning')
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('main.login'))
            
            user = User.query.get(session['user_id'])
            if not user or user.role not in allowed_roles:
                flash('Je hebt geen toegang tot deze pagina.', 'error')
                return redirect(url_for('main.dashboard'))
            
            # Sla rol op in sessie voor templates
            session['user_role'] = user.role
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Shortcuts voor rollen
def depot_access_required(f):
    return role_required('depot_manager', 'admin')(f)

def finance_access_required(f):
    return role_required('finance_manager', 'admin')(f)

# --- HELPER FUNCTIES ---

def _expire_past_due_rentals():
    """Zet verhuringen die verlopen zijn automatisch op 'returned' (best-effort)."""
    try:
        today = date.today()
        overdue = Rental.query.filter(Rental.status == 'active', Rental.end_date < today).all()
        for r in overdue:
            r.status = 'returned'
            if r.bike: r.bike.status = 'available'
        if overdue: db.session.commit()
    except Exception:
        pass

# --- ROUTES ---

@main.route('/')
def home():
    if session.get('user_id'):
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('main.login'))

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.user_id
            session['user_role'] = user.role
            session['user_name'] = f"{user.first_name} {user.last_name}"
            session['show_upcoming_popup'] = True
            flash(f'Welkom, {user.first_name}!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Ongeldige inloggegevens.', 'error')
    
    return render_template('login.html')

@main.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.home'))

@main.route('/password-reset')
def password_reset():
    return render_template('password_reset.html')

@main.route('/lang/<lang_code>')
def set_language(lang_code):
    session['lang'] = lang_code if lang_code in ['nl', 'fr'] else 'nl'
    return redirect(request.args.get('next') or url_for('main.home'))

# --- DASHBOARD ---

@main.route('/dashboard')
@login_required
def dashboard():
    _expire_past_due_rentals()
    from app.services import get_dashboard_stats 
    ctx = get_dashboard_stats()
    return render_template('dashboard.html', **ctx)

@main.route('/api/dashboard/rental-activity')
@login_required
def api_dashboard_rental_activity():
    from app.services import get_rental_activity_data
    return jsonify(get_rental_activity_data())

@main.route('/api/dashboard/upcoming-rentals')
@login_required
def api_dashboard_upcoming_rentals():
    from app.speciaal_algoritme import get_upcoming_rentals_for_popup
    return jsonify(get_upcoming_rentals_for_popup(30))

@main.route('/api/dashboard/upcoming-rentals/ack', methods=['POST'])
@login_required
def api_dashboard_upcoming_rentals_ack():
    session['show_upcoming_popup'] = False
    return jsonify({'ok': True})

@main.route('/api/child/<child_id>/has-active-rental')
@login_required
def api_child_has_active_rental(child_id):
    r = Rental.query.filter_by(child_id=child_id, status='active').first()
    return jsonify({'hasActiveRental': bool(r), 'bikeName': r.bike.name if r and r.bike else None})

# --- INVENTORY (FIETSEN & ITEMS) ---

@main.route('/inventory')
@login_required
@depot_access_required
def inventory():
    _expire_past_due_rentals()
    bikes = Bike.query.filter_by(archived=False).order_by(Bike.created_at.desc()).all()
    items = Item.query.order_by(Item.created_at.desc()).all()
    
    rental_map = {}
    for r in Rental.query.filter_by(status='active').all():
        name = f"{r.member.first_name} {r.member.last_name}" if r.member else "Onbekend"
        if r.bike_id: rental_map[r.bike_id] = name

    return render_template(
        'inventory.html',
        available_bikes=[b for b in bikes if b.status == 'available'],
        rented_bikes=[b for b in bikes if b.status == 'rented'],
        repair_bikes=[b for b in bikes if b.status == 'repair'],
        available_items=[i for i in items if i.status == 'available'],
        rented_items=[i for i in items if i.status in ['rented', 'unavailable']],
        repair_items=[i for i in items if i.status == 'repair'],
        rental_map=rental_map,
        item_rental_map={} 
    )

@main.route('/bikes/new', methods=['GET', 'POST'])
@login_required
@depot_access_required
def bikes_new():
    if request.method == 'POST':
        db.session.add(Bike(
            name=request.form.get('name', 'Fiets').strip(),
            type=request.form.get('type', 'gewoon').strip().lower(),
            status=request.form.get('status', 'available')
        ))
        db.session.commit()
        return redirect(url_for('main.inventory'))
    return render_template('bike_form.html', mode='new', bike=None, bike_types=BIKE_TYPES, bike_statuses=BIKE_STATUSES)

@main.route('/bikes/<bike_id>/edit', methods=['GET', 'POST'])
@login_required
@depot_access_required
def bikes_edit(bike_id):
    bike = Bike.query.get_or_404(bike_id)
    if request.method == 'POST':
        bike.name = request.form.get('name', bike.name).strip()
        bike.type = request.form.get('type', bike.type).strip().lower()
        bike.status = request.form.get('status', bike.status)
        db.session.commit()
        return redirect(url_for('main.inventory'))
    return render_template('bike_form.html', mode='edit', bike=bike, bike_types=BIKE_TYPES, bike_statuses=BIKE_STATUSES)

@main.route('/bikes/<bike_id>/status', methods=['POST'])
@login_required
@depot_access_required
def bikes_status(bike_id):
    bike = Bike.query.get_or_404(bike_id)
    bike.status = request.form.get('status', 'available')
    db.session.commit()
    return redirect(url_for('main.inventory'))

@main.route('/bikes/<bike_id>/delete', methods=['POST'])
@login_required
@depot_access_required
def bikes_delete(bike_id):
    bike = Bike.query.get_or_404(bike_id)
    Rental.query.filter_by(bike_id=bike.bike_id).delete()
    db.session.delete(bike)
    db.session.commit()
    flash('Fiets verwijderd.', 'warning')
    return redirect(url_for('main.inventory'))

@main.route('/objects/new', methods=['GET', 'POST'])
@login_required
@depot_access_required
def objects_new():
    if request.method == 'POST':
        cat = request.form.get('type_category')
        name = request.form.get('name', 'Object').strip()
        status = request.form.get('status', 'available')
        
        if cat == 'fiets':
            db.session.add(Bike(name=name, type=request.form.get('bike_specific_type'), status=status))
        else:
            db.session.add(Item(name=name, type=request.form.get('object_extra_type'), status=status))
        
        db.session.commit()
        return redirect(url_for('main.inventory'))
    return render_template('object_form.html')

@main.route('/items/<item_id>/delete', methods=['POST'])
@login_required
@depot_access_required
def items_delete(item_id):
    db.session.delete(Item.query.get_or_404(item_id))
    db.session.commit()
    return redirect(url_for('main.inventory'))

# --- LEDEN (MEMBERS) ---

@main.route('/members')
@login_required
@depot_access_required
def members_list():
    members = Member.query.order_by(Member.last_name, Member.first_name).all()
    active = [m for m in members if m.status in ['active', 'actief', None]]
    inactive = [m for m in members if m.status not in ['active', 'actief', None]]
    blocked_ids = {r.member_id for r in Rental.query.filter_by(status='active').all() if r.member_id}
    
    return render_template('members.html', active_members=active, inactive_members=inactive, members_sorted=members, today=date.today(), blocked_member_ids=blocked_ids)

@main.route('/members/new', methods=['GET', 'POST'])
@login_required
@depot_access_required
def members_new():
    if request.method == 'POST':
        m = Member(
            first_name=request.form.get('first_name'),
            last_name=request.form.get('last_name'),
            email=request.form.get('email'),
            phone=request.form.get('phone'),
            street=request.form.get('street'),
            house_number=request.form.get('house_number'),
            postcode=request.form.get('postcode'),
            city=request.form.get('city'),
            status=request.form.get('status', 'active')
        )
        parts = [p for p in [m.street, m.house_number, m.postcode, m.city] if p]
        m.address = " ".join(parts)
        
        db.session.add(m)
        db.session.flush() 
        for fn, ln in zip(request.form.getlist('child_first_name[]'), request.form.getlist('child_last_name[]')):
            if fn.strip(): db.session.add(Child(member_id=m.member_id, first_name=fn, last_name=ln))
            
        db.session.commit()
        return redirect(url_for('main.members_list'))
    
    return render_template('member_form.html', mode='new', member=None, member_statuses=MEMBER_STATUSES)

@main.route('/members/<member_id>/edit', methods=['GET', 'POST'])
@login_required
@depot_access_required
def members_edit(member_id):
    m = Member.query.get_or_404(member_id)
    if request.method == 'POST':
        m.first_name = request.form.get('first_name')
        m.last_name = request.form.get('last_name')
        m.email = request.form.get('email')
        m.phone = request.form.get('phone')
        m.street = request.form.get('street')
        m.house_number = request.form.get('house_number')
        m.postcode = request.form.get('postcode')
        m.city = request.form.get('city')
        m.status = request.form.get('status')
        
        parts = [p for p in [m.street, m.house_number, m.postcode, m.city] if p]
        m.address = " ".join(parts)
        
        for child in m.children: db.session.delete(child)
        for fn, ln in zip(request.form.getlist('child_first_name[]'), request.form.getlist('child_last_name[]')):
            if fn.strip(): db.session.add(Child(member_id=m.member_id, first_name=fn, last_name=ln))
            
        db.session.commit()
        return redirect(url_for('main.members_list'))
        
    return render_template('member_form.html', mode='edit', member=m, member_statuses=MEMBER_STATUSES)

@main.route('/members/<member_id>/delete', methods=['POST'])
@login_required
@depot_access_required
def members_delete(member_id):
    if Rental.query.filter((Rental.member_id == member_id) & (Rental.status == 'active')).first():
        flash('Kan lid niet verwijderen met actieve verhuring.', 'error')
        return redirect(url_for('main.members_list'))
        
    m = Member.query.get_or_404(member_id)
    Rental.query.filter_by(member_id=m.member_id).delete()
    Payment.query.filter_by(member_id=m.member_id).delete()
    db.session.delete(m)
    db.session.commit()
    flash('Lid verwijderd.', 'info')
    return redirect(url_for('main.members_list'))

@main.route('/members/<member_id>/children', methods=['GET'])
@login_required
def members_children(member_id):
    member = Member.query.get_or_404(member_id)
    active_rentals = {r.child_id: r for r in Rental.query.filter_by(status='active').all()}
    bikes = Bike.query.filter_by(status='available', archived=False).all()
    return render_template('children.html', member=member, children=member.children, active_rentals=active_rentals, available_bikes=bikes)

@main.route('/members/<member_id>/children/add', methods=['POST'])
@login_required
@depot_access_required
def members_children_add(member_id):
    # Voeg een kind toe aan een lid (eenvoudig formulier vanaf children.html)
    Member.query.get_or_404(member_id)
    first = (request.form.get('first_name') or '').strip()
    last = (request.form.get('last_name') or '').strip()
    if not first:
        flash('Voornaam is verplicht.', 'error')
        return redirect(url_for('main.members_children', member_id=member_id))
    db.session.add(Child(member_id=member_id, first_name=first, last_name=last or ''))
    db.session.commit()
    flash('Kind toegevoegd.', 'success')
    return redirect(url_for('main.members_children', member_id=member_id))

@main.route('/members/<member_id>/children/<child_id>/assign', methods=['POST'])
@login_required
@depot_access_required
def members_children_assign(member_id, child_id):
    if Rental.query.filter_by(child_id=child_id, status='active').first():
        flash('Dit kind heeft al een actieve verhuring.', 'error')
        return redirect(url_for('main.members_children', member_id=member_id))
        
    bike = Bike.query.get_or_404(request.form.get('bike_id'))
    if bike.status != 'available':
        flash('Fiets niet beschikbaar.', 'error')
        return redirect(url_for('main.members_children', member_id=member_id))
        
    db.session.add(Rental(bike_id=bike.bike_id, member_id=member_id, child_id=child_id))
    bike.status = 'rented'
    db.session.commit()
    return redirect(url_for('main.members_children', member_id=member_id))

@main.route('/members/<member_id>/children/<child_id>/delete', methods=['POST'])
@login_required
@depot_access_required
def members_children_delete(member_id, child_id):
    # Server-side guard: blokkeer verwijderen bij actieve verhuring
    if Rental.query.filter_by(child_id=child_id, status='active').first():
        flash('Kan kind niet verwijderen met actieve verhuring.', 'error')
        return redirect(url_for('main.members_children', member_id=member_id))
    ch = Child.query.get_or_404(child_id)
    db.session.delete(ch)
    db.session.commit()
    flash('Kind verwijderd.', 'info')
    return redirect(url_for('main.members_children', member_id=member_id))

# --- VERHURINGEN (RENTALS) ---

@main.route('/rentals')
@login_required
@finance_access_required
def rentals_list():
    _expire_past_due_rentals()
    # FIX: Gebruik outerjoin voor Child en Member zodat verhuringen zonder kind/member niet verdwijnen
    query = db.session.query(Rental, Bike, Child, Member)\
        .join(Bike)\
        .outerjoin(Child, Rental.child_id == Child.child_id)\
        .outerjoin(Member, Rental.member_id == Member.member_id)
    
    status = request.args.get('status', 'all')
    if status != 'all': query = query.filter(Rental.status == status)
    
    rentals = query.order_by(Rental.status, Rental.start_date.desc()).all()
    
    counts = {
        'active': Rental.query.filter_by(status='active').count(),
        'returned': Rental.query.filter_by(status='returned').count()
    }
    
    return render_template('rentals.html', rentals_data=rentals, total_active=counts['active'], total_returned=counts['returned'], bike_types=BIKE_TYPES, status_filter=status, bike_type=request.args.get('bike_type', ''), search_query=request.args.get('search', ''))

@main.route('/rentals/new', methods=['GET', 'POST'])
@main.route('/rent/<bike_id>', methods=['GET', 'POST'])
@login_required
@depot_access_required
def rental_new(bike_id=None):
    if request.method == 'POST':
        bike_id = bike_id or request.form.get('bike_id')
        member_id = request.form.get('member_id')
        child_id = request.form.get('child_id') or None
        
        if child_id and Rental.query.filter_by(child_id=child_id, status='active').first():
            flash('Dit kind heeft al een actieve verhuring.', 'error')
            return redirect(url_for('main.rental_new'))

        bike = Bike.query.get_or_404(bike_id)
        if bike.status != 'available':
            flash('Fiets is niet beschikbaar.', 'error')
            return redirect(url_for('main.inventory'))

        start = date.fromisoformat(request.form.get('start_date')) if request.form.get('start_date') else date.today()
        from datetime import timedelta
        rental = Rental(
            bike_id=bike.bike_id, member_id=member_id, child_id=child_id, 
            start_date=start, end_date=start + timedelta(days=365)
        )
        bike.status = 'rented'
        db.session.add(rental)
        
        amt = float(request.form.get('amount') or 0)
        method = request.form.get('payment_method', 'cash')
        paid = (method in ['cash', 'card']) or (request.form.get('received') == 'true')
        
        pay = Payment(member_id=member_id, amount=amt, method=method, paid_at=start, received=paid)
        db.session.add(pay)
        Member.query.get(member_id).last_payment = start
        
        db.session.commit()
        flash('Verhuring succesvol.', 'success')
        return redirect(url_for('main.rentals_list'))

    context = {
        'members': Member.query.order_by(Member.last_name).all(),
        'available_bikes': Bike.query.filter_by(status='available', archived=False).all(),
        'children': Child.query.all(),
        'today': date.today(),
        'bike': Bike.query.get(bike_id) if bike_id else None
    }
    template = 'rent.html' if bike_id else 'rent_new.html'
    return render_template(template, **context)

@main.route('/rentals/<rental_id>/end', methods=['POST'])
@login_required
@depot_access_required
def rentals_end(rental_id):
    r = Rental.query.get_or_404(rental_id)
    r.status = 'returned'
    r.end_date = date.today()
    if r.bike: r.bike.status = 'available'
    db.session.commit()
    flash('Verhuring beëindigd.', 'success')
    return redirect(url_for('main.rentals_list'))

@main.route('/rentals/<rental_id>/cancel', methods=['POST'])
@login_required
@depot_access_required
def rentals_cancel(rental_id):
    r = Rental.query.get_or_404(rental_id)
    if r.bike: r.bike.status = 'available'
    db.session.delete(r)
    db.session.commit()
    flash('Verhuring geannuleerd.', 'info')
    return redirect(url_for('main.rentals_list'))

# FIX: Route toegevoegd voor verwijderen van oude verhuringen (gebruikt door rentals.html)
@main.route('/rentals/<rental_id>/delete', methods=['POST'])
@login_required
@depot_access_required
def rentals_delete_returned(rental_id):
    r = Rental.query.get_or_404(rental_id)
    if r.status == 'active':
        flash('Kan actieve verhuring niet verwijderen (gebruik annuleren).', 'error')
        return redirect(url_for('main.rentals_list'))
    db.session.delete(r)
    db.session.commit()
    flash('Verhuring verwijderd.', 'info')
    return redirect(url_for('main.rentals_list'))

# --- BETALINGEN (PAYMENTS) ---

@main.route('/payments')
@login_required
@finance_access_required
def payments_list():
    query = db.session.query(Payment, Member).join(Member).order_by(Payment.paid_at.desc())
    if request.args.get('method') not in [None, 'all']:
        query = query.filter(Payment.method == request.args.get('method'))
    payments = query.all()
    total = sum(p.amount for p, m in payments if p.received)
    
    return render_template('payments.html', payments_data=payments, total_payments=total, 
                           cash_payments=sum(p.amount for p, m in payments if p.method=='cash'),
                           card_payments=sum(p.amount for p, m in payments if p.method=='card'),
                           bank_payments=sum(p.amount for p, m in payments if p.method=='bank_transfer' and p.received))

@main.route('/payments/new', methods=['GET', 'POST'])
@main.route('/members/<member_id>/payment', methods=['GET', 'POST'])
@login_required
@finance_access_required
def payment_new(member_id=None):
    if request.method == 'POST':
        mid = request.form.get('member_id') or member_id
        amt = float(request.form.get('amount') or 0)
        method = request.form.get('method', 'cash')
        date_str = request.form.get('paid_at')
        received = (method in ['cash', 'card']) or (request.form.get('received') == 'true')
        
        p = Payment(member_id=mid, amount=amt, method=method, received=received)
        if date_str: p.paid_at = datetime.strptime(date_str, '%Y-%m-%d').date()
        Member.query.get(mid).last_payment = p.paid_at
        
        db.session.add(p)
        db.session.commit()
        return redirect(url_for('main.payments_list'))
        
    members = Member.query.order_by(Member.last_name).all()
    if member_id:
        return render_template('payment_form.html', member=Member.query.get(member_id))
    return render_template('payment_form_new.html', members=members, today=date.today())

@main.route('/payments/<payment_id>/toggle-received', methods=['POST'])
@login_required
@finance_access_required
def payment_toggle_received(payment_id):
    p = Payment.query.get_or_404(payment_id)
    p.received = not p.received
    db.session.commit()
    return redirect(url_for('main.payments_list'))

@main.route('/payments/<payment_id>/delete', methods=['POST'])
@login_required
@finance_access_required
def payment_delete(payment_id):
    db.session.delete(Payment.query.get_or_404(payment_id))
    db.session.commit()
    return redirect(url_for('main.payments_list'))