from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class Company(db.Model):
    __tablename__ = 'companies'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    logo_url = db.Column(db.String(255))
    contact_info = db.Column(db.Text)

class MaintenanceLog(db.Model):
    __tablename__ = 'maintenance_logs'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    lot_number = db.Column(db.String(50), nullable=False)
    contact_details = db.Column(db.String(255), nullable=False)
    maintenance_class = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text, nullable=False)
    allocation = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    work_orders = db.relationship('WorkOrder', backref='maintenance_log', lazy=True)

class WorkOrder(db.Model):
    __tablename__ = 'work_orders'
    id = db.Column(db.Integer, primary_key=True)
    maintenance_log_id = db.Column(db.Integer, db.ForeignKey('maintenance_logs.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    assigned_to = db.Column(db.String(100), nullable=False)
    scheduled_date = db.Column(db.Date, nullable=False)
    completed_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    priority = db.Column(db.String(20), nullable=False)
    is_critical = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    work_order_id = db.Column(db.Integer, db.ForeignKey('work_orders.id'), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
