// ==========================================================================
// MACHINE LEARNING ANOMALY DETECTION VIEW
// ==========================================================================

async function loadAnomalies() {
    try {
        const [anomaliesRes, statsRes] = await Promise.all([
            fetch('/api/anomalies?limit=50'),
            fetch('/api/anomalies/stats')
        ]);

        if (anomaliesRes.ok) {
            const list = await anomaliesRes.json();
            renderAnomaliesTable(list);
        }

        if (statsRes.ok) {
            const stats = await statsRes.json();
            const totalEl = document.getElementById('stats-total-anomalies');
            const unresEl = document.getElementById('stats-unresolved-anomalies');
            const badgeEl = document.getElementById('sidebar-anomaly-count');

            if (totalEl) totalEl.innerText = stats.total_anomalies;
            if (unresEl) unresEl.innerText = stats.unresolved_anomalies;
            if (badgeEl) {
                badgeEl.innerText = stats.unresolved_anomalies;
                badgeEl.style.display = stats.unresolved_anomalies > 0 ? 'inline-block' : 'none';
            }
        }
    } catch (err) {
        console.error("Error loading anomalies:", err);
    }
}

function renderAnomaliesTable(anomalies) {
    const tbody = document.getElementById('anomalies-table-body');
    if (!tbody) return;

    if (!anomalies.length) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:30px; color:var(--text-muted);">No anomalies recorded. All systems operating within normal parameters.</td></tr>`;
        return;
    }

    tbody.innerHTML = anomalies.map(a => {
        const d = new Date(a.timestamp);
        const timeStr = d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        let sevClass = 'sev-low';
        if (a.severity === 'CRITICAL') sevClass = 'sev-critical';
        else if (a.severity === 'HIGH') sevClass = 'sev-high';
        else if (a.severity === 'MEDIUM') sevClass = 'sev-medium';

        const statusHtml = a.resolved 
            ? `<span style="color:var(--accent-emerald); font-size:12px; font-weight:600;">✓ Resolved</span>`
            : `<button class="btn btn-outline" style="padding:4px 10px; font-size:11px;" onclick="openResolveModal(${a.id}, '${escapeHtml(a.description)}')">Resolve</button>`;

        return `
            <tr>
                <td style="color:var(--text-muted); font-size:12px;">${timeStr}</td>
                <td><strong style="color:var(--accent-cyan);">${a.device_id}</strong></td>
                <td><span style="font-weight:600;">${a.anomaly_type}</span></td>
                <td><span class="severity-pill ${sevClass}">${a.severity}</span></td>
                <td style="font-family:monospace; color:var(--accent-blue);">${(a.anomaly_score * 100).toFixed(0)}%</td>
                <td style="max-width:320px; font-size:12px; color:var(--text-secondary);">${a.description}</td>
                <td>${statusHtml}</td>
            </tr>
        `;
    }).join('');
}

function openResolveModal(id, desc) {
    const modal = document.getElementById('resolveModal');
    const idInput = document.getElementById('resolve-anomaly-id');
    const descEl = document.getElementById('resolve-anomaly-desc');
    const actionInput = document.getElementById('resolve-action-text');

    if (idInput) idInput.value = id;
    if (descEl) descEl.innerText = desc;
    if (actionInput) actionInput.value = '';
    if (modal) modal.classList.add('active');
}

function closeResolveModal() {
    const modal = document.getElementById('resolveModal');
    if (modal) modal.classList.remove('active');
}

async function submitResolveAnomaly() {
    const id = document.getElementById('resolve-anomaly-id').value;
    const actionText = document.getElementById('resolve-action-text').value;

    if (!actionText.trim()) {
        alert("Please describe the corrective action taken.");
        return;
    }

    try {
        const res = await fetch(`/api/anomalies/${id}/resolve`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action_taken: actionText })
        });

        if (res.ok) {
            closeResolveModal();
            showToast("Anomaly resolved successfully", "success");
            loadAnomalies();
        }
    } catch (err) {
        console.error("Resolve error:", err);
    }
}

function escapeHtml(str) {
    return (str || '').replace(/'/g, "\\'").replace(/"/g, '&quot;');
}
