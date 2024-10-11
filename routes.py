from flask import render_template, request, redirect, url_for, jsonify, flash, send_file
from app import app, db
from models import Company, MaintenanceLog, WorkOrder, Notification, User
from forms import MaintenanceLogForm, WorkOrderForm, CompanySetupForm, LoginForm, RegistrationForm
from datetime import datetime, timedelta
from sqlalchemy import func, and_
import csv
import io
from fpdf import FPDF
from flask_login import login_user, login_required, logout_user, current_user

@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    pending_count = WorkOrder.query.filter_by(status='Pending').count()
    in_progress_count = WorkOrder.query.filter_by(status='In Progress').count()
    completed_count = WorkOrder.query.filter_by(status='Completed').count()
    recent_logs = MaintenanceLog.query.order_by(MaintenanceLog.created_at.desc()).limit(5).all()
    company = Company.query.first()
    unread_notifications = Notification.query.filter_by(is_read=False).order_by(Notification.created_at.desc()).all()

    return render_template('dashboard.html', 
                           pending_count=pending_count, 
                           in_progress_count=in_progress_count, 
                           completed_count=completed_count,
                           recent_logs=recent_logs,
                           company=company,
                           unread_notifications=unread_notifications)

@app.route('/maintenance_log', methods=['GET', 'POST'])
@login_required
def maintenance_log():
    form = MaintenanceLogForm()
    if form.validate_on_submit():
        new_log = MaintenanceLog()
        form.populate_obj(new_log)
        db.session.add(new_log)
        db.session.commit()
        flash('Maintenance log added successfully', 'success')
        return redirect(url_for('dashboard'))
    return render_template('maintenance_log.html', form=form)

@app.route('/work_order', methods=['GET', 'POST'])
@login_required
def work_order():
    form = WorkOrderForm()
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
    maintenance_logs = MaintenanceLog.query.all()
    return render_template('work_order.html', form=form, maintenance_logs=maintenance_logs)

@app.route('/schedule')
@login_required
def schedule():
    work_orders = WorkOrder.query.all()
    return render_template('schedule.html', work_orders=work_orders)

@app.route('/update_work_order_status', methods=['POST'])
@login_required
def update_work_order_status():
    work_order_id = request.form.get('work_order_id')
    new_status = request.form.get('new_status')
    work_order = WorkOrder.query.get(work_order_id)
    if work_order:
        work_order.status = new_status
        if new_status == 'Completed':
            work_order.completed_date = datetime.utcnow().date()
        db.session.commit()

        if work_order.is_critical and new_status in ['In Progress', 'Completed']:
            notification = Notification(
                work_order_id=work_order.id,
                message=f"Critical work order {new_status.lower()}: {work_order.maintenance_log.description[:50]}..."
            )
            db.session.add(notification)
            db.session.commit()
            flash(f'A critical work order has been {new_status.lower()}!', 'info')

        return jsonify({'success': True})
    return jsonify({'success': False}), 404

@app.route('/company_setup', methods=['GET', 'POST'])
@login_required
def company_setup():
    company = Company.query.first()
    form = CompanySetupForm(obj=company)
    if form.validate_on_submit():
        if company is None:
            company = Company()
        form.populate_obj(company)
        db.session.add(company)
        db.session.commit()
        flash('Company information updated successfully', 'success')
        return redirect(url_for('dashboard'))
    return render_template('company_setup.html', form=form)

@app.route('/reports')
@login_required
def reports():
    maintenance_classes = db.session.query(MaintenanceLog.maintenance_class).distinct().all()
    maintenance_classes = [mc[0] for mc in maintenance_classes]
    priorities = db.session.query(WorkOrder.priority).distinct().all()
    priorities = [p[0] for p in priorities]
    return render_template('reports.html', maintenance_classes=maintenance_classes, priorities=priorities)

@app.route('/filtered_reports')
@login_required
def filtered_reports():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    maintenance_class = request.args.getlist('maintenance_class')
    priority = request.args.getlist('priority')
    status = request.args.getlist('status')
    assigned_to = request.args.get('assigned_to')
    critical_only = request.args.get('critical_only')

    maintenance_logs_query = MaintenanceLog.query
    work_orders_query = WorkOrder.query

    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        maintenance_logs_query = maintenance_logs_query.filter(MaintenanceLog.date >= start_date)
        work_orders_query = work_orders_query.filter(WorkOrder.scheduled_date >= start_date)

    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        maintenance_logs_query = maintenance_logs_query.filter(MaintenanceLog.date <= end_date)
        work_orders_query = work_orders_query.filter(WorkOrder.scheduled_date <= end_date)

    if maintenance_class:
        maintenance_logs_query = maintenance_logs_query.filter(MaintenanceLog.maintenance_class.in_(maintenance_class))

    if priority:
        work_orders_query = work_orders_query.filter(WorkOrder.priority.in_(priority))

    if status:
        work_orders_query = work_orders_query.filter(WorkOrder.status.in_(status))

    if assigned_to:
        work_orders_query = work_orders_query.filter(WorkOrder.assigned_to.ilike(f"%{assigned_to}%"))

    if critical_only == 'true':
        work_orders_query = work_orders_query.filter(WorkOrder.is_critical == True)
    elif critical_only == 'false':
        work_orders_query = work_orders_query.filter(WorkOrder.is_critical == False)

    maintenance_logs = maintenance_logs_query.all()
    work_orders = work_orders_query.all()

    total_logs = len(maintenance_logs)
    total_orders = len(work_orders)
    completed_orders = sum(1 for wo in work_orders if wo.status == 'Completed')
    completion_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0

    return jsonify({
        'maintenance_logs': [
            {
                'date': log.date.strftime('%Y-%m-%d'),
                'lot_number': log.lot_number,
                'maintenance_class': log.maintenance_class,
                'description': log.description[:50] + '...' if len(log.description) > 50 else log.description
            } for log in maintenance_logs
        ],
        'work_orders': [
            {
                'id': order.id,
                'status': order.status,
                'priority': order.priority,
                'scheduled_date': order.scheduled_date.strftime('%Y-%m-%d'),
                'assigned_to': order.assigned_to,
                'is_critical': order.is_critical
            } for order in work_orders
        ],
        'total_logs': total_logs,
        'total_orders': total_orders,
        'completed_orders': completed_orders,
        'completion_rate': completion_rate
    })

