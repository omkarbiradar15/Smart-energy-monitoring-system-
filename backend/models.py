from datetime import datetime
import json
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    ForeignKey, Text, Index
)
from sqlalchemy.orm import relationship
from backend.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(120), default="")
    role = Column(String(32), default="Energy Manager") # Admin, Energy Manager, Plant Operator, Auditor
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(64), unique=True, index=True, nullable=False) # e.g., ESP32-TX01
    name = Column(String(120), nullable=False)
    location = Column(String(120), nullable=False)
    line_type = Column(String(64), default="Three-Phase 400V") # Single-Phase 230V or Three-Phase 400V
    max_current = Column(Float, default=100.0) # Amps limit
    base_kw = Column(Float, default=50.0)
    status = Column(String(32), default="ONLINE") # ONLINE, WARNING, CRITICAL, OFFLINE
    ip_address = Column(String(64), default="192.168.1.100")
    firmware_version = Column(String(32), default="v2.4.1-esp32")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    telemetry = relationship("Telemetry", back_populates="device", cascade="all, delete-orphan")
    anomalies = relationship("AnomalyLog", back_populates="device", cascade="all, delete-orphan")

class Telemetry(Base):
    __tablename__ = "telemetry"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(64), ForeignKey("devices.device_id"), index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # 3-Phase Electrical Parameters
    voltage_v = Column(Float, nullable=False)             # Line Voltage (e.g. 230V / 400V)
    voltage_l1 = Column(Float, default=230.0)
    voltage_l2 = Column(Float, default=230.0)
    voltage_l3 = Column(Float, default=230.0)
    
    current_a = Column(Float, nullable=False)             # Total / avg current
    current_l1 = Column(Float, default=0.0)
    current_l2 = Column(Float, default=0.0)
    current_l3 = Column(Float, default=0.0)
    
    active_power_kw = Column(Float, nullable=False)       # Real Power (P) in kW
    reactive_power_kvar = Column(Float, default=0.0)     # Reactive Power (Q) in kVAR
    apparent_power_kva = Column(Float, default=0.0)      # Apparent Power (S) in kVA
    
    power_factor = Column(Float, default=0.95)           # cos(phi) 0.0 - 1.0
    frequency_hz = Column(Float, default=50.0)           # Grid Frequency (49.5 - 50.5 Hz)
    energy_kwh = Column(Float, default=0.0)              # Cumulative Energy (kWh)
    temperature_c = Column(Float, default=38.5)          # Panel / Transformer Temp
    
    # Anomaly flag tagged by ML engine
    is_anomaly = Column(Boolean, default=False)
    anomaly_score = Column(Float, default=0.0)

    device = relationship("Device", back_populates="telemetry")

    __table_args__ = (
        Index("idx_device_timestamp", "device_id", "timestamp"),
    )

class AnomalyLog(Base):
    __tablename__ = "anomaly_logs"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(64), ForeignKey("devices.device_id"), index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    anomaly_type = Column(String(64), nullable=False) # e.g. OVERCURRENT, VOLTAGE_SAG, LOW_POWER_FACTOR, VAMPIRE_LOAD, PHASE_IMBALANCE, OVERHEATING
    severity = Column(String(32), default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    anomaly_score = Column(Float, default=0.85)       # 0.0 to 1.0 (ML confidence)
    description = Column(Text, nullable=False)
    metrics_snapshot = Column(Text, default="{}")    # JSON string snapshot of voltage, current, etc.
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(64), nullable=True)
    action_taken = Column(Text, nullable=True)

    device = relationship("Device", back_populates="anomalies")

    @property
    def metrics_dict(self):
        try:
            return json.loads(self.metrics_snapshot)
        except Exception:
            return {}

class AuditReport(Base):
    __tablename__ = "audit_reports"

    id = Column(Integer, primary_key=True, index=True)
    report_uid = Column(String(64), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Aggregated Energy & Financials
    total_energy_kwh = Column(Float, nullable=False)
    peak_demand_kw = Column(Float, nullable=False)
    avg_power_factor = Column(Float, default=0.92)
    total_cost = Column(Float, nullable=False)
    carbon_emissions_kg = Column(Float, nullable=False)
    trees_equivalent = Column(Float, default=0.0)
    
    efficiency_grade = Column(String(8), default="B+") # A+, A, B+, B, C, D, F
    anomaly_count = Column(Integer, default=0)
    estimated_monthly_savings = Column(Float, default=0.0)
    
    # Detailed payload (stored as JSON)
    summary_json = Column(Text, default="{}")
    breakdown_by_device_json = Column(Text, default="[]")
    recommendations_json = Column(Text, default="[]")
    
    generated_by = Column(String(64), default="Automated EMS Engine")
    created_at = Column(DateTime, default=datetime.utcnow)

class TariffConfig(Base):
    __tablename__ = "tariff_configs"

    id = Column(Integer, primary_key=True, index=True)
    tariff_name = Column(String(64), default="Industrial Tier-1")
    peak_rate = Column(Float, default=0.18)         # $/kWh
    off_peak_rate = Column(Float, default=0.08)     # $/kWh
    demand_charge = Column(Float, default=12.50)    # $/kW
    co2_factor = Column(Float, default=0.42)        # kg/kWh
    currency = Column(String(16), default="USD")
    currency_symbol = Column(String(8), default="$")
    is_active = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
