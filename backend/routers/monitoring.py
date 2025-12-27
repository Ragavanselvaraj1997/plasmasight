from fastapi import APIRouter, Depends
from ..auth import get_current_user
from ..database import get_db
from ..models_sql import Alert
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1", tags=["monitoring"])

@router.get("/metrics/live")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@router.get("/alerts/active")
async def get_active_alerts(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    # Fetch unresolved alerts
    active_alerts = db.query(Alert).filter(Alert.resolved == False).all()
    return active_alerts

@router.get("/system/health")
async def system_health():
    # In a real app, check DB connections, Redis, etc.
    return {"status": "UP", "version": "1.0.0", "timestamp": str(datetime.utcnow())}
