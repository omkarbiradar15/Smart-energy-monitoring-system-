-- =========================================================================
-- Smart Energy Monitoring & Industrial Anomaly Detection System Schema
-- Supported Engines: SQLite, MySQL 8+, PostgreSQL 14+
-- =========================================================================

-- 1. Users & RBAC
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(64) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(120) DEFAULT '',
    role VARCHAR(32) DEFAULT 'Energy Manager',
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. IoT Device Fleet & Transformers
CREATE TABLE IF NOT EXISTS devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id VARCHAR(64) NOT NULL UNIQUE,
    name VARCHAR(120) NOT NULL,
    location VARCHAR(120) NOT NULL,
    line_type VARCHAR(64) DEFAULT 'Three-Phase 400V',
    max_current FLOAT DEFAULT 100.0,
    base_kw FLOAT DEFAULT 50.0,
    status VARCHAR(32) DEFAULT 'ONLINE',
    ip_address VARCHAR(64) DEFAULT '192.168.1.100',
    firmware_version VARCHAR(32) DEFAULT 'v2.4.1-esp32',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Time-Series Electrical Telemetry
CREATE TABLE IF NOT EXISTS telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id VARCHAR(64) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    voltage_v FLOAT NOT NULL,
    voltage_l1 FLOAT DEFAULT 230.0,
    voltage_l2 FLOAT DEFAULT 230.0,
    voltage_l3 FLOAT DEFAULT 230.0,
    current_a FLOAT NOT NULL,
    current_l1 FLOAT DEFAULT 0.0,
    current_l2 FLOAT DEFAULT 0.0,
    current_l3 FLOAT DEFAULT 0.0,
    active_power_kw FLOAT NOT NULL,
    reactive_power_kvar FLOAT DEFAULT 0.0,
    apparent_power_kva FLOAT DEFAULT 0.0,
    power_factor FLOAT DEFAULT 0.95,
    frequency_hz FLOAT DEFAULT 50.0,
    energy_kwh FLOAT DEFAULT 0.0,
    temperature_c FLOAT DEFAULT 38.5,
    is_anomaly BOOLEAN DEFAULT 0,
    anomaly_score FLOAT DEFAULT 0.0,
    FOREIGN KEY (device_id) REFERENCES devices (device_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_telemetry_device_time ON telemetry (device_id, timestamp);

-- 4. Machine Learning Anomaly Event Logs
CREATE TABLE IF NOT EXISTS anomaly_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id VARCHAR(64) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    anomaly_type VARCHAR(64) NOT NULL,
    severity VARCHAR(32) DEFAULT 'MEDIUM',
    anomaly_score FLOAT DEFAULT 0.85,
    description TEXT NOT NULL,
    metrics_snapshot TEXT DEFAULT '{}',
    resolved BOOLEAN DEFAULT 0,
    resolved_at TIMESTAMP NULL,
    resolved_by VARCHAR(64) NULL,
    action_taken TEXT NULL,
    FOREIGN KEY (device_id) REFERENCES devices (device_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_anomalies_resolved_time ON anomaly_logs (resolved, timestamp);

-- 5. Automated Energy Audit Reports
CREATE TABLE IF NOT EXISTS audit_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_uid VARCHAR(64) NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL,
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    total_energy_kwh FLOAT NOT NULL,
    peak_demand_kw FLOAT NOT NULL,
    avg_power_factor FLOAT DEFAULT 0.92,
    total_cost FLOAT NOT NULL,
    carbon_emissions_kg FLOAT NOT NULL,
    trees_equivalent FLOAT DEFAULT 0.0,
    efficiency_grade VARCHAR(8) DEFAULT 'B+',
    anomaly_count INTEGER DEFAULT 0,
    estimated_monthly_savings FLOAT DEFAULT 0.0,
    summary_json TEXT DEFAULT '{}',
    breakdown_by_device_json TEXT DEFAULT '[]',
    recommendations_json TEXT DEFAULT '[]',
    generated_by VARCHAR(64) DEFAULT 'Automated EMS Engine',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Tariff and Pricing Configurations
CREATE TABLE IF NOT EXISTS tariff_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tariff_name VARCHAR(64) DEFAULT 'Industrial Tier-1',
    peak_rate FLOAT DEFAULT 0.18,
    off_peak_rate FLOAT DEFAULT 0.08,
    demand_charge FLOAT DEFAULT 12.50,
    co2_factor FLOAT DEFAULT 0.42,
    currency VARCHAR(16) DEFAULT 'USD',
    currency_symbol VARCHAR(8) DEFAULT '$',
    is_active BOOLEAN DEFAULT 1,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
