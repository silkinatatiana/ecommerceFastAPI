from app.database.db import Base
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    username = Column(String, unique=True)
    email = Column(String, unique=True)
    hashed_password = Column(String)
    is_admin = Column(Boolean, default=False)
    role = Column(String, default='customer')

    products = relationship("Product", back_populates="supplier")
    reviews = relationship("Review", back_populates="user")
    cart = relationship('Cart', uselist=False, back_populates='user')

    chats = relationship(
        'Chats',
        foreign_keys='[Chats.user_id]',
        back_populates='user'
    )

    employee_chats = relationship(
        'Chats',
        foreign_keys='[Chats.employee_id]',
        back_populates='employee'
    )