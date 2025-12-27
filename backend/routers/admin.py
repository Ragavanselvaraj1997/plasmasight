from fastapi import APIRouter, Depends
from ..auth import RoleChecker
from ..models_mongo import MongoModels

router = APIRouter(prefix="/api/v1", tags=["admin"])

@router.get("/debug/last-payload")
async def last_payload(user: dict = Depends(RoleChecker(["admin"]))):
    payload = await MongoModels.get_last_raw_payload()
    if payload:
        # Remove MongoDB _id for JSON serialization
        payload["_id"] = str(payload["_id"])
    return payload or {"status": "not_found"}

@router.get("/logs/errors")
async def get_error_logs(user: dict = Depends(RoleChecker(["admin"]))):
    # In a real app, fetch from ELK or structured logs
    return [{"timestamp": "2025-01-01T00:00:00Z", "error": "Kafka connection lost"}]

@router.post("/restart/module")
async def restart_module(module: dict, user: dict = Depends(RoleChecker(["admin"]))):
    return {"status": "restarting", "module": module.get("module_name")}

@router.get("/modules/status")
async def modules_status(user: dict = Depends(RoleChecker(["admin"]))):
    # In a real app, query orchestration (K8s/Docker)
    return {"inference_module": "RUNNING", "processor_module": "RUNNING"}
