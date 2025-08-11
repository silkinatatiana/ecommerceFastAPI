from app.backend.db import Base
from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint


class Cart(Base):
    __tablename__ = "cart"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    count = Column(Integer)

    __table_args__ = (
        UniqueConstraint('user_id', 'product_id', name='_user_product_uc'),
    )
