from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload, selectinload

from app.cache import cache
from app.database import get_db
from app.deps import get_admin
from app.models import Item, ItemStatus, User
from app.schemas import AuditRequest, ItemOut, Message, UserOut

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/items", response_model=list[ItemOut])
def admin_items(
    item_status: ItemStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    _: User = Depends(get_admin),
):
    query = db.query(Item).options(
        joinedload(Item.category),
        joinedload(Item.seller),
        selectinload(Item.images),
    )
    if item_status:
        query = query.filter(Item.status == item_status)
    return query.order_by(Item.created_at.desc()).all()


@router.post("/items/{item_id}/audit", response_model=ItemOut)
def audit_item(
    item_id: int,
    payload: AuditRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin),
):
    item = (
        db.query(Item)
        .options(joinedload(Item.category), joinedload(Item.seller), selectinload(Item.images))
        .filter(Item.id == item_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="商品不存在")
    if item.status not in (ItemStatus.pending, ItemStatus.rejected):
        raise HTTPException(status_code=400, detail="当前状态不能审核")
    item.status = ItemStatus.approved if payload.approve else ItemStatus.rejected
    item.reject_reason = None if payload.approve else (payload.reason or "不符合平台规范")
    db.commit()
    cache.bump_version("items")
    db.refresh(item)
    return item


@router.get("/users", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(get_admin),
):
    return db.query(User).order_by(User.id).all()


@router.post("/users/{user_id}/ban", response_model=Message)
def toggle_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_admin),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.id == current_admin.id:
        raise HTTPException(status_code=400, detail="不能禁用自己")
    user.is_active = not user.is_active
    db.commit()
    return Message(detail="已禁用" if not user.is_active else "已启用")
