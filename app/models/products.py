from app.backend.db import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .users import User


class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False)
    description = Column(String)
    price = Column(Integer)
    image_url = Column(String)
    stock = Column(Integer)
    rating = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    category_id = Column(Integer, ForeignKey('categories.id'))

    category = relationship("Category", back_populates="products")
    supplier_id = Column(Integer, ForeignKey(User.id))
    supplier = relationship("User", back_populates="products")
    reviews = relationship("Review", back_populates="product")

    class Config:
        json_schema_extra = {
            "example": {
                "id": Column(Integer, primary_key=True, autoincrement=True),
                "name": "Смартфон",
                "description": "Мощный смартфон",
                "price": 999.99,
                "image_url": "https://example.com/phone.jpg",
                "category_id": 1
            }
        }