from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Device
from backend.schemas import DeviceCreate, DeviceUpdate, DeviceResponse

router = APIRouter(prefix="/api/devices", tags=["Device Management"])

@router.get("", response_model=List[DeviceResponse])
def list_devices(db: Session = Depends(get_db)):
    return db.query(Device).all()

@router.get("/{device_id}", response_model=DeviceResponse)
def get_device(device_id: str, db: Session = Depends(get_db)):
    dev = db.query(Device).filter(Device.device_id == device_id).first()
    if not dev:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    return dev

@router.post("", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
def create_device(payload: DeviceCreate, db: Session = Depends(get_db)):
    existing = db.query(Device).filter(Device.device_id == payload.device_id).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Device {payload.device_id} already exists")
    
    dev = Device(
        device_id=payload.device_id,
        name=payload.name,
        location=payload.location,
        line_type=payload.line_type,
        max_current=payload.max_current,
        base_kw=payload.base_kw,
        ip_address=payload.ip_address,
        firmware_version=payload.firmware_version
    )
    db.add(dev)
    db.commit()
    db.refresh(dev)
    return dev

@router.put("/{device_id}", response_model=DeviceResponse)
def update_device(device_id: str, payload: DeviceUpdate, db: Session = Depends(get_db)):
    dev = db.query(Device).filter(Device.device_id == device_id).first()
    if not dev:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(dev, key, value)
    
    db.commit()
    db.refresh(dev)
    return dev

@router.delete("/{device_id}")
def delete_device(device_id: str, db: Session = Depends(get_db)):
    dev = db.query(Device).filter(Device.device_id == device_id).first()
    if not dev:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    
    db.delete(dev)
    db.commit()
    return {"status": "success", "message": f"Device {device_id} removed"}
