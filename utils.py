from models import WorkOrder
from sqlalchemy import func
from datetime import datetime, timedelta
from fpdf import FPDF

def get_work_order_stats():
    total = WorkOrder.query.count()
    pending = WorkOrder.query.filter_by(status='Pending').count()
    in_progress = WorkOrder.query.filter_by(status='In Progress').count()
    completed = WorkOrder.query.filter_by(status='Completed').count()
    
    return {
        'total': total,
        'pending': pending,
        'in_progress': in_progress,
        'completed': completed
    }

def get_work_order_completion_trend(days=30):
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days)
    
    completed_orders = WorkOrder.query.filter(
        WorkOrder.status == 'Completed',
        WorkOrder.completed_date >= start_date,
        WorkOrder.completed_date <= end_date
    ).with_entities(
        func.date(WorkOrder.completed_date).label('date'),
        func.count().label('count')
    ).group_by(func.date(WorkOrder.completed_date)).all()
    
    date_range = [start_date + timedelta(days=i) for i in range(days)]
    trend_data = {date: 0 for date in date_range}
    
    for order in completed_orders:
        trend_data[order.date] = order.count
    
    return [{'date': date.strftime('%Y-%m-%d'), 'count': count} for date, count in trend_data.items()]

def generate_work_order_pdf(work_order_id):
    work_order = WorkOrder.query.get(work_order_id)
    if not work_order:
        return None

    pdf = FPDF()
    pdf.add_page()

    # Set up fonts
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Work Order", ln=True, align="C")
    pdf.set_font("Arial", "", 12)

    # Work Order Details
    pdf.cell(0, 10, f"Work Order ID: {work_order.id}", ln=True)
    pdf.cell(0, 10, f"Status: {work_order.status}", ln=True)
    pdf.cell(0, 10, f"Assigned To: {work_order.assigned_to}", ln=True)
    pdf.cell(0, 10, f"Scheduled Date: {work_order.scheduled_date}", ln=True)
    pdf.cell(0, 10, f"Priority: {work_order.priority}", ln=True)
    pdf.cell(0, 10, f"Critical: {'Yes' if work_order.is_critical else 'No'}", ln=True)

    # Maintenance Log Details
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Maintenance Log Details", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Log ID: {work_order.maintenance_log.id}", ln=True)
    pdf.cell(0, 10, f"Date: {work_order.maintenance_log.date}", ln=True)
    pdf.cell(0, 10, f"Lot Number: {work_order.maintenance_log.lot_number}", ln=True)
    pdf.cell(0, 10, f"Maintenance Class: {work_order.maintenance_log.maintenance_class}", ln=True)

    # Description
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Description", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 10, work_order.maintenance_log.description)

    # Notes
    if work_order.notes:
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Notes", ln=True)
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 10, work_order.notes)

    return pdf.output(dest='S').encode('latin-1')
