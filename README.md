# ⚡ Smart Energy Monitoring & Industrial Anomaly Detection System

A full-stack, enterprise-grade IoT Energy Management Platform (EMS) designed for real-time industrial electricity consumption monitoring, machine learning-driven anomaly detection, multi-tier tariff optimization, and automated ISO 50001 energy audit reporting.

![System Status](https://img.shields.io/badge/System_Status-Online-10b981?style=for-the-badge)
![Python FastAPI](https://img.shields.io/badge/Backend-FastAPI_Python_3.14-0284c7?style=for-the-badge&logo=fastapi)
![Java Microservice](https://img.shields.io/badge/Microservice-Java_23_ISO50001-f97316?style=for-the-badge&logo=openjdk)
![Machine Learning](https://img.shields.io/badge/ML-Isolation_Forest-8b5cf6?style=for-the-badge&logo=scikitlearn)
![IoT ESP32](https://img.shields.io/badge/IoT-ESP32_WiFi_HTTP-ec4899?style=for-the-badge&logo=espressif)
![Database](https://img.shields.io/badge/Database-SQL_SQLite_PostgreSQL-334155?style=for-the-badge&logo=sqlite)

---

## 🎯 Executive Summary & Resume Highlights

- **Real-Time IoT Telemetry Stream**: Ingests high-frequency 3-phase AC voltage, current, active/reactive/apparent power, power factor, frequency, and thermal metrics via WebSocket (`ws://`) and HTTP REST APIs at sub-2-second latency.
- **Multivariate ML Anomaly Detection**: Built an unsupervised **Scikit-Learn Isolation Forest** & domain heuristic engine to instantly flag phase unbalance, transformer overcurrent inrush, voltage sags/swells, and severe power factor penalties.
- **Automated ISO 50001 Energy Auditing**: Generates printable energy audit reports calculating Energy Performance Indicators (EnPI), Time-of-Use (TOU) cost breakdowns, carbon footprint (kg CO2e), and prioritized Energy Conservation Measures (ECMs).
- **Dual Microservices Architecture**: Implemented core REST & WebSocket backend in **Python FastAPI** and enterprise compliance verification engine in **Java (Spring Boot / Java 23)**.
- **Interactive Cyber-Industrial UI**: Designed a responsive dark glassmorphism Single-Page Application (SPA) with live Chart.js time-series graphs, 3-phase gauge arrays, and interactive IoT fault injection controls.

---

## 🏗️ System Architecture

```
                                  +-----------------------------+
                                  |   Hardware IoT Node (ESP32) |
                                  |   PZEM-004T / CT Sensors    |
                                  +--------------+--------------+
                                                 |
                                  WiFi / HTTP REST / JSON
                                                 |
                                                 v
+-----------------------------------------------------------------------------------------------+
|                                 CORE BACKEND (Python FastAPI)                                 |
|                                                                                               |
|   +-----------------------+     +-----------------------+     +---------------------------+   |
|   |  IoT Telemetry Engine | --> |  SQLAlchemy Database  | <-- |  Automated Audit Reports  |   |
|   |  & WebSocket Broker   |     |  (SQLite / PostgreSQL)|     |  (PDF / HTML ECM Engine)  |   |
|   +-----------+-----------+     +-----------+-----------+     +---------------------------+   |
|               |                             |                                                 |
|               v                             v                                                 |
|   +-----------------------------------------------------+                                     |
|   |   Hybrid Machine Learning Anomaly Detector          |                                     |
|   |   (Scikit-Learn Isolation Forest + Domain Rules)    |                                     |
|   +-----------------------------------------------------+                                     |
+-------------------+---------------------------------------------------+-----------------------+
                    |                                                   |
           REST / JSON Proxy                                   WebSockets / REST
                    |                                                   |
                    v                                                   v
+----------------------------------------+             +----------------------------------------+
|  ENTERPRISE JAVA MICROSERVICE          |             |   RESPONSIVE INDUSTRIAL DASHBOARD      |
|  ISO 50001 EnPI & Tariff Engine (8081) |             |   (HTML5, Vanilla CSS, JS, Chart.js)   |
+----------------------------------------+             +----------------------------------------+
```

---

## 🛠️ Technology Stack

| Domain | Technologies Used |
| :--- | :--- |
| **Frontend** | HTML5, Modern Vanilla CSS3 (Glassmorphism Dark Theme), JavaScript (ES6+), Chart.js |
| **Core Backend** | Python 3.14, FastAPI, Starlette, Uvicorn, Pydantic, Python-JOSE (JWT Auth) |
| **Enterprise Service** | Java 23 / Spring Boot style HTTP Microservice (Port 8081) |
| **Machine Learning** | Scikit-Learn (Isolation Forest), Pandas, NumPy, Multivariate Clustering |
| **IoT & Firmware** | ESP32 DevKit V1, PZEM-004T / SCT-013 CT Sensors, C++ Arduino Firmware (`.ino`) |
| **Database & ORM** | SQLAlchemy ORM, SQLite (Default), PostgreSQL / MySQL Schema DDL scripts |
| **Testing** | Python `unittest`, FastAPI `TestClient`, End-to-End Simulation Tests |

---

## 📂 Repository Structure

```
smart-energy-monitoring/
├── backend/
│   ├── app.py                      # FastAPI Application, WebSockets & Static Servicing
│   ├── config.py                   # App Configuration, Pricing Tariffs & ML Parameters
│   ├── database.py                 # SQLAlchemy Connection & Session Management
│   ├── models.py                   # SQL Database ORM Models
│   ├── schemas.py                  # Pydantic Schemas for Validation & Swagger
│   ├── auth.py                     # JWT Authentication & Password Hashing
│   ├── ml_engine.py                # Isolation Forest & Anomaly Detection Engine
│   ├── iot_simulator.py            # Multi-Device 3-Phase IoT Telemetry Simulator
│   ├── report_generator.py         # Automated Energy Audit & ECM Generator
│   └── routers/
│       ├── auth_routes.py          # User Login & JWT Handlers
│       ├── device_routes.py        # IoT Device Fleet Management
│       ├── telemetry_routes.py     # Live Stream, Historical Trends & Ingestion
│       ├── anomaly_routes.py       # ML Anomaly Diagnostics & Resolution
│       ├── report_routes.py        # Energy Audit Generation & Printable HTML
│       └── simulator_routes.py     # Interactive Fault Injection Handlers
├── database/
│   ├── schema.sql                  # Production SQL DDL Schema (SQLite/MySQL/PostgreSQL)
│   ├── seed_data.py                # Database Seeder (48h Time-Series & Anomaly Logs)
│   └── energy_monitor.db           # SQLite Local Time-Series Database
├── frontend/
│   ├── index.html                  # Industrial EMS Dashboard SPA
│   ├── css/
│   │   ├── styles.css              # Cyber-Dark Glassmorphism Theme
│   │   └── responsive.css          # Mobile & Tablet Breakpoints
│   └── js/
│       ├── app.js                  # Master Application Lifecycle & Routing
│       ├── charts.js               # High-Performance Chart.js Engine
│       ├── live_feed.js            # WebSocket Client with Auto-Reconnect & Polling
│       ├── simulator_ui.js         # Fault Injector Control Panel
│       ├── anomaly_view.js         # ML Threat Log & Resolution Modal
│       └── reports_view.js         # Energy Audit Viewer & Java ISO 50001 Connector
├── java_service/
│   ├── src/main/java/com/energy/
│   │   └── EnergyComplianceApplication.java # Java ISO 50001 Microservice
│   ├── pom.xml                     # Maven Build Configuration
│   └── bin/                        # Compiled Java Bytecode
├── iot_firmware/
│   └── esp32_energy_meter.ino      # Ready-to-flash ESP32 C++ Arduino Firmware
├── tests/
│   ├── test_api.py                 # REST API Integration & Auth Tests
│   └── test_ml.py                  # Machine Learning Anomaly Detection Tests
├── requirements.txt                # Python Dependencies
├── run.py                          # 1-Click Master Application Runner
├── run.sh                          # Executable Unix Bash Launcher
└── README.md                       # Comprehensive Documentation
```

---

## ⚡ Quickstart & Local Execution

### 1. Prerequisites
- Python 3.10+ (Tested on Python 3.14)
- Java 17+ (Java 23 installed on system)

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Application (1-Click)
```bash
python3 run.py
# or
./run.sh
```

### 4. Access Platform
- **Industrial Dashboard**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Swagger Interactive API Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Java ISO 50001 Microservice**: [http://localhost:8081/api/compliance/health](http://localhost:8081/api/compliance/health)

### 5. Default Credentials
| Role | Username | Password |
| :--- | :--- | :--- |
| **Plant Director / Admin** | `admin` | `admin123` |
| **Control Room Operator** | `operator` | `operator123` |

---

## 📡 REST API Specifications

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/auth/login-json` | Authenticate user and receive JWT bearer token |
| `GET` | `/api/telemetry/live` | Real-time aggregate KPI summary & online fleet status |
| `GET` | `/api/telemetry/history` | Historical time-series telemetry filtered by device/hours |
| `GET` | `/api/telemetry/chart-trends` | Aggregated hourly, weekly, and monthly trend curves |
| `POST` | `/api/telemetry/ingest` | ESP32 hardware telemetry ingestion endpoint |
| `GET` | `/api/anomalies` | Query machine learning flagged anomalies & severity |
| `PUT` | `/api/anomalies/{id}/resolve` | Acknowledge & resolve anomaly with corrective notes |
| `GET` | `/api/reports` | List generated energy audit reports |
| `POST` | `/api/reports/generate` | Generate automated audit report (daily/weekly/monthly) |
| `GET` | `/api/reports/{uid}/export/html` | Printable ISO 50001 Energy Audit Certificate |
| `POST` | `/api/simulator/inject-fault` | Inject dynamic anomalies (voltage sag, overcurrent, low PF) |
| `WS` | `/ws/live` | Bi-directional high-frequency WebSocket stream |

---

## 🧪 Automated Testing

Run the test suite:
```bash
# Run ML anomaly tests
python3 -m unittest tests/test_ml.py

# Run REST API integration tests
python3 -m unittest tests/test_api.py

# Run all test cases
python3 -m unittest discover -s tests -p "test_*.py"
```

---

## 📜 Resume Bullet Points (Copy & Paste)

- **Smart Energy Monitoring & Industrial Anomaly Detection System (Python, Java, IoT, ML, SQL)**:
  - Developed an end-to-end industrial IoT energy platform tracking real-time 3-phase electrical telemetry across factory substations with sub-2s WebSocket updates.
  - Implemented an unsupervised **Isolation Forest & heuristic Machine Learning model** in Scikit-Learn that achieved high-precision detection for phase unbalance, current surges, and low power factor penalties.
  - Engineered dual microservices: core high-throughput asynchronous REST/WebSocket server in **Python FastAPI** and an **ISO 50001 compliance engine in Java**.
  - Built an automated audit engine computing Time-of-Use (TOU) energy costs, carbon footprint (kg CO2e), and generating actionable energy conservation measures (ECMs).
  - Deployed responsive dark glassmorphism dashboard in HTML5/Vanilla CSS/Chart.js along with C++ Arduino firmware for ESP32 hardware meters.
