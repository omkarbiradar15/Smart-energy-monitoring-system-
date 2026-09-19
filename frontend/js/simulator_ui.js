// ==========================================================================
// IOT SIMULATOR & FAULT INJECTION CONTROLLER
// ==========================================================================

async function injectFault(deviceId, faultType) {
    try {
        const payload = {
            device_id: deviceId,
            fault_type: faultType,
            duration_seconds: 35,
            intensity: 1.0
        };

        const res = await fetch('/api/simulator/inject-fault', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (res.ok) {
            showToast(`🚨 Fault Injected: ${faultType.toUpperCase()} on ${deviceId}`, 'warning');
            // Refresh anomaly counters
            setTimeout(loadAnomalies, 2500);
        } else {
            showToast(`Error: ${data.detail || 'Could not inject fault'}`, 'danger');
        }
    } catch (err) {
        console.error("Fault injection error:", err);
        showToast("Server communication error", 'danger');
    }
}

async function resetAllFaults() {
    try {
        const res = await fetch('/api/simulator/reset', { method: 'POST' });
        const data = await res.json();
        if (res.ok) {
            showToast("✅ All devices restored to normal nominal operation.", 'success');
        }
    } catch (err) {
        console.error("Reset error:", err);
    }
}

function showToast(message, type = 'info') {
    // Clean, unobtrusive floating notification banner
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText = 'position:fixed; bottom:24px; right:24px; z-index:9999; display:flex; flex-direction:column; gap:8px;';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    const bgColors = {
        success: 'linear-gradient(135deg, #059669, #10b981)',
        warning: 'linear-gradient(135deg, #d97706, #f59e0b)',
        danger: 'linear-gradient(135deg, #e11d48, #f43f5e)',
        info: 'linear-gradient(135deg, #0284c7, #06b6d4)'
    };

    toast.style.cssText = `
        background: ${bgColors[type] || bgColors.info};
        color: #fff;
        padding: 12px 20px;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 600;
        box-shadow: 0 10px 25px rgba(0,0,0,0.4);
        opacity: 0;
        transform: translateY(10px);
        transition: all 0.25s ease;
    `;
    toast.innerText = message;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateY(0)';
    }, 20);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        setTimeout(() => toast.remove(), 300);
    }, 3800);
}
