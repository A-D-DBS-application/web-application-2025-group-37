from datetime import datetime
from app.extensions import db
import uuid
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash

def gen_uuid():
    return str(uuid.uuid4())

class Employee(db.Model):
    employee_id = db.Column(db.String, primary_key=True, default=gen_uuid)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    password = db.Column(db.String(255))
    employee_type = db.Column(db.String(50))

class User(db.Model):
    # Keep app's own auth table separate from Supabase mirror
    __tablename__ = 'user'

    user_id = db.Column(db.String, primary_key=True, default=gen_uuid)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    password = db.Column(db.String(255))
    employee_id = db.Column(db.String, db.ForeignKey('employee.employee_id'))

    def set_password(self, raw: str):
        self.password = generate_password_hash(raw)

    def check_password(self, raw: str) -> bool:
        return check_password_hash(self.password or '', raw)

# Member management models
class Member(db.Model):
    __tablename__ = 'member'
    member_id = db.Column(db.String, primary_key=True, default=gen_uuid)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(30))
    address = db.Column(db.String(255))
    street = db.Column(db.String(120))
    house_number = db.Column(db.String(20))
    postcode = db.Column(db.String(20))
    city = db.Column(db.String(120))
    last_payment = db.Column(db.Date)
    status = db.Column(db.String(20), default='active')  # active | inactive | paused

    children = db.relationship('Child', backref='member', cascade='all, delete-orphan', lazy=True)

class Child(db.Model):
    __tablename__ = 'child'
    child_id = db.Column(db.String, primary_key=True, default=gen_uuid)
    member_id = db.Column(db.String, db.ForeignKey('member.member_id'), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)


class Bike(db.Model):
    __tablename__ = 'bike'
    bike_id = db.Column(db.String, primary_key=True, default=gen_uuid)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    name = db.Column(db.String(120), nullable=False)
    type = db.Column(db.String(80))
    status = db.Column(db.String(20), default='available')  # available | rented | repair
    archived = db.Column(db.Boolean, default=False)


class Rental(db.Model):
    __tablename__ = 'rental'
    rental_id = db.Column(db.String, primary_key=True, default=gen_uuid)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    bike_id = db.Column(db.String, db.ForeignKey('bike.bike_id'), nullable=False)
    member_id = db.Column(db.String, db.ForeignKey('member.member_id'))
    child_id = db.Column(db.String, db.ForeignKey('child.child_id'))
    start_date = db.Column(db.Date, default=date.today)
    end_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='active')  # active | returned
    # Relationships for convenient access in templates
    bike = db.relationship('Bike', lazy='joined')
    member = db.relationship('Member', lazy='joined')
    child = db.relationship('Child', lazy='joined')


class Payment(db.Model):
    __tablename__ = 'payment'
    payment_id = db.Column(db.String, primary_key=True, default=gen_uuid)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    member_id = db.Column(db.String, db.ForeignKey('member.member_id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    paid_at = db.Column(db.Date, default=date.today)

class Item(db.Model):
    __tablename__ = 'item'
    item_id = db.Column(db.String, primary_key=True, default=gen_uuid)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    name = db.Column(db.String(120), nullable=False)
    type = db.Column(db.String(80))
    status = db.Column(db.String(20), default='available')  # available | rented | repair | unavailable
    archived = db.Column(db.Boolean, default=False)
