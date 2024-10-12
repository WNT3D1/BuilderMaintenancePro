document.addEventListener('DOMContentLoaded', function() {
    // Fetch work order stats
    fetch('/api/work_order_stats')
        .then(response => response.json())
        .then(data => {
            updateWorkOrderStats(data);
        });
});

function updateWorkOrderStats(data) {
    document.getElementById('total-work-orders').textContent = data.total;
    document.getElementById('pending-work-orders').textContent = data.pending;
    document.getElementById('in-progress-work-orders').textContent = data.in_progress;
    document.getElementById('completed-work-orders').textContent = data.completed;
}
