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
    """
    User model voor authenticatie en autorisatie.
    
    Rollen:
    - 'depot_manager': Toegang tot fietsen, verhuringen, objecten, leden
    - 'finance_manager': Toegang tot betalingen en financiële rapporten
    - 'admin': Volledige toegang (optioneel voor toekomstige uitbreiding)
    """
    __tablename__ = 'user'

    user_id = db.Column(db.String, primary_key=True, default=gen_uuid)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    password = db.Column(db.String(255))
    role = db.Column(db.String(50), default='depot_manager')  # depot_manager | finance_manager | admin
    employee_id = db.Column(db.String, db.ForeignKey('employee.employee_id'))

    def set_password(self, raw: str):
        """Hash en sla wachtwoord veilig op"""
        self.password = generate_password_hash(raw)

    def check_password(self, raw: str) -> bool:
        """Verifieer wachtwoord tegen gehashte versie"""
        return check_password_hash(self.password or '', raw)
    
    def has_role(self, *roles) -> bool:
        """Check of gebruiker één van de opgegeven rollen heeft"""
        return self.role in roles
    
    def can_access_finance(self) -> bool:
        """Check of gebruiker toegang heeft tot financiële gegevens"""
        return self.role in ['finance_manager', 'admin']
    
    def can_access_depot(self) -> bool:
        """Check of gebruiker toegang heeft tot depot operaties"""
        return self.role in ['depot_manager', 'admin']

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
    method = db.Column(db.String(20), default='cash')  # cash | card | bank_transfer
    received = db.Column(db.Boolean, default=True)  # Voor bankbetalingen: is bedrag ontvangen?
    
    member = db.relationship('Member', lazy='joined')

class Item(db.Model):
    __tablename__ = 'item'
    item_id = db.Column(db.String, primary_key=True, default=gen_uuid)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    name = db.Column(db.String(120), nullable=False)
    type = db.Column(db.String(80))
    status = db.Column(db.String(20), default='available')  # available | rented | repair | unavailable
    archived = db.Column(db.Boolean, default=False)
