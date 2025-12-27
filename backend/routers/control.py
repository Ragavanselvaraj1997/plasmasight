from fastapi import APIRouter, Depends
from ..auth import get_current_user, RoleChecker
from ..models_redis import RedisModels
from ..database import get_db
from ..models_sql import ControlCommand
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

router = APIRouter(prefix="/api/v1", tags=["control"])

class ActuationCommand(BaseModel):
    delta_RF: float
    delta_gas: float

@router.post("/control/actuate")
async def actuate(cmd: ActuationCommand, user: dict = Depends(RoleChecker(["internal"])), db: Session = Depends(get_db)):
    # 1. Log to DB
    command = ControlCommand(
        timestamp=datetime.utcnow(),
        delta_RF=cmd.delta_RF,
        delta_gas=cmd.delta_gas,
        source="auto"
    )
    db.add(command)
    db.commit()

    # 2. Update Redis Cache
    RedisModels.update_control_state(0.0, cmd.dict())
    
    # 3. Logic to send command to OPC/PLC layer (omitted for now)
    return {"status": "command_sent", "command_id": command.command_id}

@router.get("/control/status")
async def get_control_status(user: dict = Depends(get_current_user)):
    state = RedisModels.get_control_state()
    return state or {"status": "inactive"}

class OverrideCommand(BaseModel):
    manual_override: bool
    values: dict

@router.post("/control/override")
async def control_override(cmd: OverrideCommand, user: dict = Depends(RoleChecker(["admin"]))):
    return {"status": "override_applied", "manual_mode": cmd.manual_override}
