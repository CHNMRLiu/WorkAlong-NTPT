"""鉴权依赖：从 Bearer Token 解析当前用户。"""
from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..utils.security import decode_access_token


def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
) -> User:
    """解析 JWT，返回当前登录用户；无效则 401。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录或令牌缺失")
    token = authorization.split(" ", 1)[1]
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="令牌无效或已过期")
    user = db.query(User).filter(User.username == payload.get("sub")).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="用户不存在或已停用")
    return user


def record_log(db: Session, user: User, module: str, action: str,
               request=None, extra: str = ""):
    """写入操作日志（异常不阻断主流程）。"""
    try:
        from ..models import OperationLog
        ip = ""
        ua = ""
        if request is not None:
            ip = request.client.host if request.client else ""
            ua = request.headers.get("user-agent", "")
        log = OperationLog(
            user_id=user.id if user else None,
            username=user.username if user else "",
            module=module,
            action=action,
            ip=ip,
            user_agent=ua,
        )
        db.add(log)
        db.commit()
    except Exception:
        db.rollback()
