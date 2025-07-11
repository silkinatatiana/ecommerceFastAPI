from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.backend.db import Base
from app.models import users, products

class Review(Base):
    __tablename__ = 'reviews'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    comment = Column(String(1000), nullable=True)
    comment_date = Column(DateTime, default=datetime.now)
    grade = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="reviews")
    product = relationship('Product', back_populates='reviews')