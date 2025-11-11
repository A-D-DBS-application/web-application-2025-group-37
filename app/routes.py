from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime, date
from app.extensions import db
from app.models import Member, Child, User, Bike, Rental, Payment
from sqlalchemy import text

main = Blueprint('main', __name__)

# Dummy data (je kunt dit later koppelen aan een echte DB)
bikes = [
    {"id": 1, "name": "Gazelle CityGo", "type": "Stadsfiets", "status": "Beschikbaar"},
    {"id": 2, "name": "Cortina E-U4", "type": "Elektrische fiets", "status": "Verhuurd"},
    {"id": 3, "name": "Batavus Quip", "type": "Stadsfiets", "status": "Beschikbaar"}
]

@main.route('/')
def home():
    # Home is the Depot Manager login. If already logged in, go to bikes dashboard.
    if session.get('user_id'):
        return redirect(url_for('main.bike_list'))
    return render_template('login.html')

@main.route('/bikes')
def bike_list():
    query = Bike.query.filter_by(archived=False)
    bikes = query.order_by(Bike.created_at.desc()).all()
    return render_template('bikes.html', bikes=bikes)

 

@main.route('/about')
def about():
    return render_template('about.html')

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
    # Seed default user if none
    if not User.query.first():
        admin = User(first_name='Admin', last_name='User', email='admin@example.com')
        admin.set_password('admin')
        db.session.add(admin)
        db.session.commit()
    if request.method == 'POST':
        email = request.form.get('email','').strip()
        password = request.form.get('password','')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['user_id'] = user.user_id
            return redirect(url_for('main.home'))
        flash('Ongeldige inloggegevens', 'error')
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
def members_list():
    members = Member.query.order_by(Member.created_at.desc()).all()
    return render_template('members.html', members=members)


@main.route('/members/new', methods=['GET', 'POST'])
@login_required
def members_new():
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        last_payment_raw = request.form.get('last_payment')
        status = request.form.get('status', 'active')

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

    return render_template('member_form.html', mode='new', member=None)


@main.route('/members/<member_id>/edit', methods=['GET', 'POST'])
@login_required
def members_edit(member_id):
    member = Member.query.get_or_404(member_id)
    if request.method == 'POST':
        member.first_name = request.form.get('first_name', '').strip()
        member.last_name = request.form.get('last_name', '').strip()
        member.email = request.form.get('email', '').strip()
        member.phone = request.form.get('phone', '').strip()
        member.address = request.form.get('address', '').strip()
        last_payment_raw = request.form.get('last_payment')
        status = request.form.get('status', 'active')

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

    return render_template('member_form.html', mode='edit', member=member)


# -----------------------
# Bikes CRUD and status
# -----------------------

@main.route('/bikes/new', methods=['GET','POST'])
@login_required
def bikes_new():
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        btype = request.form.get('type','').strip()
        status = request.form.get('status','available')
        bike = Bike(name=name or 'Fiets', type=btype, status=status)
        db.session.add(bike)
        db.session.commit()
        return redirect(url_for('main.bike_list'))
    return render_template('bike_form.html', mode='new', bike=None)


@main.route('/bikes/<bike_id>/edit', methods=['GET','POST'])
@login_required
def bikes_edit(bike_id):
    bike = Bike.query.get_or_404(bike_id)
    if request.method == 'POST':
        bike.name = request.form.get('name','').strip() or bike.name
        bike.type = request.form.get('type','').strip()
        bike.status = request.form.get('status','available')
        db.session.commit()
        return redirect(url_for('main.bike_list'))
    return render_template('bike_form.html', mode='edit', bike=bike)


@main.route('/bikes/<bike_id>/status', methods=['POST'])
@login_required
def bikes_status(bike_id):
    bike = Bike.query.get_or_404(bike_id)
    new_status = request.form.get('status','available')
    bike.status = new_status
    db.session.commit()
    return redirect(url_for('main.bike_list'))


@main.route('/bikes/<bike_id>/archive', methods=['POST'])
@login_required
def bikes_archive(bike_id):
    bike = Bike.query.get_or_404(bike_id)
    bike.archived = True
    db.session.commit()
    return redirect(url_for('main.bike_list'))

@main.route('/bikes/<bike_id>/delete', methods=['POST'])
@login_required
def bikes_delete(bike_id):
    bike = Bike.query.get_or_404(bike_id)
    # Remove dependent rentals to avoid FK constraint issues
    Rental.query.filter_by(bike_id=bike.bike_id).delete(synchronize_session=False)
    db.session.delete(bike)
    db.session.commit()
    flash('Fiets verwijderd', 'info')
    return redirect(url_for('main.bike_list'))


# -----------------------
# Rentals
# -----------------------

@main.route('/rent/<bike_id>', methods=['GET','POST'])
@login_required
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
        return redirect(url_for('main.bike_list'))
    members = Member.query.order_by(Member.last_name).all()
    return render_template('rent.html', bike=bike, members=members)


# -----------------------
# Payments
# -----------------------

@main.route('/members/<member_id>/payment', methods=['GET','POST'])
@login_required
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
    return render_template('payment_form.html', member=member)

@main.route('/members/<member_id>/delete', methods=['POST'])
@login_required
def members_delete(member_id):
    member = Member.query.get_or_404(member_id)
    # Remove dependent rentals and payments first
    Rental.query.filter_by(member_id=member.member_id).delete(synchronize_session=False)
    Payment.query.filter_by(member_id=member.member_id).delete(synchronize_session=False)
    db.session.delete(member)
    db.session.commit()
    flash('Lid verwijderd', 'info')
    return redirect(url_for('main.members_list'))

