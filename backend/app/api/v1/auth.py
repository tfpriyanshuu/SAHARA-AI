from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List, Dict, Any

from app.core.database import get_db
from app.core.security import verify_password, create_access_token, get_password_hash
from app.core.config import settings
from app.models.user import User
from app.schemas.user import LoginRequest, Token, UserResponse
from app.api.deps import get_current_user, log_audit

router = APIRouter()


@router.post("/login", response_model=Token)
def login(login_req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == login_req.username).first()
    if not user or not verify_password(login_req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token = create_access_token(subject=user.username, role=user.role)
    log_audit(db, user, action="USER_LOGIN", resource_type="AUTH", resource_id=str(user.id), details=f"User {user.username} logged in with role {user.role}")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    log_audit(db, current_user, action="USER_LOGOUT", resource_type="AUTH", resource_id=str(current_user.id), details=f"User {current_user.username} logged out")
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/demo-users")
def get_demo_users(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Return pre-seeded demo personas for hackathon judges with one-click credentials."""
    users = db.query(User).all()
    demo_list = []
    default_passwords = {
        "coordinator1": "coord123",
        "anvesha": "coord123",
        "senior1": "senior123",
        "harshit": "senior123",
        "family1": "family123",
        "anchal": "family123",
        "ops1": "ops123"
    }
    for u in users:
        demo_list.append({
            "id": u.id,
            "username": u.username,
            "full_name": u.full_name,
            "role": u.role,
            "city": u.city,
            "phone": u.phone,
            "demo_password": default_passwords.get(u.username, "password123")
        })
    return demo_list

