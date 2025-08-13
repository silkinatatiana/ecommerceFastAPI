from sqlalchemy.orm import relationship

from app.backend.db import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.sql import func

from app.config import Statuses


class Orders(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    products = Column(JSON, nullable=False)
    summa = Column(Integer, nullable=False)
    date = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, nullable=False, server_default=Statuses.DESIGNED)