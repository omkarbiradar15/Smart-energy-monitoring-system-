from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database import get_db
from backend.models import AnomalyLog, Device
from backend.schemas import AnomalyResponse, AnomalyResolveRequest

router = APIRouter(prefix="/api/anomalies", tags=["Machine Learning Anomalies"])

@router.get("", response_model=List[AnomalyResponse])
def get_anomalies(
    device_id: Optional[str] = None,
    severity: Optional[str] = None,
    resolved: Optional[bool] = None,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    query = db.query(AnomalyLog)
    if device_id:
        query = query.filter(AnomalyLog.device_id == device_id)
    if severity:
        query = query.filter(AnomalyLog.severity == severity.upper())
    if resolved is not None:
        query = query.filter(AnomalyLog.resolved == resolved)

    return query.order_by(desc(AnomalyLog.timestamp)).limit(limit).all()

@router.get("/stats")
def get_anomaly_statistics(db: Session = Depends(get_db)):
    total = db.query(AnomalyLog).count()
    unresolved = db.query(AnomalyLog).filter(AnomalyLog.resolved == False).count()
    critical = db.query(AnomalyLog).filter(AnomalyLog.severity == "CRITICAL", AnomalyLog.resolved == False).count()
    high = db.query(AnomalyLog).filter(AnomalyLog.severity == "HIGH", AnomalyLog.resolved == False).count()
    medium = db.query(AnomalyLog).filter(AnomalyLog.severity == "MEDIUM", AnomalyLog.resolved == False).count()
    low = db.query(AnomalyLog).filter(AnomalyLog.severity == "LOW", AnomalyLog.resolved == False).count()

    # Breakdown by anomaly type
    from sqlalchemy import func
    type_counts = db.query(
        AnomalyLog.anomaly_type, func.count(AnomalyLog.id)
    ).group_by(AnomalyLog.anomaly_type).all()

    return {
        "total_anomalies": total,
        "unresolved_anomalies": unresolved,
        "severity_breakdown": {
            "critical": critical,
            "high": high,
            "medium": medium,
            "low": low
        },
        "type_distribution": {item[0]: item[1] for item in type_counts}
    }

@router.put("/{anomaly_id}/resolve", response_model=AnomalyResponse)
def resolve_anomaly(
    anomaly_id: int,
    payload: AnomalyResolveRequest,
    db: Session = Depends(get_db)
):
    alert = db.query(AnomalyLog).filter(AnomalyLog.id == anomaly_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Anomaly alert not found")

    alert.resolved = True
    alert.resolved_at = datetime.utcnow()
    alert.resolved_by = "Plant Operator"
    alert.action_taken = payload.action_taken

    db.commit()
    db.refresh(alert)
    return alert
