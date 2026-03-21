from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CreateProduct(BaseModel):
    name: str
    description: str | None = None
    price: int
    stock: int
    category_id: int
    RAM_capacity: str | None = None
    built_in_memory_capacity: str | None = None
    screen: float | None = None
    cpu: str | None = None
    number_of_processor_cores: int | None = None
    number_of_graphics_cores: int | None = None
    color: str | None = None


class UpdateProduct(BaseModel):
    name: str | None = None
    description: str | None = None
    price: int | None = None
    stock: int | None = None
    category_id: int | None = None
    RAM_capacity: str | None = None
    built_in_memory_capacity: str | None = None
    screen: float | None = None
    cpu: str | None = None
    number_of_processor_cores: int | None = None
    number_of_graphics_cores: int | None = None
    color: str | None = None


class FileOut(BaseModel):
    id: int
    original_filename: str
    file_url: str
    file_size: int
    content_type: str

    model_config = ConfigDict(from_attributes=True)


class ProductOut(BaseModel):
    id: int
    name: str
    description: str | None = None
    price: int
    image_urls: list[str] = Field(default_factory=list)  # из product.files
    stock: int
    category_id: int
    supplier_id: int | None = None

    RAM_capacity: str | None = None
    built_in_memory_capacity: str | None = None
    screen: float | None = None
    cpu: str | None = None
    number_of_processor_cores: int | None = None
    number_of_graphics_cores: int | None = None
    color: str | None = None

    model_config = ConfigDict(from_attributes=True)


class CreateCategory(BaseModel):
    name: str

    model_config = ConfigDict(from_attributes=True)


class CreateUser(BaseModel):
    first_name: str
    last_name: str
    username: str
    email: str
    password: str


class CreateReviews(BaseModel):
    grade: int = Field(..., ge=1, le=5)
    comment: str = None
    photo_urls: list[str] | None = None


class Favorites(BaseModel):
    id: int
    user_id: int
    product_id: int

    model_config = ConfigDict(from_attributes=True)


class Cart(BaseModel):
    id: int
    user_id: int
    product_id: int
    count: int

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


class OrderItem(BaseModel):
    user_id: int
    products_data: dict
    summa: int


class ProfileUpdate(BaseModel):
    first_name: str
    last_name: str
    email: str


class PasswordUpdate(BaseModel):
    old_password: str = Field(..., min_length=3)
    new_password: str = Field(..., min_length=3)
    new_password_one_more_time: str = Field(..., min_length=3)


class ChatCreate(BaseModel):
    topic: str


class MessageCreate(BaseModel):
    message: str
    chat_id: int


class ChangeOrderStatus(BaseModel):
    new_status: str


class RegisterData(BaseModel):
    first_name: str
    last_name: str
    username: str
    email: str
    telegram: str
    password: str
    confirm_password: str
    role: str


class LoginData(BaseModel):
    username: str
    password: str


class RecommendOut(BaseModel):
    ids: list[int]
