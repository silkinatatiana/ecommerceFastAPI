from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.sql import func

from app.config import Statuses
from app.database.db import Base


class Orders(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    products = Column(JSON, nullable=False)  # dict{product_id: {‘price’: price, ‘count’: count}}
    summa = Column(Integer, nullable=False)
    date = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, nullable=False, server_default=Statuses.DESIGNED)
