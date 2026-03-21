from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from database.db import Base


class Cart(Base):
    __tablename__ = "cart"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"))
    count = Column(Integer)

    product = relationship("Product", back_populates="carts")
    user = relationship("User", back_populates="cart")
