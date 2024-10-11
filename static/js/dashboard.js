document.addEventListener('DOMContentLoaded', function() {
    // Fetch work order stats
    fetch('/api/work_order_stats')
        .then(response => response.json())
        .then(data => {
            updateWorkOrderStats(data);
            createWorkOrderChart(data);
        });

    // Fetch work order completion trend
    fetch('/api/work_order_completion_trend')
        .then(response => response.json())
        .then(data => {
            createCompletionTrendChart(data);
        });
});

function updateWorkOrderStats(data) {
    document.getElementById('total-work-orders').textContent = data.total;
    document.getElementById('pending-work-orders').textContent = data.pending;
    document.getElementById('in-progress-work-orders').textContent = data.in_progress;
    document.getElementById('completed-work-orders').textContent = data.completed;
}

function createWorkOrderChart(data) {
    const ctx = document.getElementById('work-order-chart').getContext('2d');
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Pending', 'In Progress', 'Completed'],
            datasets: [{
                data: [data.pending, data.in_progress, data.completed],
                backgroundColor: [
                    'rgba(255, 193, 7, 0.8)',
                    'rgba(23, 162, 184, 0.8)',
                    'rgba(40, 167, 69, 0.8)'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

function createCompletionTrendChart(data) {
    const ctx = document.getElementById('completion-trend-chart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(item => item.date),
            datasets: [{
                label: 'Completed Work Orders',
                data: data.map(item => item.count),
                borderColor: 'rgba(40, 167, 69, 1)',
                backgroundColor: 'rgba(40, 167, 69, 0.1)',
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    display: false
                },
                y: {
                    display: false
                }
            }
        }
    });
}
