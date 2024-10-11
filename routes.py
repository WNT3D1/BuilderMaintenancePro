from flask import render_template, request, redirect, url_for, jsonify
from app import app, db
from models import Company, MaintenanceLog, WorkOrder
from forms import MaintenanceLogForm, WorkOrderForm, CompanySetupForm
from datetime import datetime
from sqlalchemy import func

@app.route('/')
def dashboard():
    # Get counts for different work order statuses
    pending_count = WorkOrder.query.filter_by(status='Pending').count()
    in_progress_count = WorkOrder.query.filter_by(status='In Progress').count()
    completed_count = WorkOrder.query.filter_by(status='Completed').count()

    # Get recent maintenance logs
    recent_logs = MaintenanceLog.query.order_by(MaintenanceLog.created_at.desc()).limit(5).all()

    # Get company info
    company = Company.query.first()

    return render_template('dashboard.html', 
                           pending_count=pending_count, 
                           in_progress_count=in_progress_count, 
                           completed_count=completed_count,
                           recent_logs=recent_logs,
                           company=company)

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
            notes=form.notes.data
        )
        db.session.add(new_order)
        db.session.commit()
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
    # Get maintenance logs and work orders for the last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    maintenance_logs = MaintenanceLog.query.filter(MaintenanceLog.created_at >= thirty_days_ago).all()
    work_orders = WorkOrder.query.filter(WorkOrder.created_at >= thirty_days_ago).all()

    # Calculate some statistics
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
