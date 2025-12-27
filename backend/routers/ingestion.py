from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from ..auth import get_current_user
from ..models_mongo import MongoModels
from ..database import get_db
from ..models_sql import SensorReading, ImageMetric
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session
from datetime import datetime

router = APIRouter(prefix="/api/v1", tags=["ingestion"])

class SensorData(BaseModel):
    sensor_id: str
    ts: float
    value: float

@router.post("/sensors/upload")
async def upload_sensors(data: SensorData, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    reading = SensorReading(
        sensor_id=data.sensor_id,
        timestamp=datetime.fromtimestamp(data.ts),
        value=data.value,
        quality_flag=1 # Assuming good quality
    )
    db.add(reading)
    db.commit()
    return {"status": "success", "sensor_id": data.sensor_id}

@router.post("/images/upload")
async def upload_image(image: UploadFile = File(...), user: dict = Depends(get_current_user)):
    # In a real app, save to S3/Object Storage
    path = f"uploads/{image.filename}"
    # Simulate saving
    return {"status": "success", "path": path}

class SyncBatch(BaseModel):
    sensor_batch: List[dict] # {sensor_id, ts, value}
    image_frame: dict # {path, metrics}

@router.post("/sync")
async def sync_data(batch: SyncBatch, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    # 1. Save to MongoDB (Raw data)
    frame_id = await MongoModels.insert_raw_frame(batch.sensor_batch, batch.image_frame.get("path", ""))
    
    # 2. Save Sensor Readings to SQL/Timescale
    for s in batch.sensor_batch:
        reading = SensorReading(
            sensor_id=s['sensor_id'],
            timestamp=datetime.fromtimestamp(s['ts']),
            value=s['value'],
            quality_flag=1
        )
        db.add(reading)
    
    # 3. Save Image Metrics to SQL/Timescale
    metrics = batch.image_frame.get("metrics", {})
    img_metric = ImageMetric(
        image_id=str(frame_id),
        timestamp=datetime.utcnow(),
        mean_R=metrics.get("mean_R", 0.0),
        mean_G=metrics.get("mean_G", 0.0),
        mean_B=metrics.get("mean_B", 0.0),
        edge_density=metrics.get("edge_density", 0.0)
    )
    db.add(img_metric)
    
    db.commit()
    return {"status": "success", "frame_id": frame_id}
