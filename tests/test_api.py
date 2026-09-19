import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import unittest
from fastapi.testclient import TestClient
from backend.app import app
from backend.database import init_db

class TestEnergyMonitoringAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)

    def test_root_and_static_access(self):
        """Test root endpoint returns dashboard index."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)

    def test_auth_login_json(self):
        """Test JSON authentication login."""
        res = self.client.post("/api/auth/login-json", json={
            "username": "admin",
            "password": "admin123"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["user"]["role"], "Admin")

    def test_list_devices(self):
        """Test listing IoT sensor devices."""
        res = self.client.get("/api/devices")
        self.assertEqual(res.status_code, 200)
        devices = res.json()
        self.assertIsInstance(devices, list)
        self.assertGreaterEqual(len(devices), 1)

    def test_telemetry_live_summary(self):
        """Test live telemetry summary KPI endpoint."""
        res = self.client.get("/api/telemetry/live")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("total_active_power_kw", data)
        self.assertIn("avg_power_factor", data)
        self.assertIn("system_status", data)

    def test_telemetry_chart_trends(self):
        """Test historical trends aggregation endpoint."""
        res = self.client.get("/api/telemetry/chart-trends?period=today")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["period"], "today")
        self.assertEqual(len(data["trends"]), 24)

    def test_hardware_iot_ingest(self):
        """Test ESP32 HTTP REST telemetry ingestion."""
        payload = {
            "device_id": "ESP32-TEST-01",
            "voltage_v": 231.2,
            "current_a": 42.0,
            "active_power_kw": 28.5,
            "power_factor": 0.95,
            "frequency_hz": 50.0,
            "temperature_c": 39.0
        }
        res = self.client.post("/api/telemetry/ingest", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["status"], "success")

    def test_generate_audit_report(self):
        """Test automated energy audit generation and HTML export."""
        res = self.client.post("/api/reports/generate", json={"period": "daily"})
        self.assertEqual(res.status_code, 201)
        report = res.json()
        self.assertIn("report_uid", report)
        self.assertIn("efficiency_grade", report)
        self.assertGreater(report["total_energy_kwh"], 0)

        # Test HTML Export
        html_res = self.client.get(f"/api/reports/{report['report_uid']}/export/html")
        self.assertEqual(html_res.status_code, 200)
        self.assertIn("Smart Industrial Energy Audit", html_res.text)

    def test_simulator_fault_injection(self):
        """Test IoT fault injection API."""
        res = self.client.post("/api/simulator/inject-fault", json={
            "device_id": "ESP32-TX01",
            "fault_type": "voltage_sag",
            "duration_seconds": 15
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")

if __name__ == "__main__":
    unittest.main()
