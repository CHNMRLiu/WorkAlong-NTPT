"""统一响应格式：{code, message, data}。

- 成功：code=0
- 失败：code=1
- 分页列表：data={items, total, page, page_size}
"""
from typing import Any, Optional

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


def ok(data: Any = None, message: str = "ok"):
    return JSONResponse(content={"code": 0, "message": message, "data": jsonable_encoder(data)})


def fail(message: str = "操作失败", data: Any = None):
    return JSONResponse(content={"code": 1, "message": message, "data": data})


def page(items: Any, total: int, page: int, page_size: int):
    return ok({
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    })
