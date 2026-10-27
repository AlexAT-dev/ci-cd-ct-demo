from decimal import Decimal

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: Decimal = Field(ge=0, decimal_places=2)


class Product(ProductCreate):
    id: int


class OrderItem(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class QuoteRequest(BaseModel):
    items: list[OrderItem] = Field(min_length=1)
    promo_code: str | None = None


class QuoteResponse(BaseModel):
    subtotal: Decimal
    discount: Decimal
    total: Decimal
