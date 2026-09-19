from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

# ----------------- Auth Schemas -----------------
class UserLogin(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = ""
    role: Optional[str] = "Energy Manager"

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# ----------------- Device Schemas -----------------
class DeviceCreate(BaseModel):
    device_id: str
    name: str
    location: str
    line_type: Optional[str] = "Three-Phase 400V"
    max_current: Optional[float] = 100.0
    base_kw: Optional[float] = 50.0
    ip_address: Optional[str] = "192.168.1.100"
    firmware_version: Optional[str] = "v2.4.1-esp32"

class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    line_type: Optional[str] = None
    max_current: Optional[float] = None
    base_kw: Optional[float] = None
    status: Optional[str] = None

class DeviceResponse(BaseModel):
    id: int
    device_id: str
    name: str
    location: str
    line_type: str
    max_current: float
    base_kw: float
    status: str
    ip_address: str
    firmware_version: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ----------------- Telemetry Schemas -----------------
class TelemetryCreate(BaseModel):
    device_id: str
    timestamp: Optional[datetime] = None
    voltage_v: float
    voltage_l1: Optional[float] = None
    voltage_l2: Optional[float] = None
    voltage_l3: Optional[float] = None
    current_a: float
    current_l1: Optional[float] = None
    current_l2: Optional[float] = None
    current_l3: Optional[float] = None
    active_power_kw: float
    reactive_power_kvar: Optional[float] = 0.0
    apparent_power_kva: Optional[float] = 0.0
    power_factor: Optional[float] = 0.95
    frequency_hz: Optional[float] = 50.0
    energy_kwh: Optional[float] = 0.0
    temperature_c: Optional[float] = 38.5

class TelemetryResponse(BaseModel):
    id: int
    device_id: str
    timestamp: datetime
    voltage_v: float
    voltage_l1: float
    voltage_l2: float
    voltage_l3: float
    current_a: float
    current_l1: float
    current_l2: float
    current_l3: float
    active_power_kw: float
    reactive_power_kvar: float
    apparent_power_kva: float
    power_factor: float
    frequency_hz: float
    energy_kwh: float
    temperature_c: float
    is_anomaly: bool
    anomaly_score: float

    class Config:
        from_attributes = True

class LiveDashboardSummary(BaseModel):
    total_active_power_kw: float
    total_today_energy_kwh: float
    estimated_today_cost: float
    avg_power_factor: float
    grid_frequency_hz: float
    system_status: str # HEALTHY, WARNING, CRITICAL
    active_anomalies_count: int
    devices_online: int
    total_devices: int
    devices: List[Dict[str, Any]]

# ----------------- Anomaly Schemas -----------------
class AnomalyResponse(BaseModel):
    id: int
    device_id: str
    timestamp: datetime
    anomaly_type: str
    severity: str
    anomaly_score: float
    description: str
    metrics_snapshot: str
    resolved: bool
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    action_taken: Optional[str] = None

    class Config:
        from_attributes = True

class AnomalyResolveRequest(BaseModel):
    action_taken: str

# ----------------- Report Schemas -----------------
class ReportGenerateRequest(BaseModel):
    period: str = "daily" # daily, weekly, monthly, custom
    device_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class ReportResponse(BaseModel):
    id: int
    report_uid: str
    title: str
    period_start: datetime
    period_end: datetime
    total_energy_kwh: float
    peak_demand_kw: float
    avg_power_factor: float
    total_cost: float
    carbon_emissions_kg: float
    trees_equivalent: float
    efficiency_grade: str
    anomaly_count: int
    estimated_monthly_savings: float
    summary_json: str
    breakdown_by_device_json: str
    recommendations_json: str
    generated_by: str
    created_at: datetime

    class Config:
        from_attributes = True

# ----------------- Fault Injection / Simulator -----------------
class FaultInjectionRequest(BaseModel):
    device_id: str
    fault_type: str # normal, overcurrent, voltage_sag, low_power_factor, phase_loss, high_temp, vampire_load
    duration_seconds: Optional[int] = 30
    intensity: Optional[float] = 1.0 # 0.5 to 2.0
