"""Integration-тести: піднімають увесь FastAPI-застосунок у пам'яті й ходять
через HTTP (TestClient). Перевіряють роутинг, валідацію, серіалізацію та
взаємодію API <-> repository <-> pricing разом."""

import pytest
from fastapi.testclient import TestClient

from app.main import app, get_repo
from app.repository import ProductRepository


@pytest.fixture
def client():
    # Кожен тест отримує чисте сховище — тести не впливають один на одного.
    repo = ProductRepository()
    repo.seed()
    app.dependency_overrides[get_repo] = lambda: repo
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_list_products(client):
    response = client.get("/products")
    assert response.status_code == 200
    assert [p["name"] for p in response.json()] == ["Keyboard", "Mouse", "Monitor"]


def test_get_missing_product_returns_404(client):
    assert client.get("/products/999").status_code == 404


def test_create_and_fetch_product(client):
    created = client.post("/products", json={"name": "Webcam", "price": "59.00"})
    assert created.status_code == 201
    product_id = created.json()["id"]

    fetched = client.get(f"/products/{product_id}")
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "Webcam"


def test_create_product_validation_error(client):
    response = client.post("/products", json={"name": "", "price": "-5"})
    assert response.status_code == 422


def test_quote_with_promo(client):
    payload = {
        "items": [{"product_id": 1, "quantity": 2}, {"product_id": 3, "quantity": 1}],
        "promo_code": "MINUS50",
    }
    response = client.post("/orders/quote", json=payload)
    assert response.status_code == 200
    # 2*45.00 + 189.90 = 279.90; MINUS50 -> 229.90
    assert response.json() == {"subtotal": "279.90", "discount": "50.00", "total": "229.90"}


def test_quote_unknown_product(client):
    response = client.post("/orders/quote", json={"items": [{"product_id": 42, "quantity": 1}]})
    assert response.status_code == 404


def test_quote_business_rule_violation(client):
    payload = {"items": [{"product_id": 2, "quantity": 1}], "promo_code": "MINUS50"}
    response = client.post("/orders/quote", json=payload)
    assert response.status_code == 422
    assert "requires subtotal" in response.json()["detail"]
