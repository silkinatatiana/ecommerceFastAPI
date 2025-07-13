from app.backend.db import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .users import User

class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, nullable=False)
    description = Column(String)
    price = Column(Integer)
    image_urls =  Column(JSON, default=list)
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
                "name": "Смартфон",
                "slug": "smartphone",
                "description": "Мощный смартфон с процессором последнего поколения",
                "price": 99999,
                "image_urls": ["https://example.com/phone1.jpg", "https://example.com/phone2.jpg"],
                "stock": 100,
                "rating": 5,
                "is_active": True,
                "category_id": 1,
                "supplier_id": 1
            }
        }
