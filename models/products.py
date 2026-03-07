from sqlalchemy import FLOAT, Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database.db import Base

from .users import User


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    price = Column(Integer)
    color = Column(String)
    stock = Column(Integer)
    category_id = Column(Integer, ForeignKey("categories.id"))
    RAM_capacity = Column(String, nullable=True)
    built_in_memory_capacity = Column(String, nullable=True)
    screen = Column(FLOAT, nullable=True)
    cpu = Column(String, nullable=True)
    number_of_processor_cores = Column(Integer, nullable=True)
    number_of_graphics_cores = Column(Integer, nullable=True)
    verify = Column(Boolean, default=False)

    category = relationship("Category", back_populates="products")
    supplier_id = Column(Integer, ForeignKey(User.id))
    supplier = relationship("User", back_populates="products")
    reviews = relationship("Review", back_populates="product")
    carts = relationship("Cart", back_populates="product")
    files = relationship("File", back_populates="product")

    @property
    def image_urls(self) -> list[str]:
        """Ссылки на изображения из таблицы files (для обратной совместимости)."""
        return [f.file_url for f in (self.files or [])]

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Смартфон",
                "description": "Мощный смартфон с процессором последнего поколения",
                "price": 99999,
                "stock": 100,
                "category_id": 1,
                "RAM_capacity": "24 GB",
                "built_in_memory_capacity": "512 GB",
                "screen": 6.7,
                "cpu": " Apple M4 Pro",
                "number_of_processor_cores": 5,
                "number_of_graphics_cores": 5,
                "color": "Silver",
            }
        }
