"""In-memory сховище товарів замість БД — щоб демо не залежало від інфраструктури."""

from decimal import Decimal

from app.models import Product, ProductCreate


class ProductRepository:
    def __init__(self) -> None:
        self._items: dict[int, Product] = {}
        self._next_id = 1

    def seed(self) -> None:
        for name, price in [("Keyboard", "45.00"), ("Mouse", "19.99"), ("Monitor", "189.90")]:
            self.add(ProductCreate(name=name, price=Decimal(price)))

    def list(self) -> list[Product]:
        return list(self._items.values())

    def get(self, product_id: int) -> Product | None:
        return self._items.get(product_id)

    def add(self, data: ProductCreate) -> Product:
        product = Product(id=self._next_id, **data.model_dump())
        self._items[product.id] = product
        self._next_id += 1
        return product
