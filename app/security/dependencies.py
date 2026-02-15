from fastapi import Depends, HTTPException, status
from app.security.auth import get_current_user
from app.models.user import User

def require_admin(user: User = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin only"
        )
    return user
