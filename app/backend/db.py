from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase


class Base(DeclarativeBase):
    engine = create_engine('sqlite:///ecommerce.db', echo=True)
    SessionLocal = sessionmaker(bind=engine)