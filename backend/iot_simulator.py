import time
import math
import random
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from backend.config import SIMULATOR_SETTINGS
from backend.database import SessionLocal
from backend.models import Device, Telemetry, AnomalyLog
from backend.ml_engine import ml_detector

logger = logging.getLogger("energy_monitor.iot_simulator")

class IoTSimulator:
    """
    Advanced Industrial IoT Multi-Device Telemetry Generator.
    Simulates real-world 3-phase electrical loads, thermal dynamics,
    and supports dynamic fault injection for testing ML anomaly detection.
    """

    def __init__(self):
        self.running = False
        self.interval = SIMULATOR_SETTINGS.get("interval_seconds", 2.0)
        self.thread: Optional[threading.Thread] = None
        self.cumulative_kwh_map: Dict[str, float] = {}
        self.fault_states: Dict[str, Dict[str, Any]] = {}
        self.latest_telemetry: Dict[str, Dict[str, Any]] = {}
        self.subscribers: List[Any] = [] # WebSocket connection callbacks or queues

    def start(self):
        """Start simulator background loop."""
        if not self.running:
            self.running = True
            self._ensure_devices_exist()
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()
            logger.info("IoT Multi-Device Simulator started.")

    def stop(self):
        """Stop simulator loop."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
            logger.info("IoT Multi-Device Simulator stopped.")

    def inject_fault(self, device_id: str, fault_type: str, duration_seconds: int = 30, intensity: float = 1.0):
        """Inject specific operational anomaly into a device."""
        if fault_type == "normal":
            if device_id in self.fault_states:
                del self.fault_states[device_id]
            logger.info(f"Cleared faults for device {device_id}")
            return {"status": "success", "message": f"Device {device_id} restored to normal operational state."}

        expire_time = time.time() + duration_seconds
        self.fault_states[device_id] = {
            "fault_type": fault_type,
            "expire_time": expire_time,
            "intensity": intensity
        }
        logger.info(f"Injected fault '{fault_type}' on device '{device_id}' for {duration_seconds}s (intensity {intensity})")
        return {
            "status": "success",
            "message": f"Fault '{fault_type}' active on {device_id} for {duration_seconds} seconds.",
            "expire_in_seconds": duration_seconds
        }

    def _ensure_devices_exist(self):
        """Seed default device fleet in the database if not present."""
        db = SessionLocal()
        try:
            for dev_cfg in SIMULATOR_SETTINGS["devices"]:
                existing = db.query(Device).filter(Device.device_id == dev_cfg["device_id"]).first()
                if not existing:
                    dev = Device(
                        device_id=dev_cfg["device_id"],
                        name=dev_cfg["name"],
                        location=dev_cfg["location"],
                        line_type=dev_cfg["line_type"],
                        max_current=dev_cfg["max_current"],
                        base_kw=dev_cfg["base_kw"],
                        status="ONLINE"
                    )
                    db.add(dev)
                    # Initialize cumulative energy
                    self.cumulative_kwh_map[dev_cfg["device_id"]] = random.uniform(1500.0, 8500.0)
                else:
                    if dev_cfg["device_id"] not in self.cumulative_kwh_map:
                        self.cumulative_kwh_map[dev_cfg["device_id"]] = random.uniform(1500.0, 8500.0)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Error seeding simulator devices: {e}")
        finally:
            db.close()

    def _generate_device_reading(self, dev_cfg: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize 3-phase industrial sensor reading with noise and fault injection."""
        dev_id = dev_cfg["device_id"]
        base_kw = dev_cfg.get("base_kw", 50.0)
        max_current = dev_cfg.get("max_current", 100.0)
        
        # Check active fault
        active_fault = None
        if dev_id in self.fault_states:
            fault_info = self.fault_states[dev_id]
            if time.time() < fault_info["expire_time"]:
                active_fault = fault_info["fault_type"]
                intensity = fault_info.get("intensity", 1.0)
            else:
                del self.fault_states[dev_id]

        # Time-of-day industrial load factor (sinusoidal diurnal curve)
        now = datetime.utcnow()
        hour_frac = now.hour + (now.minute / 60.0)
        # Peak between 10am-16pm, lower at night (0.35 to 1.1)
        load_multiplier = 0.65 + 0.35 * math.sin((hour_frac - 6) * math.pi / 12)
        load_multiplier = max(0.35, min(1.15, load_multiplier))

        # Base nominal values with minor industrial grid jitter
        v_nominal = 230.0
        v_jitter = random.gauss(0, 1.2)
        v_l1 = v_nominal + v_jitter + random.gauss(0, 0.5)
        v_l2 = v_nominal + v_jitter + random.gauss(0, 0.5)
        v_l3 = v_nominal + v_jitter + random.gauss(0, 0.5)
        v_avg = (v_l1 + v_l2 + v_l3) / 3.0

        target_kw = base_kw * load_multiplier + random.gauss(0, base_kw * 0.05)
        target_kw = max(2.0, target_kw)

        pf = max(0.88, min(0.98, random.gauss(0.94, 0.02)))
        hz = round(50.0 + random.gauss(0, 0.05), 2)
        temp = round(38.0 + (target_kw / base_kw) * 12.0 + random.gauss(0, 1.0), 1)

        # Calculate balanced phase currents: P = sqrt(3) * V_ll * I * PF = 3 * V_ln * I * PF
        i_per_phase = (target_kw * 1000.0) / (3.0 * v_avg * pf)
        i_l1 = round(i_per_phase + random.gauss(0, 0.8), 2)
        i_l2 = round(i_per_phase + random.gauss(0, 0.8), 2)
        i_l3 = round(i_per_phase + random.gauss(0, 0.8), 2)

        # APPLY FAULT INJECTIONS
        if active_fault == "overcurrent":
            multiplier = 1.45 * intensity
            i_l1 *= multiplier
            i_l2 *= multiplier
            i_l3 *= multiplier
            target_kw *= multiplier
            temp += 18.0 * intensity
        elif active_fault == "voltage_sag":
            sag_drop = 45.0 * intensity
            v_l1 -= sag_drop
            v_l2 -= sag_drop
            v_l3 -= sag_drop
            v_avg = (v_l1 + v_l2 + v_l3) / 3.0
            # Motors draw more current during sag to maintain power
            i_l1 *= 1.2
            i_l2 *= 1.2
            i_l3 *= 1.2
        elif active_fault == "low_power_factor":
            pf = max(0.55, 0.70 - (0.12 * intensity))
            # Lower PF increases apparent current
            i_l1 = (target_kw * 1000.0) / (3.0 * v_avg * pf)
            i_l2 = i_l1 * 0.98
            i_l3 = i_l1 * 1.02
        elif active_fault == "phase_loss":
            # Blown fuse on Phase 2
            i_l2 = 0.0
            v_l2 *= 0.6
            i_l1 *= 1.6 # Phase 1 and 3 take over the load
            i_l3 *= 1.6
            temp += 15.0
        elif active_fault == "high_temp":
            temp = 82.0 + (10.0 * intensity) + random.uniform(0, 3)
        elif active_fault == "vampire_load":
            target_kw = base_kw * 1.8 # Unexpected night run
            i_l1 *= 1.8
            i_l2 *= 1.8
            i_l3 *= 1.8

        total_current = round((i_l1 + i_l2 + i_l3) / 3.0, 2)
        active_power_kw = round(target_kw, 2)
        apparent_power_kva = round(active_power_kw / pf, 2) if pf > 0 else active_power_kw
        reactive_power_kvar = round(math.sqrt(max(0, apparent_power_kva**2 - active_power_kw**2)), 2)

        # Accumulate kWh: delta_kwh = active_power_kw * (interval / 3600)
        current_kwh = self.cumulative_kwh_map.get(dev_id, 2500.0)
        delta_kwh = active_power_kw * (self.interval / 3600.0)
        new_kwh = round(current_kwh + delta_kwh, 4)
        self.cumulative_kwh_map[dev_id] = new_kwh

        reading = {
            "device_id": dev_id,
            "timestamp": now.isoformat(),
            "voltage_v": round(v_avg, 2),
            "voltage_l1": round(v_l1, 2),
            "voltage_l2": round(v_l2, 2),
            "voltage_l3": round(v_l3, 2),
            "current_a": total_current,
            "current_l1": round(i_l1, 2),
            "current_l2": round(i_l2, 2),
            "current_l3": round(i_l3, 2),
            "active_power_kw": active_power_kw,
            "reactive_power_kvar": reactive_power_kvar,
            "apparent_power_kva": apparent_power_kva,
            "power_factor": round(pf, 2),
            "frequency_hz": hz,
            "energy_kwh": new_kwh,
            "temperature_c": round(temp, 1),
            "device_name": dev_cfg.get("name", dev_id),
            "location": dev_cfg.get("location", "Plant")
        }

        return reading

    def _run_loop(self):
        """Continuous background loop persisting telemetry and pushing real-time events."""
        while self.running:
            try:
                db = SessionLocal()
                readings_batch = []
                anomalies_to_record = []

                for dev_cfg in SIMULATOR_SETTINGS["devices"]:
                    reading = self._generate_device_reading(dev_cfg)
                    dev_id = dev_cfg["device_id"]
                    self.latest_telemetry[dev_id] = reading

                    # Analyze with ML Anomaly Detector
                    is_anomaly, score, a_type, severity, desc = ml_detector.analyze_reading(
                        telemetry_dict=reading,
                        device_max_current=dev_cfg.get("max_current", 100.0),
                        device_base_kw=dev_cfg.get("base_kw", 50.0)
                    )

                    reading["is_anomaly"] = is_anomaly
                    reading["anomaly_score"] = score
                    reading["anomaly_type"] = a_type
                    reading["severity"] = severity

                    # Create DB Telemetry record
                    tel_record = Telemetry(
                        device_id=dev_id,
                        timestamp=datetime.utcnow(),
                        voltage_v=reading["voltage_v"],
                        voltage_l1=reading["voltage_l1"],
                        voltage_l2=reading["voltage_l2"],
                        voltage_l3=reading["voltage_l3"],
                        current_a=reading["current_a"],
                        current_l1=reading["current_l1"],
                        current_l2=reading["current_l2"],
                        current_l3=reading["current_l3"],
                        active_power_kw=reading["active_power_kw"],
                        reactive_power_kvar=reading["reactive_power_kvar"],
                        apparent_power_kva=reading["apparent_power_kva"],
                        power_factor=reading["power_factor"],
                        frequency_hz=reading["frequency_hz"],
                        energy_kwh=reading["energy_kwh"],
                        temperature_c=reading["temperature_c"],
                        is_anomaly=is_anomaly,
                        anomaly_score=score
                    )
                    readings_batch.append(tel_record)

                    # Update device status
                    dev = db.query(Device).filter(Device.device_id == dev_id).first()
                    if dev:
                        if is_anomaly:
                            dev.status = "CRITICAL" if severity == "CRITICAL" else "WARNING"
                        else:
                            dev.status = "ONLINE"
                        dev.updated_at = datetime.utcnow()

                    if is_anomaly and a_type:
                        # Throttle consecutive identical anomaly logs (avoid flooding DB every 2 seconds)
                        recent_alert = db.query(AnomalyLog).filter(
                            AnomalyLog.device_id == dev_id,
                            AnomalyLog.anomaly_type == a_type,
                            AnomalyLog.resolved == False,
                            AnomalyLog.timestamp > datetime.utcnow() - timedelta(minutes=2)
                        ).first()

                        if not recent_alert:
                            import json
                            anomaly_record = AnomalyLog(
                                device_id=dev_id,
                                timestamp=datetime.utcnow(),
                                anomaly_type=a_type,
                                severity=severity or "MEDIUM",
                                anomaly_score=score,
                                description=desc or "Anomaly detected by ML engine",
                                metrics_snapshot=json.dumps(reading),
                                resolved=False
                            )
                            anomalies_to_record.append(anomaly_record)

                db.add_all(readings_batch)
                if anomalies_to_record:
                    db.add_all(anomalies_to_record)
                db.commit()
                db.close()

                # Notify WebSocket subscribers
                for subscriber in list(self.subscribers):
                    try:
                        subscriber(list(self.latest_telemetry.values()))
                    except Exception as sub_err:
                        logger.debug(f"Subscriber push error: {sub_err}")

            except Exception as e:
                logger.error(f"Error in IoT simulator loop: {e}")

            time.sleep(self.interval)

    def add_subscriber(self, callback):
        if callback not in self.subscribers:
            self.subscribers.append(callback)

    def remove_subscriber(self, callback):
        if callback in self.subscribers:
            self.subscribers.remove(callback)

# Singleton Instance
iot_simulator = IoTSimulator()
