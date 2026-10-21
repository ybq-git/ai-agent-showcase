"""Create demo users, categories and items. Run: python seed.py"""

from app.database import Base, SessionLocal, engine
from app.models import Category, Item, ItemCondition, ItemImage, ItemStatus, User, UserRole
from app.security import hash_password


def get_or_create_user(db, username: str, email: str, password: str, role: UserRole) -> User:
    user = db.query(User).filter(User.username == username).first()
    if user:
        return user
    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        role=role,
    )
    db.add(user)
    db.flush()
    return user


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        admin = get_or_create_user(db, "admin", "admin@example.com", "admin123", UserRole.admin)
        seller = get_or_create_user(db, "seller", "seller@example.com", "seller123", UserRole.seller)
        get_or_create_user(db, "buyer", "buyer@example.com", "buyer123", UserRole.buyer)

        category_names = ["数码", "图书", "生活用品", "运动户外", "其他"]
        categories = {}
        for index, name in enumerate(category_names):
            category = db.query(Category).filter(Category.name == name).first()
            if not category:
                category = Category(name=name, sort=index)
                db.add(category)
                db.flush()
            categories[name] = category

        if db.query(Item).count() == 0:
            demo_items = [
                ("九成新 iPad 2021", "校内自提，屏幕无划痕，配充电器。", 1600, ItemCondition.like_new, "数码"),
                ("高等数学同济第七版", "上下册，少量笔记，不影响使用。", 25, ItemCondition.good, "图书"),
                ("宿舍护眼台灯", "三档亮度，用了半年，功能正常。", 35, ItemCondition.good, "生活用品"),
                ("捷安特山地车", "毕业出，刹车和变速都正常，可试骑。", 480, ItemCondition.good, "运动户外"),
            ]
            for title, description, price, condition, category_name in demo_items:
                item = Item(
                    title=title,
                    description=description,
                    price=price,
                    condition=condition,
                    category_id=categories[category_name].id,
                    seller_id=seller.id,
                    status=ItemStatus.approved,
                )
                item.images.append(ItemImage(url=f"https://picsum.photos/seed/{len(title)}/600/400", sort=0))
                db.add(item)

        db.commit()
        print("seed ok")
        print("admin  / admin123")
        print("seller / seller123")
        print("buyer  / buyer123")
        print("admin id:", admin.id)
    finally:
        db.close()


if __name__ == "__main__":
    main()
