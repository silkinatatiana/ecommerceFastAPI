from app.database.db import Base
from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship


class Favorites(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))

    __table_args__ = (
        UniqueConstraint('user_id', 'product_id', name='_user_product_uc'),
    )

    # user = relationship("User", back_populates="favorites")
    # products = relationship("Product", back_populates="in_favorites")

