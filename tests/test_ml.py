import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import unittest
from backend.ml_engine import ml_detector

class TestMLEnergyAnomalyDetector(unittest.TestCase):

    def test_nominal_reading_not_anomaly(self):
        """Test that normal nominal 3-phase readings are flagged as healthy."""
        reading = {
            "voltage_v": 230.0,
            "voltage_l1": 230.0,
            "voltage_l2": 230.0,
            "voltage_l3": 230.0,
            "current_a": 40.0,
            "current_l1": 40.0,
            "current_l2": 40.0,
            "current_l3": 40.0,
            "active_power_kw": 27.6,
            "power_factor": 0.96,
            "frequency_hz": 50.0,
            "temperature_c": 38.0
        }
        is_anomaly, score, a_type, sev, desc = ml_detector.analyze_reading(
            reading, device_max_current=100.0, device_base_kw=50.0
        )
        self.assertFalse(is_anomaly)
        self.assertLess(score, 0.40)

    def test_overcurrent_surge_detection(self):
        """Test that excessive current triggers OVERCURRENT_SURGE anomaly."""
        reading = {
            "voltage_v": 230.0,
            "current_a": 160.0, # Max current is 100A -> 160% load
            "current_l1": 160.0,
            "current_l2": 160.0,
            "current_l3": 160.0,
            "active_power_kw": 110.0,
            "power_factor": 0.95,
            "frequency_hz": 50.0,
            "temperature_c": 55.0
        }
        is_anomaly, score, a_type, sev, desc = ml_detector.analyze_reading(
            reading, device_max_current=100.0, device_base_kw=50.0
        )
        self.assertTrue(is_anomaly)
        self.assertEqual(a_type, "OVERCURRENT_SURGE")
        self.assertIn(sev, ["HIGH", "CRITICAL"])
        self.assertGreaterEqual(score, 0.85)

    def test_voltage_sag_detection(self):
        """Test that voltage drop under 207V triggers VOLTAGE_SAG anomaly."""
        reading = {
            "voltage_v": 185.0, # > 10% below nominal 230V
            "current_a": 45.0,
            "active_power_kw": 25.0,
            "power_factor": 0.94,
            "frequency_hz": 50.0,
            "temperature_c": 40.0
        }
        is_anomaly, score, a_type, sev, desc = ml_detector.analyze_reading(
            reading, device_max_current=100.0, device_base_kw=50.0
        )
        self.assertTrue(is_anomaly)
        self.assertEqual(a_type, "VOLTAGE_SAG")

    def test_low_power_factor_detection(self):
        """Test that degraded PF < 0.85 triggers LOW_POWER_FACTOR anomaly."""
        reading = {
            "voltage_v": 230.0,
            "current_a": 65.0,
            "active_power_kw": 30.0,
            "power_factor": 0.65, # Below 0.85 limit
            "frequency_hz": 50.0,
            "temperature_c": 42.0
        }
        is_anomaly, score, a_type, sev, desc = ml_detector.analyze_reading(
            reading, device_max_current=100.0, device_base_kw=50.0
        )
        self.assertTrue(is_anomaly)
        self.assertEqual(a_type, "LOW_POWER_FACTOR")

    def test_phase_imbalance_calculation(self):
        """Test NEMA phase unbalance computation formula."""
        imbalance = ml_detector.compute_phase_imbalance(50.0, 50.0, 50.0)
        self.assertEqual(imbalance, 0.0)

        # Severe unbalance: Phase 1: 80A, Phase 2: 0A, Phase 3: 70A
        imbalance_sev = ml_detector.compute_phase_imbalance(80.0, 0.0, 70.0)
        self.assertGreater(imbalance_sev, 50.0)

if __name__ == "__main__":
    unittest.main()
