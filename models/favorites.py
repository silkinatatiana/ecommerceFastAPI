from sqlalchemy import Column, ForeignKey, Integer, UniqueConstraint

from database.db import Base


class Favorites(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"))

    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="_user_product_uc"),
    )
