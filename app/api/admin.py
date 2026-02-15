from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.database import get_db
from app.models.user import User
from app.security.encryption import hash_password
from app.security.dependencies import require_admin

router = APIRouter(prefix="/admin", tags=["Admin"])


class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str
    is_admin: bool = False


@router.post(
    "/create-user",
    operation_id="admin_create_user"
)
def create_user(
    data: CreateUserRequest,
    db: Session = Depends(get_db),
    #admin = Depends(require_admin)   # 🔒 ADMIN ONLY
):
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        role="admin" if data.is_admin else "user"
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "message": "User created",
        "user_id": user.id
    }
