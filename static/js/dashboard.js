document.addEventListener('DOMContentLoaded', function() {
    // Fetch work order stats
    fetch('/api/work_order_stats')
        .then(response => response.json())
        .then(data => {
            updateWorkOrderStats(data);
            createWorkOrderChart(data);
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
                    position: 'right',
                    labels: {
                        boxWidth: 10,
                        padding: 5,
                        font: {
                            size: 10
                        }
                    }
                }
            },
            layout: {
                padding: 5
            }
        }
    });
}
