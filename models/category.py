from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from database.db import Base


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)

    products = relationship("Product", back_populates="category")

    def __str__(self):
        return self.name or ""

    class Config:
        json_schema_extra = {"example": {"id": 1, "name": "Электроника"}}
