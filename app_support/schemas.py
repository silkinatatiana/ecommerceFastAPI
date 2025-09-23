from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional


class OrderResponse(BaseModel):
    id: int
    user_id: int
    products: dict
    summa: int
    date: datetime
    status: str

    class Config:
        from_attributes = True