// ==========================================================================
// MAIN APPLICATION INITIALIZER & ROUTER
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initRealtimePowerChart();
    loadTrendChart('today');
    initLiveTelemetryStream();
    loadAnomalies();
    loadReports();

    // Fetch initial device list for donut chart
    fetch('/api/telemetry/live')
        .then(r => r.json())
        .then(data => {
            if (data.devices) {
                initDonutChart(data.devices);
            }
        })
        .catch(console.error);
});

function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const viewName = item.getAttribute('data-view');
            switchView(viewName);
        });
    });
}

function switchView(viewName) {
    // Update nav active state
    document.querySelectorAll('.nav-item').forEach(item => {
        if (item.getAttribute('data-view') === viewName) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });

    // Update section active state
    document.querySelectorAll('.view-section').forEach(sec => {
        sec.classList.remove('active');
    });

    const targetSection = document.getElementById(`view-${viewName}`);
    if (targetSection) {
        targetSection.classList.add('active');
    }

    // Update Page Header
    const heading = document.getElementById('page-heading');
    const subheading = document.getElementById('page-subheading');

    const headers = {
        'live-monitor': {
            title: 'Live Energy Monitor',
            sub: 'Real-time industrial 3-phase telemetry streaming'
        },
        'analytics': {
            title: 'Energy Analytics & Trends',
            sub: 'Historical electricity consumption, peak demand, and cost matrix'
        },
        'anomalies': {
            title: 'Machine Learning Anomaly Detection',
            sub: 'Real-time multivariate isolation forest & domain rule diagnostics'
        },
        'simulator': {
            title: 'IoT Sensor Fleet & Fault Simulator',
            sub: 'Interactive ESP32 multi-device telemetry generator and fault injection'
        },
        'reports': {
            title: 'Automated Energy Audit Reports',
            sub: 'ISO 50001 compliant energy certificates & actionable ECM recommendations'
        },
        'java-compliance': {
            title: 'Enterprise Java ISO 50001 Compliance Engine',
            sub: 'Java 23 backend microservice for EnPI verification and utility penalties'
        }
    };

    if (headers[viewName]) {
        if (heading) heading.innerText = headers[viewName].title;
        if (subheading) subheading.innerText = headers[viewName].sub;
    }

    // Trigger tab-specific refresh
    if (viewName === 'anomalies') loadAnomalies();
    if (viewName === 'reports') loadReports();
    if (viewName === 'analytics') loadTrendChart('today');
}
