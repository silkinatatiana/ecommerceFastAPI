from app.database.db import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship


class Chats(Base):
    __tablename__ = 'chats'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    topic = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    active = Column(Boolean, nullable=False, default=True)

    messages = relationship("Messages", back_populates="chat")

    user = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="chats"
    )

    employee = relationship(
        "User",
        foreign_keys=[employee_id],
        back_populates="employee_chats"
    )
