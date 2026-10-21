from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload, selectinload

from app.cache import cache
from app.database import get_db
from app.deps import get_optional_user, get_seller
from app.models import Category, Item, ItemImage, ItemStatus, Order, User, UserRole
from app.schemas import ItemCreate, ItemOut, ItemPage, ItemUpdate, Message

router = APIRouter(prefix="/api/items", tags=["items"])

ITEM_CACHE_TTL = 60
NULL_CACHE_TTL = 30


def _serialize(item: Item) -> dict:
    return ItemOut.model_validate(item).model_dump(mode="json")


def _record_view(db: Session, item_id: int) -> int:
    count = cache.incr(f"item:views:{item_id}")
    if count % 10 == 0:
        db.query(Item).filter(Item.id == item_id).update(
            {Item.view_count: Item.view_count + 10}, synchronize_session=False
        )
        db.commit()
    return count


def _load_item(db: Session, item_id: int) -> Item | None:
    return (
        db.query(Item)
        .options(
            joinedload(Item.category),
            joinedload(Item.seller),
            selectinload(Item.images),
        )
        .filter(Item.id == item_id)
        .first()
    )


@router.post("", response_model=ItemOut, status_code=status.HTTP_201_CREATED)
def create_item(
    payload: ItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_seller),
):
    if not db.get(Category, payload.category_id):
        raise HTTPException(status_code=404, detail="分类不存在")

    item = Item(
        title=payload.title,
        description=payload.description,
        price=payload.price,
        condition=payload.condition,
        category_id=payload.category_id,
        seller_id=current_user.id,
        status=ItemStatus.approved if current_user.role == UserRole.admin else ItemStatus.pending,
    )
    for index, url in enumerate(payload.image_urls):
        item.images.append(ItemImage(url=url, sort=index))
    db.add(item)
    db.commit()
    cache.bump_version("items")
    return _load_item(db, item.id)


@router.get("", response_model=ItemPage)
def list_items(
    q: str = Query(default="", max_length=100),
    category_id: int | None = None,
    sort: Literal["latest", "price_asc", "price_desc"] = "latest",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    version = cache.version("items")
    cache_key = f"items:{version}:{q}:{category_id}:{sort}:{page}:{page_size}"
    cached = cache.get_json(cache_key)
    if cached is not None:
        return cached

    query = db.query(Item).filter(Item.status == ItemStatus.approved)
    if q:
        query = query.filter(or_(Item.title.contains(q), Item.description.contains(q)))
    if category_id:
        query = query.filter(Item.category_id == category_id)

    total = query.count()
    if sort == "price_asc":
        query = query.order_by(Item.price.asc(), Item.id.desc())
    elif sort == "price_desc":
        query = query.order_by(Item.price.desc(), Item.id.desc())
    else:
        query = query.order_by(Item.created_at.desc(), Item.id.desc())

    items = (
        query.options(
            joinedload(Item.category),
            joinedload(Item.seller),
            selectinload(Item.images),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    data = {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [_serialize(item) for item in items],
    }
    cache.set_json(cache_key, data, ex=ITEM_CACHE_TTL)
    return data


@router.get("/mine", response_model=list[ItemOut])
def my_items(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_seller),
):
    items = (
        db.query(Item)
        .options(
            joinedload(Item.category),
            joinedload(Item.seller),
            selectinload(Item.images),
        )
        .filter(Item.seller_id == current_user.id)
        .order_by(Item.created_at.desc())
        .all()
    )
    return items


@router.get("/{item_id}", response_model=ItemOut)
def get_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    version = cache.version("items")
    cache_key = f"item:{item_id}:{version}"

    def cached_response(cached: dict) -> dict:
        if cached.get("__null__"):
            raise HTTPException(status_code=404, detail="商品不存在")
        base = int(cached.get("view_count", 0))
        count = _record_view(db, item_id)
        if count % 10 == 0:
            cached["view_count"] = base + 10
            cache.set_json(cache_key, cached, ex=ITEM_CACHE_TTL)
            return cached
        result = dict(cached)
        result["view_count"] = base + (count % 10)
        return result

    cached = cache.get_json(cache_key)
    if cached is not None:
        return cached_response(cached)

    # 缓存击穿保护：同一 key 只放一个请求回源，其余请求拿锁后重查缓存
    with cache.mutex(f"lock:{cache_key}"):
        cached = cache.get_json(cache_key)
        if cached is not None:
            return cached_response(cached)

        item = _load_item(db, item_id)
        public_statuses = (ItemStatus.approved, ItemStatus.reserved, ItemStatus.sold)
        is_public = item is not None and item.status in public_statuses
        visible = is_public or (
            item is not None
            and current_user is not None
            and (current_user.id == item.seller_id or current_user.role == UserRole.admin)
        )
        if not visible:
            cache.set_json(cache_key, {"__null__": True}, ex=NULL_CACHE_TTL)
            raise HTTPException(status_code=404, detail="商品不存在")

        data = _serialize(item)
        base = int(data.get("view_count", 0))
        count = _record_view(db, item_id)
        if count % 10 == 0:
            data["view_count"] = base + 10
        else:
            data["view_count"] = base + (count % 10)
        if is_public:
            cache.set_json(cache_key, {**data, "view_count": base}, ex=ITEM_CACHE_TTL)
        return data


@router.patch("/{item_id}", response_model=ItemOut)
def update_item(
    item_id: int,
    payload: ItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_seller),
):
    item = _load_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="商品不存在")
    if item.seller_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="只能修改自己的商品")

    changes = payload.model_dump(exclude_unset=True)
    image_urls = changes.pop("image_urls", None)
    if "category_id" in changes and not db.get(Category, changes["category_id"]):
        raise HTTPException(status_code=404, detail="分类不存在")
    for field, value in changes.items():
        setattr(item, field, value)
    if image_urls is not None:
        item.images.clear()
        for index, url in enumerate(image_urls):
            item.images.append(ItemImage(url=url, sort=index))
    if current_user.role != UserRole.admin:
        item.status = ItemStatus.pending
        item.reject_reason = None
    db.commit()
    cache.bump_version("items")
    return _load_item(db, item.id)


@router.post("/{item_id}/off-shelf", response_model=Message)
def off_shelf(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_seller),
):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="商品不存在")
    if item.seller_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="只能操作自己的商品")
    if item.status in (ItemStatus.reserved, ItemStatus.sold):
        raise HTTPException(status_code=400, detail="交易中的商品不能下架")
    item.status = ItemStatus.off_shelf
    db.commit()
    cache.bump_version("items")
    return Message(detail="商品已下架")


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_seller),
):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="商品不存在")
    if item.seller_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="只能删除自己的商品")
    if db.query(Order).filter(Order.item_id == item_id).first():
        raise HTTPException(status_code=400, detail="商品已有订单，不能删除")
    db.delete(item)
    db.commit()
    cache.bump_version("items")
