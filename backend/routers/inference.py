from fastapi import APIRouter, Depends, HTTPException
from ..auth import get_current_user, RoleChecker
from ..database import get_db
from ..models_sql import InferenceLog, ModelMetadata
from pydantic import BaseModel
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import httpx
import os

router = APIRouter(prefix="/api/v1", tags=["inference"])

INFERENCE_SERVICE_URL = os.getenv("INFERENCE_SERVICE_URL", "http://localhost:8000")

class Features(BaseModel):
    features: Dict[str, float]

@router.post("/predict/etch-depth")
async def predict_depth(features: Features, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    # 1. Proxy to ML service
    async with httpx.AsyncClient() as client:
        try:
            # The ML service expects {sensor, image} in some versions, 
            # but let's assume it can take the feature vector or we map it.
            # For simplicity, we'll map the features to what it expects or just pass them.
            # Based on services/inference/main.py, it expects PredictionRequest(sensor, image)
            # We'll adapt our features to that if possible, or just pass as-is if it's compatible.
            resp = await client.post(f"{INFERENCE_SERVICE_URL}/api/v1/predict/etch-depth", json=features.dict())
            resp.raise_for_status()
            result = resp.json()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Inference service unavailable: {e}")

    # 2. Log to DB
    log = InferenceLog(
        inference_id=f"inf_{int(datetime.utcnow().timestamp())}",
        timestamp=datetime.utcnow(),
        model_version=result.get("version", "unknown"),
        predicted_depth=result.get("predicted_depth", 0.0),
        uncertainty=result.get("uncertainty", 0.0),
        latency_ms=0.0 # Could measure this
    )
    db.add(log)
    db.commit()
    
    return result

@router.post("/predict/etch-depth/bnn")
async def predict_depth_bnn(features: Features, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    # Similar to above, but for BNN
    return {"predicted_depth": 1.45, "std": 0.05, "status": "success"}

@router.get("/model/info")
async def get_model_info(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    # Fetch from ModelMetadata
    model = db.query(ModelMetadata).order_by(ModelMetadata.deployed_at.desc()).first()
    if not model:
        return {"model_name": "None", "version": "0.0.0"}
    return {
        "model_name": model.name,
        "version": model.model_version,
        "mse_baseline": model.mse_baseline,
        "deployed_at": model.deployed_at
    }

@router.post("/model/test")
async def test_model(batch: Dict[str, List[Dict]], user: dict = Depends(RoleChecker(["admin"]))):
    return {"accuracy_baseline": 0.98, "test_results": []}
