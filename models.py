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
