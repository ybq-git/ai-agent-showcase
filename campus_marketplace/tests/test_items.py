from tests.conftest import auth, create_approved_item


def test_item_visibility_audit_and_permissions(
    client, seller_token, buyer_token, admin_token, category_id
):
    create = client.post(
        "/api/items",
        json={
            "title": "宿舍台灯",
            "description": "三档亮度",
            "price": "35.00",
            "condition": "good",
            "category_id": category_id,
            "image_urls": [],
        },
        headers=auth(seller_token),
    )
    assert create.status_code == 201, create.text
    item_id = create.json()["id"]
    assert create.json()["status"] == "pending"

    public_list = client.get("/api/items")
    assert public_list.json()["total"] == 0

    forbidden = client.post(
        "/api/items",
        json={
            "title": "买家不能发布",
            "price": "10.00",
            "category_id": category_id,
        },
        headers=auth(buyer_token),
    )
    assert forbidden.status_code == 403

    audit = client.post(
        f"/api/admin/items/{item_id}/audit",
        json={"approve": True},
        headers=auth(admin_token),
    )
    assert audit.status_code == 200
    assert audit.json()["status"] == "approved"

    public_list = client.get("/api/items")
    assert public_list.json()["total"] == 1
    detail = client.get(f"/api/items/{item_id}")
    assert detail.status_code == 200
    assert detail.json()["seller_name"] == "seller"

    buyer_edit = client.patch(
        f"/api/items/{item_id}",
        json={"title": "越权修改"},
        headers=auth(buyer_token),
    )
    assert buyer_edit.status_code == 403

    seller_edit = client.patch(
        f"/api/items/{item_id}",
        json={"price": "30.00"},
        headers=auth(seller_token),
    )
    assert seller_edit.status_code == 200
    assert seller_edit.json()["status"] == "pending"


def test_search_filter_and_pagination(client, seller_token, admin_token, category_id):
    for index, (title, price) in enumerate(
        [("自行车", "100.00"), ("台灯", "30.00"), ("教材", "20.00")]
    ):
        create_approved_item(
            client,
            seller_token,
            admin_token,
            category_id,
            title=title,
            price=price,
        )

    result = client.get("/api/items", params={"q": "车"})
    assert result.status_code == 200
    assert result.json()["total"] == 1

    page = client.get("/api/items", params={"page": 1, "page_size": 2, "sort": "price_asc"})
    body = page.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2
    assert body["items"][0]["title"] == "教材"
