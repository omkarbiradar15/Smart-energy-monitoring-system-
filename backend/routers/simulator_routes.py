from fastapi import APIRouter, HTTPException, status
from backend.schemas import FaultInjectionRequest
from backend.iot_simulator import iot_simulator

router = APIRouter(prefix="/api/simulator", tags=["IoT Hardware Simulation & Fault Injection"])

@router.post("/inject-fault")
def inject_fault(payload: FaultInjectionRequest):
    valid_faults = [
        "normal",
        "overcurrent",
        "voltage_sag",
        "low_power_factor",
        "phase_loss",
        "high_temp",
        "vampire_load"
    ]
    if payload.fault_type not in valid_faults:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid fault type '{payload.fault_type}'. Valid options: {valid_faults}"
        )

    res = iot_simulator.inject_fault(
        device_id=payload.device_id,
        fault_type=payload.fault_type,
        duration_seconds=payload.duration_seconds or 30,
        intensity=payload.intensity or 1.0
    )
    return res

@router.get("/status")
def get_simulator_status():
    return {
        "running": iot_simulator.running,
        "interval_seconds": iot_simulator.interval,
        "active_faults": iot_simulator.fault_states,
        "online_devices": list(iot_simulator.latest_telemetry.keys())
    }

@router.post("/reset")
def reset_all_faults():
    iot_simulator.fault_states.clear()
    return {"status": "success", "message": "All device faults reset to normal nominal operation."}
