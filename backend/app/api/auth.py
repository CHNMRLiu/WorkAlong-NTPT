"""认证接口：登录、获取当前用户、修改密码。"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import (
    ChangePasswordRequest,
    LoginRequest,
    UserResponse,
)
from ..utils.response import fail, ok
from ..utils.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from .deps import get_current_user, record_log

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/login")
def login(req: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        return fail("用户名或密码错误")
    if not user.is_active:
        return fail("账号已停用")
    token = create_access_token(user.username, user.id)
    record_log(db, user, "认证", "登录", request)
    return ok({
        "token": token,
        "user": UserResponse.model_validate(user).model_dump(),
    })


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return ok(UserResponse.model_validate(current_user).model_dump())


@router.post("/change-password")
def change_password(
    req: ChangePasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(req.old_password, current_user.password_hash):
        return fail("原密码错误")
    if len(req.new_password) < 6:
        return fail("新密码至少 6 位")
    current_user.password_hash = hash_password(req.new_password)
    db.commit()
    record_log(db, current_user, "认证", "修改密码", request)
    return ok(message="密码已修改")


@router.get("/users")
def list_users(db: Session = Depends(get_db),
               current_user: User = Depends(get_current_user)):
    users = db.query(User).order_by(User.id).all()
    return ok([UserResponse.model_validate(u).model_dump() for u in users])
