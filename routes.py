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

@app.route('/maintenance_log', methods=['GET', 'POST'])
@login_required
def maintenance_log():
    form = MaintenanceLogForm()
    if form.validate_on_submit():
        new_log = MaintenanceLog(
            date=form.date.data,
            lot_number=form.lot_number.data,
            contact_details=form.contact_details.data,
            maintenance_class=form.maintenance_class.data,
            description=form.description.data,
            allocation=form.allocation.data
        )
        db.session.add(new_log)
        db.session.flush()  # This assigns an ID to new_log

        new_order = WorkOrder(
            maintenance_log_id=new_log.id,
            status=form.status.data,
            assigned_to=form.assigned_to.data,
            scheduled_date=form.scheduled_date.data,
            priority=form.priority.data,
            notes=form.notes.data,
            is_critical=form.is_critical.data
        )
        db.session.add(new_order)

        if new_order.is_critical:
            notification = Notification(
                work_order_id=new_order.id,
                message=f"Critical work order created: {new_log.description[:50]}..."
            )
            db.session.add(notification)

        db.session.commit()
        flash('Maintenance log and work order created successfully', 'success')
        return redirect(url_for('dashboard'))

    return render_template('maintenance_log.html', form=form)

@app.route('/work_order', methods=['GET', 'POST'])
@login_required
def work_order():
    try:
        form = WorkOrderForm()
        logging.info(f"WorkOrderForm initialized with {len(form.maintenance_log_id.choices)} choices")
        
        # Log all available maintenance logs
        all_logs = MaintenanceLog.query.all()
        logging.info(f"Total maintenance logs in database: {len(all_logs)}")
        for log in all_logs:
            logging.info(f"Log ID: {log.id}, Date: {log.date}, Lot Number: {log.lot_number}")
        
        if form.validate_on_submit():
            new_order = WorkOrder(
                maintenance_log_id=form.maintenance_log_id.data,
                status=form.status.data,
                assigned_to=form.assigned_to.data,
                scheduled_date=form.scheduled_date.data,
                priority=form.priority.data,
                notes=form.notes.data,
                is_critical=form.is_critical.data
            )
            db.session.add(new_order)

            if new_order.is_critical:
                notification = Notification(
                    work_order_id=new_order.id,
                    message=f"Critical work order created for maintenance log {new_order.maintenance_log_id}"
                )
                db.session.add(notification)

            db.session.commit()
            flash('Work order created successfully', 'success')
            return redirect(url_for('dashboard'))

        if request.method == 'POST' and not form.validate():
            logging.error(f"Form validation errors: {form.errors}")
            flash('There was an error creating the work order. Please check the form and try again.', 'danger')

        return render_template('work_order.html', form=form)
    except Exception as e:
        logging.error(f"Error in work_order route: {str(e)}")
        flash('An unexpected error occurred. Please try again later.', 'danger')
        return redirect(url_for('dashboard'))

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

@app.route('/dashboard')
@login_required
def dashboard():
    maintenance_logs = MaintenanceLog.query.order_by(MaintenanceLog.date.desc()).limit(5).all()
    work_orders = WorkOrder.query.order_by(WorkOrder.scheduled_date).limit(5).all()
    notifications = Notification.query.filter_by(is_read=False).all()

    return render_template('dashboard.html', 
                           maintenance_logs=maintenance_logs, 
                           work_orders=work_orders,
                           notifications=notifications)

@app.route('/filtered_work_orders')
@login_required
def filtered_work_orders():
    work_orders = WorkOrder.query.all()
    return jsonify([{
        'id': order.id,
        'maintenance_log_id': order.maintenance_log_id,
        'status': order.status,
        'assigned_to': order.assigned_to,
        'scheduled_date': order.scheduled_date.strftime('%Y-%m-%d'),
        'priority': order.priority,
        'is_critical': order.is_critical
    } for order in work_orders])