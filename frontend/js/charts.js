// ==========================================================================
// CHART VISUALIZATION MODULE (Chart.js 4+)
// ==========================================================================

let realtimeChart = null;
let historicalChart = null;
let donutChart = null;

const MAX_REALTIME_POINTS = 30;
const realtimeLabels = [];
const realtimeData = [];

function initRealtimePowerChart() {
    const ctx = document.getElementById('realtimePowerChart');
    if (!ctx) return;

    // Prepopulate empty buffer
    const now = new Date();
    for (let i = MAX_REALTIME_POINTS; i > 0; i--) {
        const t = new Date(now.getTime() - i * 2000);
        realtimeLabels.push(t.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
        realtimeData.push(null);
    }

    realtimeChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: realtimeLabels,
            datasets: [{
                label: 'Active Load (kW)',
                data: realtimeData,
                borderColor: '#06b6d4',
                backgroundColor: 'rgba(6, 182, 212, 0.12)',
                borderWidth: 2.5,
                fill: true,
                tension: 0.35,
                pointRadius: 2,
                pointHoverRadius: 5,
                pointBackgroundColor: '#38bdf8'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 400 },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.9)',
                    borderColor: 'rgba(6, 182, 212, 0.4)',
                    borderWidth: 1,
                    titleColor: '#f8fafc',
                    bodyColor: '#38bdf8',
                    callbacks: {
                        label: (c) => ` ${c.parsed.y ? c.parsed.y.toFixed(1) : 0} kW`
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#64748b', maxTicksLimit: 6, font: { size: 10 } }
                },
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#64748b', font: { size: 10 } },
                    suggestedMin: 50,
                    suggestedMax: 300
                }
            }
        }
    });
}

function updateRealtimeChart(totalKw) {
    if (!realtimeChart) return;

    const timeLabel = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    
    realtimeLabels.push(timeLabel);
    realtimeData.push(totalKw);

    if (realtimeLabels.length > MAX_REALTIME_POINTS) {
        realtimeLabels.shift();
        realtimeData.shift();
    }

    realtimeChart.update('none'); // high performance non-blocking update
}

async function loadTrendChart(period = 'today', btnElement = null) {
    if (btnElement) {
        document.querySelectorAll('.chart-filters .filter-btn').forEach(b => b.classList.remove('active'));
        btnElement.classList.add('active');
    }

    try {
        const res = await fetch(`/api/telemetry/chart-trends?period=${period}`);
        const data = await res.json();
        
        const labels = data.trends.map(t => t.time);
        const kwValues = data.trends.map(t => t.power_kw);
        const kwhValues = data.trends.map(t => t.energy_kwh);

        const ctx = document.getElementById('historicalTrendChart');
        if (!ctx) return;

        if (historicalChart) {
            historicalChart.destroy();
        }

        historicalChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        type: 'line',
                        label: 'Average Power (kW)',
                        data: kwValues,
                        borderColor: '#38bdf8',
                        backgroundColor: 'rgba(56, 189, 248, 0.1)',
                        borderWidth: 2,
                        tension: 0.3,
                        yAxisID: 'y'
                    },
                    {
                        type: 'bar',
                        label: 'Energy Consumed (kWh)',
                        data: kwhValues,
                        backgroundColor: 'rgba(16, 185, 129, 0.45)',
                        borderColor: '#10b981',
                        borderWidth: 1,
                        borderRadius: 4,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: { color: '#94a3b8', font: { size: 12 } }
                    }
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: '#64748b' }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: '#38bdf8' },
                        title: { display: true, text: 'Power (kW)', color: '#38bdf8' }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        grid: { drawOnChartArea: false },
                        ticks: { color: '#10b981' },
                        title: { display: true, text: 'Energy (kWh)', color: '#10b981' }
                    }
                }
            }
        });
    } catch (err) {
        console.error("Error loading trend chart:", err);
    }
}

function initDonutChart(devices) {
    const ctx = document.getElementById('loadShareDonutChart');
    if (!ctx) return;

    if (donutChart) {
        donutChart.destroy();
    }

    const labels = devices.map(d => d.device_name || d.device_id);
    const data = devices.map(d => d.active_power_kw || d.base_kw || 20);

    donutChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: [
                    '#06b6d4',
                    '#38bdf8',
                    '#10b981',
                    '#f59e0b',
                    '#a855f7'
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#94a3b8', font: { size: 11 }, boxWidth: 12 }
                }
            },
            cutout: '70%'
        }
    });
}
