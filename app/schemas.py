from pydantic import BaseModel, Field
from datetime import datetime
from typing import List


class CreateProduct(BaseModel):
    name: str
    description: str | None = None
    price: int
    image_urls: List[str] = Field(default_factory=list)
    stock: int
    category_id: int

class ProductOut(BaseModel):
    id: int
    name: str
    slug: str
    description: str | None = None
    price: int
    image_urls: List[str] = Field(default_factory=list)
    stock: int
    rating: int
    is_active: bool
    category_id: int
    supplier_id: int
    
    class Config:
        from_attributes = True

class CreateCategory(BaseModel):
    name: str

    class Config:
        from_attributes = True


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