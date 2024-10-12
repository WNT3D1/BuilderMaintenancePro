document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('work-order-form');
    if (form) {
        form.addEventListener('submit', function(event) {
            event.preventDefault();
            
            if (validateForm()) {
                this.submit();
            }
        });
    }

    const filterForm = document.getElementById('filter-form');
    if (filterForm) {
        filterForm.addEventListener('submit', function(event) {
            event.preventDefault();
            fetchFilteredWorkOrders();
        });
    }

    // Initial load of work orders
    fetchFilteredWorkOrders();
});

function validateForm() {
    let isValid = true;
    const requiredFields = document.querySelectorAll('[required]');
    
    requiredFields.forEach(field => {
        if (!field.value) {
            isValid = false;
            field.classList.add('is-invalid');
        } else {
            field.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

function fetchFilteredWorkOrders() {
    const filterForm = document.getElementById('filter-form');
    if (filterForm) {
        const formData = new FormData(filterForm);
        const queryString = new URLSearchParams(formData).toString();

        fetch(`/filtered_work_orders?${queryString}`)
            .then(response => response.json())
            .then(data => {
                updateWorkOrdersTable(data);
            })
            .catch(error => {
                console.error('Error:', error);
            });
    }
}

function updateWorkOrdersTable(workOrders) {
    const tableBody = document.querySelector('#work-orders-table tbody');
    if (tableBody) {
        tableBody.innerHTML = '';

        workOrders.forEach(order => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${order.id}</td>
                <td>${order.maintenance_log_id}</td>
                <td>${order.status}</td>
                <td>${order.assigned_to}</td>
                <td>${order.scheduled_date}</td>
                <td>${order.priority}</td>
                <td>${order.is_critical ? 'Yes' : 'No'}</td>
                <td>
                    <button class="btn btn-sm btn-primary status-update-btn" data-work-order-id="${order.id}" data-status="In Progress">
                        Start
                    </button>
                    <button class="btn btn-sm btn-success status-update-btn" data-work-order-id="${order.id}" data-status="Completed">
                        Complete
                    </button>
                </td>
            `;
            tableBody.appendChild(row);
        });

        // Re-attach event listeners for status update buttons
        attachStatusUpdateListeners();
    }
}

function attachStatusUpdateListeners() {
    const statusButtons = document.querySelectorAll('.status-update-btn');
    
    statusButtons.forEach(button => {
        button.addEventListener('click', function() {
            const workOrderId = this.dataset.workOrderId;
            const newStatus = this.dataset.status;
            updateWorkOrderStatus(workOrderId, newStatus);
        });
    });
}

function updateWorkOrderStatus(workOrderId, newStatus) {
    fetch('/update_work_order_status', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `work_order_id=${workOrderId}&new_status=${newStatus}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            fetchFilteredWorkOrders();
        } else {
            alert('Failed to update work order status. Please try again.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while updating the work order status.');
    });
}
