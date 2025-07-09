from pydantic import BaseModel, Field
from datetime import datetime


class CreateProduct(BaseModel):
    name: str
    description: str
    price: int
    image_url: str
    stock: int
    category_id: int


class CreateCategory(BaseModel):
    name: str

    class Config:
        orm_mode = True


class CreateUser(BaseModel):
    first_name: str
    last_name: str
    username: str
    email: str
    password: str


class CreateReviews(BaseModel):
    grade: int = Field(..., ge=1, le=5)
    comment: str = None
    comment_date: datetime = Field(default_factory=datetime.now)
    is_active: bool = True