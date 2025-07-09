from app.backend.db import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship



class Category(Base):
    __tablename__ = 'categories'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    slug = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)

    products = relationship("Product", back_populates="category")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Электроника"
            }
        }


# from sqlalchemy.schema import CreateTable
# print(CreateTable(Product.__table__))
# print(CreateTable(Category.__table__))