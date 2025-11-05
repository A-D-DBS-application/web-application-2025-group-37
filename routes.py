from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
from extensions import db
from models import Member, Child

main = Blueprint('main', __name__)

# Dummy data (je kunt dit later koppelen aan een echte DB)
bikes = [
    {"id": 1, "name": "Gazelle CityGo", "type": "Stadsfiets", "status": "Beschikbaar"},
    {"id": 2, "name": "Cortina E-U4", "type": "Elektrische fiets", "status": "Verhuurd"},
    {"id": 3, "name": "Batavus Quip", "type": "Stadsfiets", "status": "Beschikbaar"}
]

@main.route('/')
def home():
    return render_template('index.html')

@main.route('/bikes')
def bike_list():
    return render_template('bikes.html', bikes=bikes)

@main.route('/rent/<int:bike_id>')
def rent_bike(bike_id):
    bike = next((b for b in bikes if b["id"] == bike_id), None)
    return render_template('rent.html', bike=bike)

@main.route('/about')
def about():
    return render_template('about.html')

# -----------------------
# Member management (Depot manager)
# -----------------------

@main.route('/members')
def members_list():
    members = Member.query.order_by(Member.created_at.desc()).all()
    return render_template('members.html', members=members)


@main.route('/members/new', methods=['GET', 'POST'])
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

        db.session.commit()
        return redirect(url_for('main.members_list'))

    return render_template('member_form.html', mode='new', member=None)


@main.route('/members/<member_id>/edit', methods=['GET', 'POST'])
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

