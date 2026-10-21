from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.cache import cache
from app.database import get_db
from app.deps import get_current_user
from app.models import Item, ItemStatus, Order, OrderStatus, User, UserRole
from app.schemas import Message, OrderCreate, OrderOut, OrderPage

router = APIRouter(prefix="/api/orders", tags=["orders"])


def _order_query(db: Session):
    return db.query(Order).options(
        joinedload(Order.item),
        joinedload(Order.buyer),
        joinedload(Order.seller),
    )


def _get_order_for_update(db: Session, order_id: int) -> Order | None:
    return db.query(Order).filter(Order.id == order_id).with_for_update().first()


def _ensure_participant(order: Order, user: User) -> None:
    if user.role != UserRole.admin and user.id not in (order.buyer_id, order.seller_id):
        raise HTTPException(status_code=403, detail="无权查看该订单")


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in (UserRole.buyer, UserRole.admin):
        raise HTTPException(status_code=403, detail="只有买家可以下单")

    item = (
        db.query(Item)
        .filter(Item.id == payload.item_id)
        .with_for_update()
        .first()
    )
    if not item or item.status != ItemStatus.approved:
        raise HTTPException(status_code=400, detail="商品不可购买")
    if item.seller_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能购买自己的商品")

    active = (
        db.query(Order)
        .filter(
            Order.item_id == item.id,
            Order.status.in_([OrderStatus.pending, OrderStatus.confirmed]),
        )
        .first()
    )
    if active:
        raise HTTPException(status_code=400, detail="商品已有进行中的订单")

    order = Order(
        item_id=item.id,
        buyer_id=current_user.id,
        seller_id=item.seller_id,
        price=item.price,
        status=OrderStatus.pending,
    )
    item.status = ItemStatus.reserved
    db.add(order)
    db.commit()
    cache.bump_version("items")
    return _order_query(db).filter(Order.id == order.id).first()


@router.get("", response_model=OrderPage)
def list_orders(
    role: Literal["buyer", "seller"] | None = None,
    order_status: OrderStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = _order_query(db)
    if current_user.role != UserRole.admin:
        if role == "seller":
            query = query.filter(Order.seller_id == current_user.id)
        elif role == "buyer":
            query = query.filter(Order.buyer_id == current_user.id)
        else:
            query = query.filter(
                (Order.buyer_id == current_user.id) | (Order.seller_id == current_user.id)
            )
    if order_status:
        query = query.filter(Order.status == order_status)
    orders = query.order_by(Order.created_at.desc()).all()
    return {"total": len(orders), "items": orders}


@router.get("/{order_id}", response_model=OrderOut)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = _order_query(db).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    _ensure_participant(order, current_user)
    return order


@router.post("/{order_id}/confirm", response_model=OrderOut)
def confirm_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = _get_order_for_update(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if current_user.id != order.seller_id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="只有卖家可以确认订单")
    if order.status != OrderStatus.pending:
        raise HTTPException(status_code=400, detail="当前状态不能确认订单")
    order.status = OrderStatus.confirmed
    db.commit()
    return _order_query(db).filter(Order.id == order.id).first()


@router.post("/{order_id}/complete", response_model=OrderOut)
def complete_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = _get_order_for_update(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if current_user.id != order.buyer_id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="只有买家可以完成订单")
    if order.status != OrderStatus.confirmed:
        raise HTTPException(status_code=400, detail="只有已确认的订单可以完成")
    order.status = OrderStatus.completed
    item = db.get(Item, order.item_id)
    if item:
        item.status = ItemStatus.sold
    db.commit()
    cache.bump_version("items")
    return _order_query(db).filter(Order.id == order.id).first()


@router.post("/{order_id}/cancel", response_model=Message)
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = _get_order_for_update(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if current_user.id not in (order.buyer_id, order.seller_id) and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="无权取消该订单")
    if order.status not in (OrderStatus.pending, OrderStatus.confirmed):
        raise HTTPException(status_code=400, detail="当前状态不能取消订单")
    order.status = OrderStatus.cancelled
    item = db.get(Item, order.item_id)
    if item and item.status == ItemStatus.reserved:
        item.status = ItemStatus.approved
    db.commit()
    cache.bump_version("items")
    return Message(detail="订单已取消")
