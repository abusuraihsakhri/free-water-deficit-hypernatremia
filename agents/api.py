"""Optional FastAPI server: validated clinical calculator and legacy audit endpoints."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from .base import AuditLogger
from .models import SystemTaskPayload
from .supervisor import SystemSupervisor
from water_deficit import calculate_metrics

supervisor = SystemSupervisor(model_provider="mock")
app = FastAPI(
    title="Free Water Deficit Hypernatremia API",
    description="Adult hypernatremia calculation; legacy audit demonstration retained.",
    version="3.1.0",
)


class ChatRequest(BaseModel):
    query: str


class WaterDeficitRequest(BaseModel):
    weight_kg: float = Field(ge=1, le=500, allow_inf_nan=False)
    serum_sodium: float = Field(gt=145, le=250, allow_inf_nan=False)
    tbw_fraction: float = Field(ge=0.3, le=0.8, allow_inf_nan=False)
    target_sodium: float = Field(default=140, ge=120, le=200, allow_inf_nan=False)
    fluid_sodium: float = Field(default=0, ge=0, le=600, allow_inf_nan=False)
    fluid_potassium: float = Field(default=0, ge=0, le=200, allow_inf_nan=False)


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "free-water-deficit-hypernatremia",
            "version": "3.1.0"}


@app.post("/api/water-deficit")
def api_water_deficit(payload: WaterDeficitRequest):
    try:
        return calculate_metrics(**payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/metrics")
def metrics():
    return {"dossiers_processed_total": len(supervisor.dossier_registry),
            "audit_blocks_total": len(AuditLogger.get_trail()),
            "system_status": "NOMINAL_OPTIMAL"}


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    return supervisor.process_task(payload).to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        return {"response": supervisor.query_supervisory_chat(req.query)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(),
            "verified": AuditLogger.verify_integrity()}
