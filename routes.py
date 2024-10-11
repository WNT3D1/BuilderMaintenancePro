from flask import render_template, request, redirect, url_for, jsonify, flash, send_file
from app import app, db
from models import Company, MaintenanceLog, WorkOrder, Notification
from forms import MaintenanceLogForm, WorkOrderForm, CompanySetupForm
from datetime import datetime, timedelta
from sqlalchemy import func
import csv
import io
from fpdf import FPDF

@app.route('/')
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
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('maintenance_log.html', form=form)

@app.route('/work_order', methods=['GET', 'POST'])
def work_order():
    form = WorkOrderForm()
    if form.validate_on_submit():
        new_order = WorkOrder(
            maintenance_log_id=form.maintenance_log_id.data,
            status=form.status.data,
            assigned_to=form.assigned_to.data,
            scheduled_date=form.scheduled_date.data,
            notes=form.notes.data,
            priority=form.priority.data,
            is_critical=form.is_critical.data
        )
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

        return redirect(url_for('dashboard'))
    maintenance_logs = MaintenanceLog.query.all()
    return render_template('work_order.html', form=form, maintenance_logs=maintenance_logs)

@app.route('/schedule')
def schedule():
    work_orders = WorkOrder.query.all()
    return render_template('schedule.html', work_orders=work_orders)

@app.route('/update_work_order_status', methods=['POST'])
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
def company_setup():
    company = Company.query.first()
    form = CompanySetupForm(obj=company)
    if form.validate_on_submit():
        if company is None:
            company = Company()
        form.populate_obj(company)
        db.session.add(company)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('company_setup.html', form=form)

@app.route('/reports')
def reports():
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    maintenance_logs = MaintenanceLog.query.filter(MaintenanceLog.created_at >= thirty_days_ago).all()
    work_orders = WorkOrder.query.filter(WorkOrder.created_at >= thirty_days_ago).all()

    total_logs = len(maintenance_logs)
    total_orders = len(work_orders)
    completed_orders = sum(1 for wo in work_orders if wo.status == 'Completed')
    completion_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0

    return render_template('reports.html', 
                           maintenance_logs=maintenance_logs, 
                           work_orders=work_orders,
                           total_logs=total_logs,
                           total_orders=total_orders,
                           completed_orders=completed_orders,
                           completion_rate=completion_rate)

@app.route('/export_report/<report_type>/<format>')
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
    return send_file(io.BytesIO(output.getvalue().encode()),
                     mimetype='text/csv',
                     as_attachment=True,
                     attachment_filename=filename)

def export_pdf(data, filename, headers, report_type):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Add headers
    for header in headers:
        pdf.cell(30, 10, header, 1)
    pdf.ln()
    
    # Add data
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

    pdf_output = pdf.output(dest='S').encode('latin-1')
    return send_file(io.BytesIO(pdf_output),
                     mimetype='application/pdf',
                     as_attachment=True,
                     attachment_filename=filename)

@app.route('/filtered_work_orders')
def filtered_work_orders():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    status = request.args.get('status')
    priority = request.args.get('priority')
    sort_by = request.args.get('sort_by', 'scheduled_date')
    sort_order = request.args.get('sort_order', 'asc')

    query = WorkOrder.query

    if start_date:
        query = query.filter(WorkOrder.scheduled_date >= datetime.strptime(start_date, '%Y-%m-%d'))
    if end_date:
        query = query.filter(WorkOrder.scheduled_date <= datetime.strptime(end_date, '%Y-%m-%d'))
    if status:
        query = query.filter(WorkOrder.status == status)
    if priority:
        query = query.filter(WorkOrder.priority == priority)

    if sort_by == 'scheduled_date':
        query = query.order_by(WorkOrder.scheduled_date.asc() if sort_order == 'asc' else WorkOrder.scheduled_date.desc())
    elif sort_by == 'status':
        query = query.order_by(WorkOrder.status.asc() if sort_order == 'asc' else WorkOrder.status.desc())
    elif sort_by == 'priority':
        query = query.order_by(WorkOrder.priority.asc() if sort_order == 'asc' else WorkOrder.priority.desc())

    filtered_orders = query.all()

    work_orders_data = []
    for order in filtered_orders:
        work_orders_data.append({
            'id': order.id,
            'maintenance_log_id': order.maintenance_log_id,
            'status': order.status,
            'assigned_to': order.assigned_to,
            'scheduled_date': order.scheduled_date.strftime('%Y-%m-%d'),
            'notes': order.notes,
            'priority': order.priority,
            'is_critical': order.is_critical
        })

    return jsonify(work_orders_data)

@app.route('/mark_notification_as_read/<int:notification_id>', methods=['POST'])
def mark_notification_as_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    notification.is_read = True
    db.session.commit()
    return jsonify({'success': True})
