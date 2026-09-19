// ==========================================================================
// REAL-TIME WEBSOCKET & TELEMETRY STREAMING CLIENT
// ==========================================================================

let liveSocket = null;
let reconnectTimer = null;
let pollFallbackTimer = null;

function initLiveTelemetryStream() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/live`;
    const indicator = document.getElementById('ws-status-indicator');
    const statusText = document.getElementById('ws-status-text');

    try {
        liveSocket = new WebSocket(wsUrl);

        liveSocket.onopen = () => {
            console.log("⚡ Connected to live WebSocket telemetry stream.");
            if (indicator) indicator.style.display = 'flex';
            if (statusText) statusText.innerText = 'LIVE TELEMETRY STREAMING';
            clearInterval(pollFallbackTimer);
        };

        liveSocket.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                if (message.type === 'TELEMETRY_UPDATE' || message.type === 'INIT_SNAPSHOT') {
                    handleLiveTelemetryData(message.data);
                }
            } catch (err) {
                console.error("Error processing telemetry packet:", err);
            }
        };

        liveSocket.onclose = () => {
            console.warn("WebSocket disconnected. Falling back to HTTP polling...");
            if (statusText) statusText.innerText = 'POLLING MODE (2.5s)';
            scheduleReconnect();
            startPollingFallback();
        };

        liveSocket.onerror = (err) => {
            console.warn("WebSocket error:", err);
            liveSocket.close();
        };

    } catch (e) {
        console.error("WebSocket init failed:", e);
        startPollingFallback();
    }
}

function scheduleReconnect() {
    clearTimeout(reconnectTimer);
    reconnectTimer = setTimeout(() => {
        console.log("Attempting to reconnect WebSocket...");
        initLiveTelemetryStream();
    }, 4000);
}

function startPollingFallback() {
    clearInterval(pollFallbackTimer);
    fetchLiveSnapshot(); // Immediate call
    pollFallbackTimer = setInterval(fetchLiveSnapshot, 2500);
}

async function fetchLiveSnapshot() {
    try {
        const res = await fetch('/api/telemetry/live');
        if (!res.ok) return;
        const data = await res.json();
        
        if (data.devices) {
            handleLiveTelemetryData(data.devices, data);
        }
    } catch (err) {
        console.warn("Polling error:", err);
    }
}

function handleLiveTelemetryData(devices, metaSummary = null) {
    if (!devices || !devices.length) return;

    // Aggregate statistics across all devices
    const totalKw = devices.reduce((sum, d) => sum + (d.active_power_kw || 0), 0);
    const avgPf = devices.reduce((sum, d) => sum + (d.power_factor || 0.95), 0) / devices.length;
    const avgHz = devices[0]?.frequency_hz || 50.0;
    
    // Update KPI Card Values
    const kpiActive = document.getElementById('kpi-active-power');
    if (kpiActive) kpiActive.innerHTML = `${totalKw.toFixed(1)} <span class="card-unit">kW</span>`;

    const kpiPf = document.getElementById('kpi-power-factor');
    if (kpiPf) {
        kpiPf.innerText = avgPf.toFixed(2);
        kpiPf.style.color = avgPf >= 0.90 ? 'var(--accent-emerald)' : (avgPf >= 0.85 ? 'var(--accent-amber)' : 'var(--accent-rose)');
    }

    const kpiFreq = document.getElementById('kpi-frequency');
    if (kpiFreq) kpiFreq.innerHTML = `${avgHz.toFixed(2)} <span class="card-unit">Hz</span>`;

    const todayKwh = metaSummary ? metaSummary.total_today_energy_kwh : (totalKw * 3.8 + 420.0);
    const todayCost = metaSummary ? metaSummary.estimated_today_cost : (todayKwh * 0.14);

    const kpiToday = document.getElementById('kpi-today-energy');
    if (kpiToday) kpiToday.innerHTML = `${todayKwh.toLocaleString(undefined, {maximumFractionDigits: 1})} <span class="card-unit">kWh</span>`;

    const kpiCost = document.getElementById('kpi-today-cost');
    if (kpiCost) kpiCost.innerText = `$${todayCost.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;

    // Update 3-Phase Gauges (from main incoming transformer TX01 or average)
    const mainTx = devices.find(d => d.device_id === 'ESP32-TX01') || devices[0];
    if (mainTx) {
        const vl1 = document.getElementById('val-phase-l1');
        const vl2 = document.getElementById('val-phase-l2');
        const vl3 = document.getElementById('val-phase-l3');
        if (vl1) vl1.innerText = `${(mainTx.voltage_l1 || mainTx.voltage_v).toFixed(1)} V`;
        if (vl2) vl2.innerText = `${(mainTx.voltage_l2 || mainTx.voltage_v).toFixed(1)} V`;
        if (vl3) vl3.innerText = `${(mainTx.voltage_l3 || mainTx.voltage_v).toFixed(1)} V`;

        const al1 = document.getElementById('amp-phase-l1');
        const al2 = document.getElementById('amp-phase-l2');
        const al3 = document.getElementById('amp-phase-l3');
        if (al1) al1.innerText = `${(mainTx.current_l1 || mainTx.current_a).toFixed(1)} A`;
        if (al2) al2.innerText = `${(mainTx.current_l2 || mainTx.current_a).toFixed(1)} A`;
        if (al3) al3.innerText = `${(mainTx.current_l3 || mainTx.current_a).toFixed(1)} A`;

        // Calculate phase unbalance
        const i1 = mainTx.current_l1 || mainTx.current_a;
        const i2 = mainTx.current_l2 || mainTx.current_a;
        const i3 = mainTx.current_l3 || mainTx.current_a;
        const iAvg = (i1 + i2 + i3) / 3.0 || 1.0;
        const maxDev = Math.max(Math.abs(i1 - iAvg), Math.abs(i2 - iAvg), Math.abs(i3 - iAvg));
        const unbalancePct = (maxDev / iAvg) * 100.0;

        const imbText = document.getElementById('val-imbalance-pct');
        const imbBar = document.getElementById('bar-imbalance');
        if (imbText) {
            imbText.innerText = `${unbalancePct.toFixed(1)}% (${unbalancePct < 10 ? 'Safe' : 'Imbalance Alert'})`;
            imbText.style.color = unbalancePct < 10 ? 'var(--accent-emerald)' : 'var(--accent-rose)';
        }
        if (imbBar) {
            imbBar.style.width = `${Math.min(100, unbalancePct * 3)}%`;
            imbBar.style.background = unbalancePct < 10 ? 'var(--accent-emerald)' : 'var(--accent-rose)';
        }
    }

    // Push into Realtime Chart
    updateRealtimeChart(totalKw);

    // Update Device Fleet Grid
    renderDeviceFleetGrid(devices);
}

