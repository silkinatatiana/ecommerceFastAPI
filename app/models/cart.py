from sqlalchemy.orm import relationship

from app.database.db import Base
from sqlalchemy import Column, Integer, ForeignKey


class Cart(Base):
    __tablename__ = "cart"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    count = Column(Integer)

    product = relationship('Product', back_populates='carts')
    user = relationship('User', back_populates='cart')