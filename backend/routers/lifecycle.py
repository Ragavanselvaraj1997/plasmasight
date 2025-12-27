from fastapi import APIRouter, Depends, UploadFile, File
from ..auth import RoleChecker
from ..database import get_db
from ..models_sql import ModelMetadata, DeploymentHistory
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

router = APIRouter(prefix="/api/v1", tags=["lifecycle"])

@router.post("/model/upload")
async def upload_model(model: UploadFile = File(...), metadata: UploadFile = File(...), user: dict = Depends(RoleChecker(["admin"])), db: Session = Depends(get_db)):
    # 1. Save model file (simulated)
    # 2. Parse metadata and save to ModelMetadata table
    # For now, let's assume we create a record with some defaults
    ver = f"v{int(datetime.utcnow().timestamp())}"
    new_model = ModelMetadata(
        model_version=ver,
        name=model.filename,
        trained_on="Latest Batch",
        mse_baseline=0.01,
        deployed_at=None
    )
    db.add(new_model)
    db.commit()
    return {"status": "model_staged", "version": ver, "filename": model.filename}

class DeployCommand(BaseModel):
    version: str

@router.post("/model/deploy")
async def deploy_model(cmd: DeployCommand, user: dict = Depends(RoleChecker(["admin"])), db: Session = Depends(get_db)):
    # 1. Update ModelMetadata
    model = db.query(ModelMetadata).filter(ModelMetadata.model_version == cmd.version).first()
    if not model:
        return {"status": "error", "message": "Model not found"}
    
    model.deployed_at = datetime.utcnow()
    
    # 2. Add to DeploymentHistory
    history = DeploymentHistory(
        model_version=cmd.version,
        start_time=datetime.utcnow(),
        status="promoted"
    )
    db.add(history)
    db.commit()
    return {"status": "deployed", "version": cmd.version}

class RollbackCommand(BaseModel):
    rollback_to_version: str

@router.post("/model/rollback")
async def rollback_model(cmd: RollbackCommand, user: dict = Depends(RoleChecker(["admin"])), db: Session = Depends(get_db)):
    history = DeploymentHistory(
        model_version=cmd.rollback_to_version,
        start_time=datetime.utcnow(),
        status="rolled-back"
    )
    db.add(history)
    db.commit()
    return {"status": "rolled_back", "to_version": cmd.rollback_to_version}

@router.get("/model/history")
async def model_history(user: dict = Depends(RoleChecker(["admin"])), db: Session = Depends(get_db)):
    history = db.query(DeploymentHistory).order_by(DeploymentHistory.start_time.desc()).all()
    return history
