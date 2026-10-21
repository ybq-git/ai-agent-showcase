import os
import sys
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test_campus.db"
os.environ["REDIS_URL"] = ""
os.environ["JWT_SECRET"] = "test-secret-please-use-32-bytes-ok"

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pytest
from fastapi.testclient import TestClient

from app.cache import cache
from app.database import Base, SessionLocal, engine
from app.main import app
from app.models import Category, User, UserRole
from app.security import hash_password


@pytest.fixture(autouse=True)
def clean_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    cache._fallback._data.clear()
    yield


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def category_id(client):
    db = SessionLocal()
    try:
        category = Category(name="数码", sort=0)
        db.add(category)
        db.commit()
        db.refresh(category)
        return category.id
    finally:
        db.close()


@pytest.fixture()
def admin_token(client):
    db = SessionLocal()
    try:
        db.add(
            User(
                username="admin",
                email="admin@example.com",
                password_hash=hash_password("admin123"),
                role=UserRole.admin,
            )
        )
        db.commit()
    finally:
        db.close()
    return _login(client, "admin", "admin123")


@pytest.fixture()
def seller_token(client):
    return _register(client, "seller", "seller@example.com", "seller123", "seller")


@pytest.fixture()
def buyer_token(client):
    return _register(client, "buyer", "buyer@example.com", "buyer123", "buyer")


def _register(client, username, email, password, role="buyer") -> str:
    response = client.post(
        "/api/auth/register",
        json={"username": username, "email": email, "password": password, "role": role},
    )
    assert response.status_code == 201, response.text
    return _login(client, username, password)


def _login(client, username, password) -> str:
    response = client.post(
        "/api/auth/login",
        data={"username": username, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def create_approved_item(client, seller_token, admin_token, category_id, title="二手自行车", price="100.00"):
    response = client.post(
        "/api/items",
        json={
            "title": title,
            "description": "测试商品",
            "price": price,
            "condition": "good",
            "category_id": category_id,
            "image_urls": ["https://example.com/a.jpg"],
        },
        headers=auth(seller_token),
    )
    assert response.status_code == 201, response.text
    item_id = response.json()["id"]
    response = client.post(
        f"/api/admin/items/{item_id}/audit",
        json={"approve": True},
        headers=auth(admin_token),
    )
    assert response.status_code == 200, response.text
    return item_id