@app.route('/export_report/<report_type>/<format>')
@login_required
def export_report(report_type, format):
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    if report_type == 'maintenance_logs':
        data = MaintenanceLog.query.filter(MaintenanceLog.created_at >= thirty_days_ago).all()
        filename = f"maintenance_logs_report.{format}"
        headers = ['Date', 'Lot Number', 'Contact Details', 'Maintenance Class', 'Description', 'Allocation']
    elif report_type == 'work_orders':
        data = WorkOrder.query.filter(WorkOrder.created_at >= thirty_days_ago).all()
        filename = f"work_orders_report.{format}"
        headers = ['ID', 'Status', 'Assigned To', 'Scheduled Date', 'Completed Date', 'Priority', 'Is Critical']
    else:
        return "Invalid report type", 400

    if format == 'csv':
        return export_csv(data, filename, headers)
    elif format == 'pdf':
        return export_pdf(data, filename, headers, report_type)
    else:
        return "Invalid format", 400

def export_csv(data, filename, headers):
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(headers)
    for item in data:
        if isinstance(item, MaintenanceLog):
            writer.writerow([item.date, item.lot_number, item.contact_details, item.maintenance_class, item.description, item.allocation])
        elif isinstance(item, WorkOrder):
            writer.writerow([item.id, item.status, item.assigned_to, item.scheduled_date, item.completed_date, item.priority, item.is_critical])

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        download_name=filename,
        as_attachment=True
    )

def export_pdf(data, filename, headers, report_type):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    for header in headers:
        pdf.cell(30, 10, header, 1)
    pdf.ln()
    
    for item in data:
        if isinstance(item, MaintenanceLog):
            pdf.cell(30, 10, str(item.date), 1)
            pdf.cell(30, 10, item.lot_number, 1)
            pdf.cell(30, 10, item.contact_details[:20], 1)
            pdf.cell(30, 10, item.maintenance_class, 1)
            pdf.cell(30, 10, item.description[:20], 1)
            pdf.cell(30, 10, item.allocation, 1)
        elif isinstance(item, WorkOrder):
            pdf.cell(30, 10, str(item.id), 1)
            pdf.cell(30, 10, item.status, 1)
            pdf.cell(30, 10, item.assigned_to, 1)
            pdf.cell(30, 10, str(item.scheduled_date), 1)
            pdf.cell(30, 10, str(item.completed_date) if item.completed_date else '', 1)
            pdf.cell(30, 10, item.priority, 1)
            pdf.cell(30, 10, 'Yes' if item.is_critical else 'No', 1)
        pdf.ln()

    pdf_output = pdf.output(dest='S')
    return send_file(io.BytesIO(pdf_output),
                     mimetype='application/pdf',
                     download_name=filename,
                     as_attachment=True)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Logged in successfully.', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html', form=form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in.', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/mark_notification_as_read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_as_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    notification.is_read = True
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/work_order_stats')
@login_required
def work_order_stats():
    pending_count = WorkOrder.query.filter_by(status='Pending').count()
    in_progress_count = WorkOrder.query.filter_by(status='In Progress').count()
    completed_count = WorkOrder.query.filter_by(status='Completed').count()
    total_count = pending_count + in_progress_count + completed_count

    return jsonify({
        'total': total_count,
        'pending': pending_count,
        'in_progress': in_progress_count,
        'completed': completed_count
    })

@app.route('/api/work_order_completion_trend')
@login_required
def work_order_completion_trend():
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=30)
    
    completed_orders = WorkOrder.query.filter(
        WorkOrder.status == 'Completed',
        WorkOrder.completed_date >= start_date,
        WorkOrder.completed_date <= end_date
    ).with_entities(
        func.date(WorkOrder.completed_date).label('date'),
        func.count().label('count')
    ).group_by(func.date(WorkOrder.completed_date)).all()
    
    date_range = [start_date + timedelta(days=i) for i in range(31)]
    trend_data = {date: 0 for date in date_range}
    
    for order in completed_orders:
        trend_data[order.date] = order.count
    
    return jsonify([{'date': date.strftime('%Y-%m-%d'), 'count': count} for date, count in trend_data.items()])