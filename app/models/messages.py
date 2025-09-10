from app.backend.db import Base
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship


class Messages(Base):
    __tablename__ = 'messages'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False)
    message = Column(String)
    sender_id = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


    chat = relationship("Chats", back_populates="messages")
