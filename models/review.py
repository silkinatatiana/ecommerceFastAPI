from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database.db import Base


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"))
    comment = Column(String(1000), nullable=True)
    comment_date = Column(DateTime, default=datetime.now)
    grade = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    photo_urls = Column(JSON, nullable=True)

    user = relationship("User", back_populates="reviews")
    product = relationship("Product", back_populates="reviews")
