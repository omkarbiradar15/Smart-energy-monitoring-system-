#!/usr/bin/env python3
"""
Smart Energy Monitoring System - Master Unified Application Runner
Initializes SQLite database, starts Java Compliance Microservice,
and launches the FastAPI & WebSockets Live Industrial EMS Dashboard.
"""

import os
import sys
import subprocess
import time
import uvicorn
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from database.seed_data import seed_database

def start_java_service():
    """Attempt to compile and start Java ISO 50001 Microservice in background."""
    java_src = BASE_DIR / "java_service" / "src" / "main" / "java" / "com" / "energy" / "EnergyComplianceApplication.java"
    bin_dir = BASE_DIR / "java_service" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Compile
        compile_cmd = ["javac", "-d", str(bin_dir), str(java_src)]
        subprocess.run(compile_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Run in background
        run_cmd = ["java", "-cp", str(bin_dir), "com.energy.EnergyComplianceApplication"]
        java_proc = subprocess.Popen(run_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("☕ Java ISO 50001 Compliance Microservice running on http://localhost:8081")
        return java_proc
    except Exception as e:
        print(f"⚠️  Note: Java service not started ({e}). Core Python backend will handle all functions.")
        return None

def main():
    print("=========================================================================")
    print("⚡  SMART INDUSTRIAL ENERGY MONITORING & ANOMALY DETECTION SYSTEM v2.5.0")
    print("=========================================================================")
    
    # 1. Initialize & Seed Database
    seed_database()

    # 2. Start Java Microservice
    java_proc = start_java_service()

    print("\n🚀 Starting FastAPI Industrial Web Server & WebSocket Telemetry Stream...")
    print("-------------------------------------------------------------------------")
    print("📊 Dashboard UI:         http://127.0.0.1:8000/")
    print("📑 Swagger REST Docs:    http://127.0.0.1:8000/docs")
    print("⚡ Live WebSocket:       ws://127.0.0.1:8000/ws/live")
    print("🔑 Default Admin User:   username: 'admin' | password: 'admin123'")
    print("🔑 Demo Operator User:   username: 'operator' | password: 'operator123'")
    print("-------------------------------------------------------------------------\n")

    try:
        uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=False, log_level="info")
    finally:
        if java_proc:
            java_proc.terminate()

if __name__ == "__main__":
    main()
