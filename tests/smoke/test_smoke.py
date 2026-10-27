"""Smoke-тести: запускаються проти РЕАЛЬНО розгорнутого сервісу (Docker-контейнер
у CI або staging після деплою). Адреса задається змінною BASE_URL."""

import os

import httpx
import pytest

BASE_URL = os.getenv("BASE_URL")

pytestmark = pytest.mark.skipif(not BASE_URL, reason="BASE_URL is not set")


def test_service_is_healthy():
    response = httpx.get(f"{BASE_URL}/health", timeout=5)
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_quote_endpoint_works():
    payload = {"items": [{"product_id": 1, "quantity": 1}], "promo_code": "SAVE10"}
    response = httpx.post(f"{BASE_URL}/orders/quote", json=payload, timeout=5)
    assert response.status_code == 200
    assert response.json()["total"] == "40.50"
