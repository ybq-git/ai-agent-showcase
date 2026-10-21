from tests.conftest import auth, create_approved_item


def test_order_state_machine(client, buyer_token, seller_token, admin_token, category_id):
    item_id = create_approved_item(
        client, seller_token, admin_token, category_id, title="订单测试商品"
    )

    created = client.post("/api/orders", json={"item_id": item_id}, headers=auth(buyer_token))
    assert created.status_code == 201, created.text
    order_id = created.json()["id"]
    assert created.json()["status"] == "pending"

    second_buyer = client.post(
        "/api/auth/register",
        json={
            "username": "buyer2",
            "email": "buyer2@example.com",
            "password": "buyer2123",
            "role": "buyer",
        },
    )
    assert second_buyer.status_code == 201
    buyer2_token = client.post(
        "/api/auth/login", data={"username": "buyer2", "password": "buyer2123"}
    ).json()["access_token"]
    conflict = client.post("/api/orders", json={"item_id": item_id}, headers=auth(buyer2_token))
    assert conflict.status_code == 400

    complete_too_early = client.post(
        f"/api/orders/{order_id}/complete", headers=auth(buyer_token)
    )
    assert complete_too_early.status_code == 400

    confirmed = client.post(f"/api/orders/{order_id}/confirm", headers=auth(seller_token))
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "confirmed"

    completed = client.post(f"/api/orders/{order_id}/complete", headers=auth(buyer_token))
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"

    cancel_after_complete = client.post(
        f"/api/orders/{order_id}/cancel", headers=auth(buyer_token)
    )
    assert cancel_after_complete.status_code == 400

    detail = client.get(f"/api/items/{item_id}", headers=auth(buyer_token))
    assert detail.status_code == 200
    assert detail.json()["status"] == "sold"


def test_cannot_buy_own_item(client, seller_token, admin_token, category_id):
    item_id = create_approved_item(
        client, seller_token, admin_token, category_id, title="自己的商品"
    )
    response = client.post("/api/orders", json={"item_id": item_id}, headers=auth(seller_token))
    assert response.status_code == 403
