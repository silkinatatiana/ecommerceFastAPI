from app.backend.db import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.sql import func


class Orders(Base):
    __tablename__ = "Orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    products = Column(JSON, nullable=False)
    summa = Column(Integer)
    date = Column(DateTime, server_default=func.now())
    status = Column(String) # по умолч оформлен Добавить все статус в файлик конфиг (status.start = "Оформлен" и так для всех статусов)
    # Статусы: оформлен, на сборке, отправлен, доставлен, завершен, отменен
