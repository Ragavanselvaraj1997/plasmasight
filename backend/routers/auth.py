from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from ..auth import create_access_token, get_current_user, verify_password, get_password_hash
from ..database import get_db
from ..models_sql import User, Role
from pydantic import BaseModel
from datetime import timedelta
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_access_token(
        data={"sub": user.username}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/user")
async def get_user_info(current_user: dict = Depends(get_current_user)):
    return current_user

@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    return {"status": "token_invalidated"}

@router.get("/roles")
async def view_roles(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    roles = db.query(Role).all()
    return [{"role_id": r.role_id, "name": r.name} for r in roles]
