from pydantic import BaseModel, Field
from datetime import datetime


class CreateProduct(BaseModel):
    name: str
    description: str
    price: int
    image_url: str
    stock: int
    category: int


class CreateCategory(BaseModel):
    name: str
    parent_id: int | None = None


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
