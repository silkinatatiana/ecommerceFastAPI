from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional


class CreateProduct(BaseModel):
    name: str
    description: Optional[str] = None
    price: int
    stock: int
    category_id: int
    image_urls: Optional[List[str]] = None
    RAM_capacity: Optional[str] = None
    built_in_memory_capacity: Optional[str] = None
    screen: Optional[float] = None
    cpu: Optional[str] = None
    number_of_processor_cores: Optional[int] = None
    number_of_graphics_cores: Optional[int] = None
    color: Optional[str] = None


class ProductOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: int
    image_urls: List[str] = Field(default_factory=list)
    stock: int
    category_id: int
    supplier_id: Optional[int] = None

    RAM_capacity: Optional[str] = None
    built_in_memory_capacity: Optional[str] = None
    screen: Optional[float] = None
    cpu: Optional[str] = None
    number_of_processor_cores: Optional[int] = None
    number_of_graphics_cores: Optional[int] = None
    color: Optional[str] = None

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
    user_id: int
    grade: int = Field(..., ge=1, le=5)
    comment: str = None
    photo_urls: Optional[List[str]] = None


class Favorites(BaseModel):
    id: int
    user_id: int
    product_id: int

    class Config:
        from_attributes = True


class Cart(BaseModel):
    id: int
    user_id: int
    product_id: int
    count: int

    class Config:
        from_attributes = True


class CartItem(BaseModel):
    product_id: int
    count: int = 1


class CartUpdate(BaseModel):
    product_id: int
    add: bool
    count: int = 1


class OrderResponse(BaseModel):
    id: int
    user_id: int
    products: dict
    summa: int
    date: datetime
    status: str

    class Config:
        from_attributes = True


class OrderItem(BaseModel):
    user_id: int
    products_data: dict
    summa: int
