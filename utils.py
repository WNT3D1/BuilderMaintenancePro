from models import WorkOrder
from sqlalchemy import func
from datetime import datetime, timedelta

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
