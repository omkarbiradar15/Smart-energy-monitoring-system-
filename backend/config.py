import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "database"
DB_DIR.mkdir(exist_ok=True)

DATABASE_PATH = DB_DIR / "energy_monitor.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATABASE_PATH}")

# Security & JWT
SECRET_KEY = os.getenv("SECRET_KEY", "smart-energy-monitoring-super-secret-jwt-key-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Energy & Tariff Defaults (Industrial Rate Tier Structure)
DEFAULT_TARIFF = {
    "peak_rate_per_kwh": 0.18,      # Peak hours (08:00 - 20:00)
    "off_peak_rate_per_kwh": 0.08,  # Off-peak hours (20:00 - 08:00)
    "demand_charge_per_kw": 12.50,  # Max Demand charge ($/kW)
    "currency": "USD",
    "currency_symbol": "$",
    "co2_kg_per_kwh": 0.42          # Carbon emission factor (Grid avg)
}

# Machine Learning & Anomaly Detection Parameters
ML_SETTINGS = {
    "contamination": 0.05,          # Isolation Forest expected anomaly ratio
    "voltage_nominal": 230.0,       # Single-phase nominal (or 400V 3-phase line-to-line)
    "voltage_tolerance_pct": 10.0,  # ±10% acceptable voltage variation
    "frequency_nominal": 50.0,      # 50 Hz or 60 Hz grid
    "frequency_tolerance_hz": 1.0,
    "min_power_factor": 0.85,       # Under 0.85 incurs utility penalty
    "max_temperature_c": 75.0       # Industrial motor/panel alert limit
}

# IoT Simulator Settings
SIMULATOR_SETTINGS = {
    "interval_seconds": 2.0,        # Broadcast & ingestion tick
    "devices": [
        {
            "device_id": "ESP32-TX01",
            "name": "Main Incoming Transformer",
            "location": "Substation 1",
            "line_type": "Three-Phase 400V",
            "max_current": 500.0,
            "base_kw": 120.0
        },
        {
            "device_id": "ESP32-LINE-A",
            "name": "Assembly Line Robot Array",
            "location": "Production Bay 1",
            "line_type": "Three-Phase 400V",
            "max_current": 150.0,
            "base_kw": 45.0
        },
        {
            "device_id": "ESP32-HVAC-01",
            "name": "Industrial Chiller & HVAC",
            "location": "Utility Roof",
            "line_type": "Three-Phase 400V",
            "max_current": 200.0,
            "base_kw": 60.0
        },
        {
            "device_id": "ESP32-PRESS-02",
            "name": "Heavy Stamping Press #2",
            "location": "Metal Shop",
            "line_type": "Three-Phase 400V",
            "max_current": 180.0,
            "base_kw": 35.0
        }
    ]
}
