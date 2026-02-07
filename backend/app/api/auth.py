from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import settings
from app.core.auth import create_access_token, verify_token
from app.schemas.auth import LoginRequest, TokenResponse, ChangePasswordRequest

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Mutable runtime password override (in-memory only, resets on restart)
_runtime_password: str | None = None


def _get_password() -> str:
    return _runtime_password if _runtime_password is not None else settings.ADMIN_PASSWORD


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    if req.username != settings.ADMIN_USERNAME or req.password != _get_password():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(data={"sub": req.username})
    return TokenResponse(access_token=token)


@router.post("/change-password", dependencies=[Depends(verify_token)])
async def change_password(req: ChangePasswordRequest):
    global _runtime_password
    if req.old_password != _get_password():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="当前密码错误")
    if len(req.new_password) < 4:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="新密码长度至少 4 位")
    _runtime_password = req.new_password
    return {"detail": "密码已修改"}
