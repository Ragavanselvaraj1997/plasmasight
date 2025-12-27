from fastapi import FastAPI, Depends, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from .database import init_db, SessionLocal
from .models_sql import User, Role
from .auth import get_password_hash
import json
import asyncio
from kafka import KafkaConsumer

from .routers import ingestion, inference, control, monitoring, lifecycle, admin, auth

app = FastAPI(title="Plasma Etch Control System API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(ingestion.router)
app.include_router(inference.router)
app.include_router(control.router)
app.include_router(monitoring.router)
app.include_router(lifecycle.router)
app.include_router(admin.router)
app.include_router(auth.router)

def seed_db():
    db = SessionLocal()
    try:
        # Check for roles
        if not db.query(Role).first():
            admin_role = Role(name="admin")
            engineer_role = Role(name="engineer")
            internal_role = Role(name="internal")
            viewer_role = Role(name="viewer")
            db.add_all([admin_role, engineer_role, internal_role, viewer_role])
            db.commit()
            
        # Check for admin user
        if not db.query(User).filter(User.username == "admin").first():
            admin_role = db.query(Role).filter(Role.name == "admin").first()
            admin_user = User(
                username="admin",
                hashed_password=get_password_hash("password"),
                role_id=admin_role.role_id
            )
            db.add(admin_user)
            db.commit()
    finally:
        db.close()

@app.on_event("startup")
def on_startup():
    try:
        init_db()
        seed_db()
    except Exception as e:
        print(f"DB Init/Seed Error: {e}")

@app.get("/")
def read_root():
    return {"status": "System Operational", "api_version": "v1"}

@app.websocket("/ws/metrics")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await asyncio.sleep(0.5)
            await websocket.send_json({
               "timestamp": asyncio.get_event_loop().time(),
               "predicted_depth": 1.23,
               "rf_power": 1000 + (asyncio.get_event_loop().time() % 10),
               "status": "Running" 
            })
    except Exception as e:
        print(f"WS Error: {e}")
        await websocket.close()
