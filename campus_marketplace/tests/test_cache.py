from app.database import SessionLocal
from app.models import Item
from tests.conftest import create_approved_item


def test_view_counter_flushes_every_ten_views(
    client, buyer_token, seller_token, admin_token, category_id
):
    item_id = create_approved_item(
        client, seller_token, admin_token, category_id, title="浏览量测试商品"
    )
    for _ in range(10):
        response = client.get(f"/api/items/{item_id}")
        assert response.status_code == 200

    db = SessionLocal()
    try:
        item = db.get(Item, item_id)
        assert item is not None
        assert item.view_count == 10
    finally:
        db.close()


def test_missing_item_is_cached_as_null(client):
    first = client.get("/api/items/99999")
    second = client.get("/api/items/99999")
    assert first.status_code == 404
    assert second.status_code == 404
