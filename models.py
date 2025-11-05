from datetime import datetime
from extensions import db
import uuid

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
    user_id = db.Column(db.String, primary_key=True, default=gen_uuid)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    password = db.Column(db.String(255))
    employee_id = db.Column(db.String, db.ForeignKey('employee.employee_id'))

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
    last_payment = db.Column(db.Date)
    status = db.Column(db.String(20), default='active')  # active | inactive | paused

    children = db.relationship('Child', backref='member', cascade='all, delete-orphan', lazy=True)

class Child(db.Model):
    __tablename__ = 'child'
    child_id = db.Column(db.String, primary_key=True, default=gen_uuid)
    member_id = db.Column(db.String, db.ForeignKey('member.member_id'), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
