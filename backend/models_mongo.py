from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGO_URL)
db = client.plasma_etch

class MongoModels:
    @staticmethod
    async def insert_raw_frame(sensor_batch: list, image_path: str):
        frame = {
            "timestamp": datetime.utcnow(),
            "sensor_batch": sensor_batch,
            "image_path": image_path
        }
        result = await db.raw_frames.insert_one(frame)
        return str(result.inserted_id)

    @staticmethod
    async def insert_archived_features(features: dict, ground_truth_depth: float = None):
        archive = {
            "timestamp": datetime.utcnow(),
            "features": features,
            "ground_truth_depth": ground_truth_depth
        }
        result = await db.archived_features.insert_one(archive)
        return str(result.inserted_id)

    @staticmethod
    async def get_last_raw_payload():
        return await db.raw_frames.find_one(sort=[("timestamp", -1)])
