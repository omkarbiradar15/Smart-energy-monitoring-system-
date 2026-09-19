import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import random
import math
import json
from datetime import datetime, timedelta
from backend.database import init_db, SessionLocal
from backend.models import User, Device, Telemetry, AnomalyLog, AuditReport, TariffConfig
from backend.auth import hash_password
from backend.report_generator import report_engine

def seed_database():
    """Populate database with rich historical telemetry and realistic operational data."""
    init_db()
    db = SessionLocal()
    try:
        print("🌱 Seeding Smart Energy Monitoring System database...")

        # 1. Users
        if not db.query(User).filter(User.username == "admin").first():
            db.add(User(
                username="admin",
                email="admin@smartenergy.io",
                hashed_password=hash_password("admin123"),
                full_name="Chief Energy Officer",
                role="Admin"
            ))
            db.add(User(
                username="operator",
                email="operator@smartenergy.io",
                hashed_password=hash_password("operator123"),
                full_name="Plant Operations Lead",
                role="Plant Operator"
            ))

        # 2. Devices
        devices_data = [
            {
                "device_id": "ESP32-TX01",
                "name": "Main Incoming Transformer",
                "location": "Substation 1",
                "line_type": "Three-Phase 400V",
                "max_current": 500.0,
                "base_kw": 120.0,
                "status": "ONLINE"
            },
            {
                "device_id": "ESP32-LINE-A",
                "name": "Assembly Line Robot Array",
                "location": "Production Bay 1",
                "line_type": "Three-Phase 400V",
                "max_current": 150.0,
                "base_kw": 45.0,
                "status": "ONLINE"
            },
            {
                "device_id": "ESP32-HVAC-01",
                "name": "Industrial Chiller & HVAC",
                "location": "Utility Roof",
                "line_type": "Three-Phase 400V",
                "max_current": 200.0,
                "base_kw": 60.0,
                "status": "ONLINE"
            },
            {
                "device_id": "ESP32-PRESS-02",
                "name": "Heavy Stamping Press #2",
                "location": "Metal Shop",
                "line_type": "Three-Phase 400V",
                "max_current": 180.0,
                "base_kw": 35.0,
                "status": "WARNING"
            }
        ]

        for d_info in devices_data:
            existing = db.query(Device).filter(Device.device_id == d_info["device_id"]).first()
            if not existing:
                db.add(Device(**d_info))

        db.commit()

        # 3. Seed 48 hours of historical hourly telemetry
        existing_telemetry_count = db.query(Telemetry).count()
        if existing_telemetry_count < 100:
            print("⏳ Generating 48-hour time series electrical telemetry...")
            now = datetime.utcnow()
            telemetry_entries = []

            for h in range(48, 0, -1):
                t_stamp = now - timedelta(hours=h)
                hour_of_day = t_stamp.hour
                diurnal_factor = 0.5 + 0.5 * max(0.2, math.sin((hour_of_day - 6) * math.pi / 12))

                for dev in devices_data:
                    dev_id = dev["device_id"]
                    base_kw = dev["base_kw"]
                    max_i = dev["max_current"]

                    # Inject occasional anomaly spike in history
                    is_anomaly_point = (h in [14, 27] and dev_id == "ESP32-PRESS-02")
                    
                    v_nominal = 230.0 + random.uniform(-2, 2)
                    pf = random.uniform(0.92, 0.97) if not is_anomaly_point else 0.68
                    kw = base_kw * diurnal_factor * random.uniform(0.95, 1.05)
                    
                    if is_anomaly_point:
                        kw *= 1.55

                    i_calc = (kw * 1000.0) / (3.0 * v_nominal * pf)
                    kva = kw / pf
                    kvar = math.sqrt(max(0, kva**2 - kw**2))
                    temp = 36.0 + (kw / base_kw) * 10.0 + random.uniform(0, 3)

                    t_entry = Telemetry(
                        device_id=dev_id,
                        timestamp=t_stamp,
                        voltage_v=round(v_nominal, 2),
                        voltage_l1=round(v_nominal + random.uniform(-1, 1), 2),
                        voltage_l2=round(v_nominal + random.uniform(-1, 1), 2),
                        voltage_l3=round(v_nominal + random.uniform(-1, 1), 2),
                        current_a=round(i_calc, 2),
                        current_l1=round(i_calc * 1.02, 2),
                        current_l2=round(i_calc * 0.98, 2),
                        current_l3=round(i_calc * 1.00, 2),
                        active_power_kw=round(kw, 2),
                        reactive_power_kvar=round(kvar, 2),
                        apparent_power_kva=round(kva, 2),
                        power_factor=round(pf, 3),
                        frequency_hz=round(50.0 + random.uniform(-0.04, 0.04), 2),
                        energy_kwh=round(kw * (48 - h + 1) * 1.0, 2),
                        temperature_c=round(temp, 1),
                        is_anomaly=is_anomaly_point,
                        anomaly_score=0.91 if is_anomaly_point else 0.08
                    )
                    telemetry_entries.append(t_entry)

            db.add_all(telemetry_entries)
            db.commit()

        # 4. Seed Anomaly Logs
        if db.query(AnomalyLog).count() == 0:
            print("🚨 Seeding ML anomaly event logs...")
            db.add(AnomalyLog(
                device_id="ESP32-PRESS-02",
                timestamp=datetime.utcnow() - timedelta(hours=14),
                anomaly_type="LOW_POWER_FACTOR",
                severity="HIGH",
                anomaly_score=0.92,
                description="Power factor dropped to 0.68 on Heavy Stamping Press #2. Capacitor bank de-energized.",
                metrics_snapshot=json.dumps({"voltage_v": 228.4, "current_a": 142.1, "power_factor": 0.68, "kw": 54.2}),
                resolved=False
            ))
            db.add(AnomalyLog(
                device_id="ESP32-HVAC-01",
                timestamp=datetime.utcnow() - timedelta(hours=28),
                anomaly_type="THERMAL_OVERHEAT",
                severity="MEDIUM",
                anomaly_score=0.81,
                description="Chiller condenser cooling loop temperature exceeded 72°C during ambient heatwave.",
                metrics_snapshot=json.dumps({"temperature_c": 73.4, "power_factor": 0.94, "kw": 62.1}),
                resolved=True,
                resolved_at=datetime.utcnow() - timedelta(hours=26),
                resolved_by="Plant Operator",
                action_taken="Cleaned condenser air filters and adjusted fan speed setpoint."
            ))
            db.commit()

        # 5. Generate Initial Energy Audit Reports
        if db.query(AuditReport).count() == 0:
            print("📊 Generating baseline Energy Audit Report...")
            report_engine.generate_report(db=db, period_type="daily")
            report_engine.generate_report(db=db, period_type="weekly")

        print("✅ Database seeding complete.")
    except Exception as e:
        db.rollback()
        print(f"❌ Database seeding error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