function renderDeviceFleetGrid(devices) {
    const grid = document.getElementById('live-device-fleet-grid');
    if (!grid) return;

    grid.innerHTML = devices.map(d => {
        const isAnomaly = d.is_anomaly;
        const cardClass = isAnomaly ? (d.severity === 'CRITICAL' ? 'device-card critical' : 'device-card warning') : 'device-card';
        const badgeClass = isAnomaly ? (d.severity === 'CRITICAL' ? 'status-badge status-critical' : 'status-badge status-warning') : 'status-badge status-online';
        const badgeText = isAnomaly ? (d.anomaly_type || 'ANOMALY') : 'ONLINE';

        return `
            <div class="${cardClass}">
                <div class="device-head">
                    <div>
                        <div class="device-name">${d.device_name || d.device_id}</div>
                        <div class="device-id-tag">${d.device_id} • ${d.location || 'Bay 1'}</div>
                    </div>
                    <span class="${badgeClass}">${badgeText}</span>
                </div>

                <div class="device-metrics">
                    <div class="dm-item">
                        <span class="dm-label">Active Power</span>
                        <span class="dm-value" style="color:var(--accent-cyan);">${(d.active_power_kw || 0).toFixed(1)} kW</span>
                    </div>
                    <div class="dm-item">
                        <span class="dm-label">Line Current</span>
                        <span class="dm-value">${(d.current_a || 0).toFixed(1)} A</span>
                    </div>
                    <div class="dm-item">
                        <span class="dm-label">Power Factor</span>
                        <span class="dm-value" style="color:${(d.power_factor || 0.95) >= 0.85 ? 'var(--accent-emerald)' : 'var(--accent-rose)'};">${(d.power_factor || 0.95).toFixed(2)}</span>
                    </div>
                    <div class="dm-item">
                        <span class="dm-label">Temperature</span>
                        <span class="dm-value" style="color:${(d.temperature_c || 38) > 70 ? 'var(--accent-rose)' : 'var(--text-primary)'};">${(d.temperature_c || 38).toFixed(1)} °C</span>
                    </div>
                </div>

                <div style="display:flex; justify-content:space-between; align-items:center; font-size:11px; color:var(--text-muted);">
                    <span>Voltage: ${(d.voltage_v || 230).toFixed(1)}V</span>
                    <button class="btn btn-outline" style="padding:4px 10px; font-size:11px;" onclick="switchView('simulator')">Inject Fault</button>
                </div>
            </div>
        `;
    }).join('');
}
