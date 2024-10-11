document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('work-order-form');
    const statusButtons = document.querySelectorAll('.status-update-btn');
    
    form.addEventListener('submit', function(event) {
        event.preventDefault();
        
        if (validateForm()) {
            this.submit();
        }
    });
    
    statusButtons.forEach(button => {
        button.addEventListener('click', function() {
            const workOrderId = this.dataset.workOrderId;
            const newStatus = this.dataset.status;
            updateWorkOrderStatus(workOrderId, newStatus);
        });
    });
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
            location.reload();
        } else {
            alert('Failed to update work order status. Please try again.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while updating the work order status.');
    });
}
