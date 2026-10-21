from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload, selectinload

from app.database import get_db
from app.deps import get_current_user
from app.models import Favorite, Item, ItemStatus, User
from app.schemas import FavoriteOut

router = APIRouter(prefix="/api", tags=["favorites"])


def _favorite_query(db: Session):
    return db.query(Favorite).options(
        joinedload(Favorite.item).joinedload(Item.category),
        joinedload(Favorite.item).joinedload(Item.seller),
        joinedload(Favorite.item).selectinload(Item.images),
    )


@router.post("/items/{item_id}/favorite", response_model=FavoriteOut, status_code=status.HTTP_201_CREATED)
def add_favorite(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = db.get(Item, item_id)
    if not item or item.status != ItemStatus.approved:
        raise HTTPException(status_code=404, detail="商品不存在或未上架")
    exists = (
        db.query(Favorite)
        .filter(Favorite.user_id == current_user.id, Favorite.item_id == item_id)
        .first()
    )
    if exists:
        raise HTTPException(status_code=400, detail="已经收藏过该商品")
    favorite = Favorite(user_id=current_user.id, item_id=item_id)
    db.add(favorite)
    db.commit()
    return _favorite_query(db).filter(Favorite.id == favorite.id).first()


@router.delete("/items/{item_id}/favorite", status_code=status.HTTP_204_NO_CONTENT)
def remove_favorite(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    favorite = (
        db.query(Favorite)
        .filter(Favorite.user_id == current_user.id, Favorite.item_id == item_id)
        .first()
    )
    if not favorite:
        raise HTTPException(status_code=404, detail="尚未收藏该商品")
    db.delete(favorite)
    db.commit()


@router.get("/favorites", response_model=list[FavoriteOut])
def list_favorites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        _favorite_query(db)
        .filter(Favorite.user_id == current_user.id)
        .order_by(Favorite.created_at.desc())
        .all()
    )
