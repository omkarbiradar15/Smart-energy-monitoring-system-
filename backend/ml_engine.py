import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional
from datetime import datetime
from sklearn.ensemble import IsolationForest
from backend.config import ML_SETTINGS

logger = logging.getLogger("energy_monitor.ml_engine")

class EnergyAnomalyDetector:
    """
    Hybrid Machine Learning and Industrial Domain Rules Anomaly Detection Engine.
    Uses Scikit-Learn IsolationForest alongside electrical physics boundaries.
    """

    def __init__(self, contamination: float = 0.05):
        self.contamination = contamination
        self.model = IsolationForest(
            n_estimators=100,
            contamination=contamination,
            random_state=42,
            bootstrap=True
        )
        self.is_trained = False
        self.baseline_stats = {}
        self._initialize_baseline_model()

    def _initialize_baseline_model(self):
        """Train baseline model on synthetic industrial standard profile."""
        try:
            # Generate synthetic normal operational distribution (1000 samples)
            np.random.seed(42)
            n_samples = 1000
            
            # Normal distribution of electrical parameters (3-phase industrial loads)
            voltage = np.random.normal(loc=230.0, scale=4.0, size=n_samples)
            current = np.random.uniform(low=10.0, high=120.0, size=n_samples)
            power_factor = np.random.uniform(low=0.90, high=0.99, size=n_samples)
            # 3-phase real power: P = 3 * V_ln * I * PF / 1000
            active_power = (3.0 * voltage * current * power_factor) / 1000.0
            temperature = np.random.normal(loc=42.0, scale=6.0, size=n_samples)
            phase_imbalance = np.random.uniform(low=0.2, high=5.0, size=n_samples)

            X_train = np.column_stack([
                active_power,
                current,
                voltage,
                power_factor,
                temperature,
                phase_imbalance
            ])

            self.model.fit(X_train)
            self.is_trained = True
            
            self.baseline_stats = {
                "mean_kw": float(np.mean(active_power)),
                "std_kw": float(np.std(active_power)),
                "mean_current": float(np.mean(current)),
                "std_current": float(np.std(current)),
                "mean_pf": float(np.mean(power_factor)),
                "mean_temp": float(np.mean(temperature))
            }
            logger.info("ML Anomaly Detection baseline model trained successfully.")
        except Exception as e:
            logger.error(f"Error training ML baseline model: {e}")

    def compute_phase_imbalance(self, l1: float, l2: float, l3: float) -> float:
        """Calculate percentage current/voltage unbalance according to NEMA standard."""
        avg = (l1 + l2 + l3) / 3.0
        if avg == 0:
            return 0.0
        max_dev = max(abs(l1 - avg), abs(l2 - avg), abs(l3 - avg))
        return round((max_dev / avg) * 100.0, 2)

    def analyze_reading(
        self,
        telemetry_dict: Dict[str, Any],
        device_max_current: float = 100.0,
        device_base_kw: float = 50.0
    ) -> Tuple[bool, float, Optional[str], Optional[str], Optional[str]]:
        """
        Evaluate single IoT telemetry packet for anomalies.
        Returns:
            is_anomaly: bool
            anomaly_score: float (0.0 normal -> 1.0 critical anomaly)
            anomaly_type: str or None
            severity: str (LOW, MEDIUM, HIGH, CRITICAL) or None
            description: str or None
        """
        def get_val(key, default):
            v = telemetry_dict.get(key)
            return float(v) if v is not None else float(default)

        v = get_val("voltage_v", 230.0)
        i = get_val("current_a", 0.0)
        kw = get_val("active_power_kw", 0.0)
        pf = get_val("power_factor", 0.95)
        hz = get_val("frequency_hz", 50.0)
        temp = get_val("temperature_c", 38.0)
        
        i_l1 = get_val("current_l1", i)
        i_l2 = get_val("current_l2", i)
        i_l3 = get_val("current_l3", i)
        
        imbalance_pct = self.compute_phase_imbalance(i_l1, i_l2, i_l3)

        # 1. Physical / Electrical Rule Checks (High Precision Industrial Heuristics)
        detected_types = []
        highest_severity = "LOW"
        base_score = 0.0

        # Check Overcurrent / Load Spike
        if i > (device_max_current * 1.15):
            detected_types.append("OVERCURRENT_SURGE")
            highest_severity = "CRITICAL" if i > (device_max_current * 1.35) else "HIGH"
            base_score = max(base_score, 0.92)

        # Check Voltage Sag / Swell
        v_nominal = ML_SETTINGS["voltage_nominal"]
        v_low = v_nominal * (1 - ML_SETTINGS["voltage_tolerance_pct"] / 100.0) # < 207V
        v_high = v_nominal * (1 + ML_SETTINGS["voltage_tolerance_pct"] / 100.0) # > 253V
        if v < v_low:
            detected_types.append("VOLTAGE_SAG")
            highest_severity = "HIGH" if v < 195.0 else "MEDIUM"
            base_score = max(base_score, 0.88)
        elif v > v_high:
            detected_types.append("VOLTAGE_SWELL")
            highest_severity = "HIGH" if v > 260.0 else "MEDIUM"
            base_score = max(base_score, 0.85)

        # Check Power Factor Drop (Severe Reactive Penalty)
        if pf < ML_SETTINGS["min_power_factor"]:
            detected_types.append("LOW_POWER_FACTOR")
            severity = "HIGH" if pf < 0.75 else "MEDIUM"
            if highest_severity not in ["CRITICAL", "HIGH"]:
                highest_severity = severity
            base_score = max(base_score, 0.82)

        # Check 3-Phase Imbalance (Motor damage risk)
        if imbalance_pct > 15.0:
            detected_types.append("PHASE_CURRENT_IMBALANCE")
            highest_severity = "CRITICAL" if imbalance_pct > 30.0 else "HIGH"
            base_score = max(base_score, 0.89)

        # Check Overheating
        if temp > ML_SETTINGS["max_temperature_c"]:
            detected_types.append("THERMAL_OVERHEAT")
            highest_severity = "CRITICAL" if temp > 85.0 else "HIGH"
            base_score = max(base_score, 0.94)

        # Check Grid Frequency Deviation
        if abs(hz - ML_SETTINGS["frequency_nominal"]) > ML_SETTINGS["frequency_tolerance_hz"]:
            detected_types.append("GRID_FREQUENCY_UNSTABLE")
            if highest_severity not in ["CRITICAL", "HIGH"]:
                highest_severity = "MEDIUM"
            base_score = max(base_score, 0.78)

        # 2. Machine Learning Isolation Forest Prediction
        ml_is_anomaly = False
        ml_score = 0.0
        if self.is_trained:
            try:
                feature_vector = np.array([[
                    kw,
                    i,
                    v,
                    pf,
                    temp,
                    imbalance_pct
                ]])
                prediction = self.model.predict(feature_vector)[0] # -1 = anomaly, 1 = normal
                decision = self.model.decision_function(feature_vector)[0]
                
                # Convert decision function to normalized 0.0 - 1.0 anomaly score
                # Lower decision score = more anomalous
                ml_score = float(np.clip(1.0 / (1.0 + np.exp(decision * 10.0)), 0.0, 1.0))
                
                if prediction == -1 or ml_score > 0.65:
                    ml_is_anomaly = True
                    if not detected_types:
                        detected_types.append("UNSUPERVISED_PATTERN_ANOMALY")
                        highest_severity = "MEDIUM" if ml_score < 0.85 else "HIGH"
            except Exception as e:
                logger.warning(f"ML inference warning: {e}")

        # Final Decision Synthesis
        is_anomaly = (len(detected_types) > 0) or ml_is_anomaly
        final_score = max(base_score, ml_score) if is_anomaly else min(0.15, ml_score)
        
        if is_anomaly:
            primary_type = detected_types[0] if detected_types else "ANOMALOUS_CONSUMPTION"
            description = self._generate_description(
                primary_type, v, i, kw, pf, hz, temp, imbalance_pct, device_max_current
            )
            return True, round(final_score, 3), primary_type, highest_severity, description

        return False, round(final_score, 3), None, None, None

    def _generate_description(
        self,
        anomaly_type: str,
        v: float,
        i: float,
        kw: float,
        pf: float,
        hz: float,
        temp: float,
        imbalance: float,
        max_i: float
    ) -> str:
        """Generate human-readable root-cause diagnostic message."""
        descriptions = {
            "OVERCURRENT_SURGE": f"Measured current ({i:.1f}A) exceeded rated safety limit ({max_i:.1f}A) by {((i/max_i)-1)*100:.1f}%. Possible motor locked rotor or load spike.",
            "VOLTAGE_SAG": f"Grid voltage dropped to {v:.1f}V (nominal 230V). Risk of control system brownout or increased motor heating.",
            "VOLTAGE_SWELL": f"Grid voltage spiked to {v:.1f}V (limit 253V). Risk of dielectric stress and electronic insulation breakdown.",
            "LOW_POWER_FACTOR": f"Power factor degraded to {pf:.2f} (standard >= 0.85). Incurring heavy utility kVAR penalty and wasted distribution capacity.",
            "PHASE_CURRENT_IMBALANCE": f"3-Phase current imbalance reached {imbalance:.1f}% (NEMA limit < 10%). Risk of severe motor torque pulsation and stator overheating.",
            "THERMAL_OVERHEAT": f"Operating temperature reached {temp:.1f}°C (safe threshold 75°C). Critical ventilation or cooling failure suspected.",
            "GRID_FREQUENCY_UNSTABLE": f"Supply frequency drifted to {hz:.2f} Hz (nominal 50.0 Hz). Grid instability detected.",
            "UNSUPERVISED_PATTERN_ANOMALY": f"Multivariate consumption pattern deviated significantly from baseline operational model (Active Power: {kw:.1f} kW, PF: {pf:.2f})."
        }
        return descriptions.get(anomaly_type, f"Abnormal operational state detected: {anomaly_type}")

# Singleton Instance
ml_detector = EnergyAnomalyDetector()
