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
    return render_template('work_order.html', form=form)
