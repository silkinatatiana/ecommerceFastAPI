from sqlalchemy import Column, Integer, ForeignKey

from database.db import Base


class Views(Base):
    __tablename__ = "views"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer)
    count_views = Column(Integer, default=1)
