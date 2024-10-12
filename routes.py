from flask import render_template, request, redirect, url_for, jsonify, flash
from app import app, db
from models import Company, MaintenanceLog, WorkOrder, Notification, User
from forms import MaintenanceLogForm, WorkOrderForm, CompanySetupForm, LoginForm, RegistrationForm
from datetime import datetime, timedelta
from sqlalchemy import func, and_
import csv
import io
from fpdf import FPDF
from flask_login import login_user, login_required, logout_user, current_user
import logging

logging.basicConfig(level=logging.INFO)

@app.route('/work_order', methods=['GET', 'POST'])
@login_required
def work_order():
    logging.info(f"User {current_user.username} accessing work_order route")
    
    maintenance_logs_count = MaintenanceLog.query.count()
    logging.info(f"Number of MaintenanceLog entries: {maintenance_logs_count}")

    if maintenance_logs_count == 0:
        test_logs = [
            MaintenanceLog(date=datetime.utcnow().date(), lot_number="LOT001", contact_details="John Doe", 
                           maintenance_class="3MTR", description="Test maintenance log 1", allocation="Team A"),
            MaintenanceLog(date=datetime.utcnow().date(), lot_number="LOT002", contact_details="Jane Smith", 
                           maintenance_class="IAS", description="Test maintenance log 2", allocation="Team B"),
        ]
        db.session.add_all(test_logs)
        db.session.commit()
        logging.info("Added test MaintenanceLog entries")

    form = WorkOrderForm()
    logging.info(f"WorkOrderForm created with maintenance_log_id choices: {form.maintenance_log_id.choices}")
    
    if form.validate_on_submit():
        new_order = WorkOrder()
        form.populate_obj(new_order)
        db.session.add(new_order)
        db.session.commit()

        if new_order.is_critical:
            notification = Notification(
                work_order_id=new_order.id,
                message=f"Critical work order created: {new_order.maintenance_log.description[:50]}..."
            )
            db.session.add(notification)
            db.session.commit()
            flash('A critical work order has been created!', 'warning')

        flash('Work order created successfully', 'success')
        return redirect(url_for('dashboard'))
    
    if form.errors:
        logging.error(f"Form validation errors: {form.errors}")
    
    return render_template('work_order.html', form=form)

# Add other routes here...

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            logging.info(f"User {user.username} logged in successfully")
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))
