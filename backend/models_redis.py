import redis
import json
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
r = redis.from_url(REDIS_URL, decode_responses=True)

class RedisModels:
    @staticmethod
    def set_feature_cache(window_id: str, feature_vector: list):
        data = {
            "feature_vector": feature_vector,
            "timestamp": json.dumps(json.dumps(None)) # Placeholder for timestamp logic if needed
        }
        # In a real app we'd use a real timestamp
        from datetime import datetime
        data["timestamp"] = datetime.utcnow().isoformat()
        r.set(f"feature:{window_id}", json.dumps(data), ex=3600) # 1 hour expiry

    @staticmethod
    def get_feature_cache(window_id: str):
        data = r.get(f"feature:{window_id}")
        return json.loads(data) if data else None

    @staticmethod
    def update_control_state(last_prediction: float, last_actuation_command: dict):
        state = {
            "last_prediction": last_prediction,
            "last_actuation_command": last_actuation_command,
            "timestamp": datetime.utcnow().isoformat()
        }
        r.set("control_state", json.dumps(state))

    @staticmethod
    def get_control_state():
        data = r.get("control_state")
        return json.loads(data) if data else None
