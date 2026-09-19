from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database import get_db
from backend.models import AuditReport
from backend.schemas import ReportGenerateRequest, ReportResponse
from backend.report_generator import report_engine

router = APIRouter(prefix="/api/reports", tags=["Automated Energy Audit Reports"])

@router.get("", response_model=List[ReportResponse])
def list_reports(limit: int = Query(default=20, ge=1, le=100), db: Session = Depends(get_db)):
    return db.query(AuditReport).order_by(desc(AuditReport.created_at)).limit(limit).all()

@router.get("/{report_uid}", response_model=ReportResponse)
def get_report(report_uid: str, db: Session = Depends(get_db)):
    report = db.query(AuditReport).filter(AuditReport.report_uid == report_uid).first()
    if not report:
        raise HTTPException(status_code=404, detail="Audit report not found")
    return report

@router.post("/generate", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def generate_new_report(payload: ReportGenerateRequest, db: Session = Depends(get_db)):
    report = report_engine.generate_report(
        db=db,
        period_type=payload.period,
        device_id=payload.device_id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        generated_by="Automated Industrial EMS Engine"
    )
    return report

@router.get("/{report_uid}/export/html", response_class=HTMLResponse)
def export_report_html(report_uid: str, db: Session = Depends(get_db)):
    """Generate sleek, printable standalone HTML Energy Audit Certificate."""
    report = db.query(AuditReport).filter(AuditReport.report_uid == report_uid).first()
    if not report:
        raise HTTPException(status_code=404, detail="Audit report not found")

    import json
    summary = json.loads(report.summary_json or "{}")
    devices = json.loads(report.breakdown_by_device_json or "[]")
    recs = json.loads(report.recommendations_json or "[]")

    # Generate rich printable HTML
    devices_rows = "".join([
        f"""<tr>
            <td style="padding:10px; border-bottom:1px solid #e2e8f0; font-weight:600;">{d.get('name')} ({d.get('device_id')})</td>
            <td style="padding:10px; border-bottom:1px solid #e2e8f0;">{d.get('location')}</td>
            <td style="padding:10px; border-bottom:1px solid #e2e8f0; text-align:right;">{d.get('energy_kwh'):,.1f} kWh</td>
            <td style="padding:10px; border-bottom:1px solid #e2e8f0; text-align:right;">{d.get('share_pct')}%</td>
            <td style="padding:10px; border-bottom:1px solid #e2e8f0; text-align:right; font-weight:600;">${d.get('cost'):,.2f}</td>
        </tr>""" for d in devices
    ])

    recs_cards = "".join([
        f"""<div style="background:#f8fafc; border-left:4px solid {'#ef4444' if r.get('priority')=='CRITICAL' else '#3b82f6'}; padding:16px; margin-bottom:12px; border-radius:4px;">
            <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                <span style="font-weight:700; color:#0f172a;">{r.get('title')}</span>
                <span style="font-size:12px; font-weight:700; background:#e2e8f0; padding:2px 8px; border-radius:12px;">{r.get('category')} | {r.get('priority')}</span>
            </div>
            <p style="margin:4px 0 8px 0; font-size:13px; color:#475569;">{r.get('description')}</p>
            <div style="font-size:12px; color:#16a34a; font-weight:600;">
                Est. Annual Savings: ${r.get('annual_saving_usd',0):,.2f} / yr ({r.get('kwh_saved_annual',0):,.1f} kWh) • Simple Payback: {r.get('estimated_roi_months')} months
            </div>
        </div>""" for r in recs
    ])

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{report.title} - {report.report_uid}</title>
    <style>
        body {{ font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif; background: #fff; color: #1e293b; margin: 0; padding: 40px; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #0284c7; padding-bottom: 20px; }}
        .badge-grade {{ background: #0284c7; color: #fff; font-size: 28px; font-weight: 800; padding: 10px 24px; border-radius: 8px; display: inline-block; }}
        .grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin: 24px 0; }}
        .kpi {{ background: #f1f5f9; padding: 16px; border-radius: 8px; border: 1px solid #e2e8f0; }}
        .kpi-val {{ font-size: 24px; font-weight: 800; color: #0f172a; margin-top: 4px; }}
        .kpi-label {{ font-size: 12px; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
        th {{ background: #0f172a; color: #fff; text-align: left; padding: 10px; font-size: 13px; }}
        @media print {{ body {{ padding: 0; }} button {{ display: none; }} }}
    </style>
</head>
<body>
    <div style="text-align:right; margin-bottom: 15px;">
        <button onclick="window.print()" style="padding:10px 20px; background:#0284c7; color:#fff; border:none; border-radius:6px; font-weight:600; cursor:pointer;">Print / Save as PDF</button>
    </div>
    <div class="header">
        <div>
            <h1 style="margin:0; font-size:26px; color:#0f172a;">Smart Industrial Energy Audit</h1>
            <div style="color:#64748b; font-size:14px; margin-top:4px;">UID: {report.report_uid} | ISO 50001 Verified Telemetry</div>
            <div style="font-size:13px; color:#0284c7; margin-top:2px;">Audit Period: {report.period_start.strftime('%Y-%m-%d %H:%M')} UTC to {report.period_end.strftime('%Y-%m-%d %H:%M')} UTC</div>
        </div>
        <div style="text-align:right;">
            <div class="badge-grade">Grade {report.efficiency_grade}</div>
            <div style="font-size:11px; color:#64748b; margin-top:4px;">Efficiency Rating</div>
        </div>
    </div>

    <div class="grid">
        <div class="kpi">
            <div class="kpi-label">Total Consumption</div>
            <div class="kpi-val">{report.total_energy_kwh:,.1f} <span style="font-size:14px; color:#64748b;">kWh</span></div>
        </div>
        <div class="kpi">
            <div class="kpi-label">Peak Demand</div>
            <div class="kpi-val">{report.peak_demand_kw:,.1f} <span style="font-size:14px; color:#64748b;">kW</span></div>
        </div>
        <div class="kpi">
            <div class="kpi-label">Total Energy Cost</div>
            <div class="kpi-val">${report.total_cost:,.2f}</div>
        </div>
        <div class="kpi">
            <div class="kpi-label">Carbon Footprint</div>
            <div class="kpi-val">{report.carbon_emissions_kg:,.1f} <span style="font-size:14px; color:#64748b;">kg CO2e</span></div>
        </div>
    </div>

    <h2 style="font-size:18px; color:#0f172a; border-bottom:1px solid #e2e8f0; padding-bottom:8px; margin-top:30px;">Substation & Machine Energy Distribution</h2>
    <table>
        <thead>
            <tr>
                <th>Equipment / Line</th>
                <th>Location</th>
                <th style="text-align:right;">Energy (kWh)</th>
                <th style="text-align:right;">Load Share</th>
                <th style="text-align:right;">Total Cost</th>
            </tr>
        </thead>
        <tbody>
            {devices_rows}
        </tbody>
    </table>

    <h2 style="font-size:18px; color:#0f172a; border-bottom:1px solid #e2e8f0; padding-bottom:8px; margin-top:30px;">Actionable Energy Conservation Measures (ECMs)</h2>
    {recs_cards}

    <div style="margin-top:40px; padding-top:20px; border-top:1px solid #e2e8f0; display:flex; justify-content:space-between; font-size:12px; color:#94a3b8;">
        <div>Generated automatically by Smart Energy Monitoring System (FastAPI + ML Engine + ESP32 IoT).</div>
        <div>Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</div>
    </div>
</body>
</html>"""

    return HTMLResponse(content=html_content)
