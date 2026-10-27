import os
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException

from app import pricing
from app.models import Product, ProductCreate, QuoteRequest, QuoteResponse
from app.repository import ProductRepository

APP_VERSION = os.getenv("APP_VERSION", "dev")

app = FastAPI(title="Shop Pricing API", version=APP_VERSION)

_repo = ProductRepository()
_repo.seed()


def get_repo() -> ProductRepository:
    return _repo


Repo = Annotated[ProductRepository, Depends(get_repo)]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": APP_VERSION}


@app.get("/products", response_model=list[Product])
def list_products(repo: Repo):
    return repo.list()


@app.get("/products/{product_id}", response_model=Product)
def get_product(product_id: int, repo: Repo):
    product = repo.get(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.post("/products", response_model=Product, status_code=201)
def create_product(data: ProductCreate, repo: Repo):
    return repo.add(data)


@app.post("/orders/quote", response_model=QuoteResponse)
def quote_order(request: QuoteRequest, repo: Repo):
    lines = []
    for item in request.items:
        product = repo.get(item.product_id)
        if product is None:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
        lines.append((product.price, item.quantity))
    try:
        return pricing.quote(lines, request.promo_code)
    except pricing.PricingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
