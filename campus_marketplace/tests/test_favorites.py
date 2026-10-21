from tests.conftest import auth, create_approved_item


def test_favorite_add_list_remove(client, buyer_token, seller_token, admin_token, category_id):
    item_id = create_approved_item(
        client, seller_token, admin_token, category_id, title="收藏测试商品"
    )

    created = client.post(f"/api/items/{item_id}/favorite", headers=auth(buyer_token))
    assert created.status_code == 201, created.text
    assert created.json()["item"]["id"] == item_id

    duplicate = client.post(f"/api/items/{item_id}/favorite", headers=auth(buyer_token))
    assert duplicate.status_code == 400

    favorites = client.get("/api/favorites", headers=auth(buyer_token))
    assert favorites.status_code == 200
    assert len(favorites.json()) == 1

    removed = client.delete(f"/api/items/{item_id}/favorite", headers=auth(buyer_token))
    assert removed.status_code == 204
    assert client.get("/api/favorites", headers=auth(buyer_token)).json() == []
