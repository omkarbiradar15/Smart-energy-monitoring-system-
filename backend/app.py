import os
import json
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import List
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.config import BASE_DIR, DEFAULT_TARIFF
from backend.database import init_db, SessionLocal
from backend.models import User, TariffConfig
from backend.auth import hash_password
from backend.iot_simulator import iot_simulator

# Import Routers
from backend.routers.auth_routes import router as auth_router
from backend.routers.device_routes import router as device_router
from backend.routers.telemetry_routes import router as telemetry_router
from backend.routers.anomaly_routes import router as anomaly_router
from backend.routers.report_routes import router as report_router
from backend.routers.simulator_routes import router as simulator_router

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("energy_monitor")

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total active: {len(self.active_connections)}")

    async def broadcast_json(self, data: dict):
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception:
                dead_connections.append(connection)
        for dead in dead_connections:
            if dead in self.active_connections:
                self.active_connections.remove(dead)

manager = ConnectionManager()

def seed_initial_data():
    """Seed initial administrator and tariff configuration."""
    db = SessionLocal()
    try:
        # Admin User
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                email="admin@smartenergy.io",
                hashed_password=hash_password("admin123"),
                full_name="Plant Energy Director",
                role="Admin"
            )
            db.add(admin)

        # Demo Operator
        operator = db.query(User).filter(User.username == "operator").first()
        if not operator:
            operator = User(
                username="operator",
                email="operator@smartenergy.io",
                hashed_password=hash_password("operator123"),
                full_name="Control Room Operator",
                role="Plant Operator"
            )
            db.add(operator)

        # Default Tariff
        tariff = db.query(TariffConfig).first()
        if not tariff:
            tariff = TariffConfig(
                tariff_name="Industrial TOU Tariff (High Tension)",
                peak_rate=DEFAULT_TARIFF["peak_rate_per_kwh"],
                off_peak_rate=DEFAULT_TARIFF["off_peak_rate_per_kwh"],
                demand_charge=DEFAULT_TARIFF["demand_charge_per_kw"],
                co2_factor=DEFAULT_TARIFF["co2_kg_per_kwh"],
                currency="USD",
                currency_symbol="$",
                is_active=True
            )
            db.add(tariff)

        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Initial seeding error: {e}")
    finally:
        db.close()

# Bridge IoT Simulator callbacks to asyncio WebSocket Broadcast
loop_ref = None

def on_telemetry_tick(readings):
    if loop_ref and manager.active_connections:
        asyncio.run_coroutine_threadsafe(
            manager.broadcast_json({"type": "TELEMETRY_UPDATE", "data": readings}),
            loop_ref
        )

@asynccontextmanager
async def lifespan(app: FastAPI):
    global loop_ref
    loop_ref = asyncio.get_running_loop()
    
    # Initialize DB & Seed Baseline Data
    init_db()
    seed_initial_data()
    
    # Start IoT Multi-Device Simulation Loop
    iot_simulator.add_subscriber(on_telemetry_tick)
    iot_simulator.start()
    
    logger.info("Smart Energy Monitoring System Backend Ready!")
    yield
    
    # Shutdown
    iot_simulator.stop()
    logger.info("Shutting down Smart Energy Monitoring System.")

app = FastAPI(
    title="Smart Energy Monitoring & Anomaly Detection System",
    description="IoT-driven Industrial Electricity Consumption Platform with Machine Learning & Automated Energy Audits",
    version="2.5.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(auth_router)
app.include_router(device_router)
app.include_router(telemetry_router)
app.include_router(anomaly_router)
app.include_router(report_router)
app.include_router(simulator_router)

# WebSocket Endpoint
@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send initial snapshot immediately
        snapshot = list(iot_simulator.latest_telemetry.values())
        if snapshot:
            await websocket.send_json({"type": "INIT_SNAPSHOT", "data": snapshot})
            
        while True:
            # Keepalive listener
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.debug(f"WebSocket closed: {e}")
        manager.disconnect(websocket)

# Mount Frontend Static Assets
frontend_dir = BASE_DIR / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

@app.api_route("/", methods=["GET", "HEAD"])
def serve_index():
    index_path = BASE_DIR / "frontend" / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "Smart Energy Monitoring API Online. Visit /docs for Swagger API documentation."}
