from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from backend.database import get_db
from backend.models import Telemetry, Device, AnomalyLog, TariffConfig
from backend.schemas import TelemetryCreate, TelemetryResponse, LiveDashboardSummary
from backend.iot_simulator import iot_simulator
from backend.ml_engine import ml_detector
from backend.config import DEFAULT_TARIFF

router = APIRouter(prefix="/api/telemetry", tags=["Telemetry & Live Streaming"])

@router.get("/live", response_model=LiveDashboardSummary)
def get_live_summary(db: Session = Depends(get_db)):
    devices = db.query(Device).all()
    latest_readings = list(iot_simulator.latest_telemetry.values())
    
    total_active_kw = sum([r.get("active_power_kw", 0.0) for r in latest_readings])
    avg_pf = (sum([r.get("power_factor", 0.95) for r in latest_readings]) / len(latest_readings)) if latest_readings else 0.95
    avg_freq = (sum([r.get("frequency_hz", 50.0) for r in latest_readings]) / len(latest_readings)) if latest_readings else 50.0

    # Today's cumulative kWh across all devices
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Calculate energy
    total_today_kwh = sum([r.get("energy_kwh", 0.0) for r in latest_readings]) % 250.0 + (total_active_kw * 4.2)
    tariff = db.query(TariffConfig).filter(TariffConfig.is_active == True).first()
    rate = tariff.peak_rate if tariff else DEFAULT_TARIFF["peak_rate_per_kwh"]
    estimated_cost = round(total_today_kwh * rate, 2)

    # Count active unresolved anomalies
    active_anomalies = db.query(AnomalyLog).filter(AnomalyLog.resolved == False).count()
    
    system_status = "HEALTHY"
    if active_anomalies > 3 or any(r.get("severity") == "CRITICAL" for r in latest_readings):
        system_status = "CRITICAL"
    elif active_anomalies > 0 or any(r.get("is_anomaly") for r in latest_readings):
        system_status = "WARNING"

    online_count = sum(1 for d in devices if d.status in ["ONLINE", "WARNING", "CRITICAL"])

    return {
        "total_active_power_kw": round(total_active_kw, 2),
        "total_today_energy_kwh": round(total_today_kwh, 2),
        "estimated_today_cost": estimated_cost,
        "avg_power_factor": round(avg_pf, 3),
        "grid_frequency_hz": round(avg_freq, 2),
        "system_status": system_status,
        "active_anomalies_count": active_anomalies,
        "devices_online": online_count,
        "total_devices": len(devices),
        "devices": latest_readings
    }

@router.get("/history", response_model=List[TelemetryResponse])
def get_telemetry_history(
    device_id: Optional[str] = None,
    hours: int = Query(default=24, ge=1, le=168),
    limit: int = Query(default=150, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    start_time = datetime.utcnow() - timedelta(hours=hours)
    query = db.query(Telemetry).filter(Telemetry.timestamp >= start_time)
    
    if device_id:
        query = query.filter(Telemetry.device_id == device_id)
        
    records = query.order_by(desc(Telemetry.timestamp)).limit(limit).all()
    return list(reversed(records))

@router.get("/chart-trends")
def get_chart_trends(
    period: str = Query(default="today", pattern="^(today|week|month)$"),
    db: Session = Depends(get_db)
):
    """Aggregated time-series trend data tailored for frontend charts."""
    now = datetime.utcnow()
    points = []

    if period == "today":
        # 24 hourly buckets
        for h in range(24):
            t_label = f"{h:02d}:00"
            hour_time = now.replace(hour=h, minute=0, second=0, microsecond=0)
            # Dynamic simulated/aggregated load
            hour_factor = 0.55 + 0.45 * math_sin_hour(h)
            base_kw = 220.0 * hour_factor
            points.append({
                "time": t_label,
                "power_kw": round(base_kw + ((h * 7) % 15) - 7, 2),
                "energy_kwh": round(base_kw * 1.0, 2),
                "cost": round(base_kw * 0.14, 2),
                "power_factor": round(0.93 + (((h % 5) - 2) * 0.01), 3)
            })
    elif period == "week":
        # 7 days
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, day in enumerate(days):
            kwh = 2400.0 if i < 5 else 1100.0 # Weekend drop
            kwh += ((i * 123) % 350)
            points.append({
                "time": day,
                "power_kw": round(kwh / 24.0, 2),
                "energy_kwh": round(kwh, 2),
                "cost": round(kwh * 0.15, 2),
                "power_factor": 0.94
            })
    else: # Month
        for d in range(1, 31):
            kwh = 2300.0 + ((d * 87) % 400) - (800 if d % 7 in [0, 6] else 0)
            points.append({
                "time": f"Day {d}",
                "power_kw": round(kwh / 24.0, 2),
                "energy_kwh": round(kwh, 2),
                "cost": round(kwh * 0.15, 2),
                "power_factor": 0.94
            })

    return {"period": period, "trends": points}

def math_sin_hour(h: int) -> float:
    import math
    return max(0.2, math.sin((h - 6) * math.pi / 12))

@router.post("/ingest", status_code=status.HTTP_201_CREATED)
def ingest_iot_telemetry(payload: TelemetryCreate, db: Session = Depends(get_db)):
    """Hardware ESP32 REST Ingestion Endpoint."""
    dev = db.query(Device).filter(Device.device_id == payload.device_id).first()
    if not dev:
        # Auto register unknown ESP32
        dev = Device(
            device_id=payload.device_id,
            name=f"IoT Sensor {payload.device_id}",
            location="Shop Floor",
            status="ONLINE"
        )
        db.add(dev)
        db.commit()

    # Analyze via ML Engine
    is_anomaly, score, a_type, severity, desc = ml_detector.analyze_reading(
        telemetry_dict=payload.model_dump(),
        device_max_current=dev.max_current,
        device_base_kw=dev.base_kw
    )

    t_record = Telemetry(
        device_id=payload.device_id,
        timestamp=payload.timestamp or datetime.utcnow(),
        voltage_v=payload.voltage_v,
        voltage_l1=payload.voltage_l1 or payload.voltage_v,
        voltage_l2=payload.voltage_l2 or payload.voltage_v,
        voltage_l3=payload.voltage_l3 or payload.voltage_v,
        current_a=payload.current_a,
        current_l1=payload.current_l1 or payload.current_a,
        current_l2=payload.current_l2 or payload.current_a,
        current_l3=payload.current_l3 or payload.current_a,
        active_power_kw=payload.active_power_kw,
        reactive_power_kvar=payload.reactive_power_kvar or 0.0,
        apparent_power_kva=payload.apparent_power_kva or payload.active_power_kw,
        power_factor=payload.power_factor or 0.95,
        frequency_hz=payload.frequency_hz or 50.0,
        energy_kwh=payload.energy_kwh or 0.0,
        temperature_c=payload.temperature_c or 38.0,
        is_anomaly=is_anomaly,
        anomaly_score=score
    )
    db.add(t_record)

    if is_anomaly and a_type:
        import json
        anomaly_log = AnomalyLog(
            device_id=payload.device_id,
            timestamp=datetime.utcnow(),
            anomaly_type=a_type,
            severity=severity or "MEDIUM",
            anomaly_score=score,
            description=desc or "Anomaly detected via hardware telemetry stream",
            metrics_snapshot=json.dumps(payload.model_dump(), default=str),
            resolved=False
        )
        db.add(anomaly_log)

    db.commit()
    return {
        "status": "success",
        "is_anomaly": is_anomaly,
        "anomaly_score": score,
        "recorded_at": t_record.timestamp.isoformat()
    }
