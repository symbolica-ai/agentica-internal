# fmt: off

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Annotated, Any, Generic, Literal, TypeVar

import pydantic as pd

__all__ = [
    'Status',
    'Priority',
    'ValidationError',
    'SimpleUser',
    'UserWithDefaults',
    'UserWithOptional',
    'CoercibleTypes',
    'StrictTypes',
    'ConstrainedFields',
    'AnnotatedConstraints',
    'Address',
    'Person',
    'Company',
    'BaseEntity',
    'Product',
    'DigitalProduct',
    'Status',
    'Task',
    'HttpMethod',
    'ValidatedUser',
    'CrossValidatedModel',
    'AliasedFields',
    'SerializationAlias',
    'Container',
    'PaginatedResponse',
    'OrderItem',
    'Order',
    'ImmutableConfig',
    'StrictModel',
    'FlexibleModel',
]

################################################################################

# re-export

ValidationError = pd.ValidationError

################################################################################

# TypeVar for generic models
T = TypeVar("T")

# Enums defined at module level so they can be referenced in defaults
class Status(str, Enum):
    """Status enum for tasks and orders."""
    PENDING = "pending"
    ACTIVE = "active"
    INACTIVE = "inactive"


class Priority(int, Enum):
    """Priority enum for tasks."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3


################################################################################

# -------------------------------------------------------------------------
# Basic Models
# -------------------------------------------------------------------------

class SimpleUser(pd.BaseModel):
    """Minimal model with required fields."""

    name: str
    age: int


class UserWithDefaults(pd.BaseModel):
    """Model with default values."""

    name: str
    age: int = 0
    active: bool = True
    tags: list[str] = pd.Field(default_factory=list)


class UserWithOptional(pd.BaseModel):
    """Model with optional fields."""

    name: str
    nickname: str | None = None
    bio: str | None = None


# -------------------------------------------------------------------------
# Type Coercion Models
# -------------------------------------------------------------------------

class CoercibleTypes(pd.BaseModel):
    """Model demonstrating type coercion."""

    integer: int
    floating: float
    string: str
    boolean: bool


class StrictTypes(pd.BaseModel):
    """Model with strict type checking."""

    model_config = pd.ConfigDict(strict=True)

    integer: int
    string: str


# -------------------------------------------------------------------------
# Constrained Fields
# -------------------------------------------------------------------------

class ConstrainedFields(pd.BaseModel):
    """Model with field constraints."""

    positive_int: int = pd.Field(gt=0)
    bounded_float: float = pd.Field(ge=0.0, le=1.0)
    short_string: str = pd.Field(min_length=1, max_length=10)
    fixed_list: list[int] = pd.Field(min_length=1, max_length=5)


class AnnotatedConstraints(pd.BaseModel):
    """Model using Annotated for constraints."""

    score: Annotated[int, pd.Field(ge=0, le=100)]
    name: Annotated[str, pd.Field(pattern=r"^[A-Z][a-z]+$")]


# -------------------------------------------------------------------------
# Nested Models
# -------------------------------------------------------------------------

class Address(pd.BaseModel):
    """Nested model for address."""

    street: str
    city: str
    postal_code: str
    country: str = "USA"


class Person(pd.BaseModel):
    """Model with nested model field."""

    name: str
    address: "Address"


class Company(pd.BaseModel):
    """Model with list of nested models."""

    name: str
    employees: list["SimpleUser"]
    headquarters: "Address"


# -------------------------------------------------------------------------
# Inheritance Models
# -------------------------------------------------------------------------

class BaseEntity(pd.BaseModel):
    """Base model for inheritance."""

    id: int
    created_at: datetime = pd.Field(default_factory=datetime.now)


class Product(BaseEntity):
    """Inherited model adding product fields."""

    name: str
    price: Decimal
    in_stock: bool = True


class DigitalProduct(Product):
    """Further inherited model for digital products."""

    download_url: str
    file_size_mb: float


# -------------------------------------------------------------------------
# Enum and Literal Models
# -------------------------------------------------------------------------

# Reference module-level enums
Status = Status
Priority = Priority


class Task(pd.BaseModel):
    """Model using enums."""

    title: str
    status: Status
    priority: Priority = Priority.MEDIUM


class HttpMethod(pd.BaseModel):
    """Model using Literal types."""

    method: Literal["GET", "POST", "PUT", "DELETE"]
    path: str


# -------------------------------------------------------------------------
# Validator Models
# -------------------------------------------------------------------------

class ValidatedUser(pd.BaseModel):
    """Model with field validators."""

    username: str
    email: str
    age: int

    @pd.field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        if not v.isalnum():
            raise ValueError("username must be alphanumeric")
        return v.lower()

    @pd.field_validator("age")
    @classmethod
    def age_reasonable(cls, v: int) -> int:
        if not 0 <= v <= 150:
            raise ValueError("age must be between 0 and 150")
        return v


class CrossValidatedModel(pd.BaseModel):
    """Model with model-level validator."""

    password: str
    password_confirm: str

    @pd.model_validator(mode="after")
    def passwords_match(self) -> "CrossValidatedModel":
        if self.password != self.password_confirm:
            raise ValueError("passwords do not match")
        return self


# -------------------------------------------------------------------------
# Alias Models
# -------------------------------------------------------------------------

class AliasedFields(pd.BaseModel):
    """Model with field aliases."""

    model_config = pd.ConfigDict(populate_by_name=True)

    internal_id: int = pd.Field(alias="id")
    user_name: str = pd.Field(alias="userName")
    is_active: bool = pd.Field(alias="isActive", default=True)


class SerializationAlias(pd.BaseModel):
    """Model with serialization aliases."""

    snake_case: str = pd.Field(serialization_alias="snakeCase")
    another_field: int = pd.Field(serialization_alias="anotherField")


# -------------------------------------------------------------------------
# Generic Models
# -------------------------------------------------------------------------

class Container(pd.BaseModel, Generic[T]):
    """Generic container model."""

    value: T
    metadata: dict[str, Any] = pd.Field(default_factory=dict)


class PaginatedResponse(pd.BaseModel, Generic[T]):
    """Generic paginated response."""

    items: list[T]
    total: int
    page: int = 1
    page_size: int = 10


# -------------------------------------------------------------------------
# Complex Nested Models
# -------------------------------------------------------------------------

class OrderItem(pd.BaseModel):
    """Order item model."""

    product_id: int
    quantity: int = pd.Field(gt=0)
    unit_price: Decimal


class Order(BaseEntity):
    """Complex order model with nested items."""

    customer_name: str
    items: list["OrderItem"]
    shipping_address: "Address"
    status: Status = Status.PENDING
    notes: str | None = None

    @property
    def total(self) -> Decimal:
        return sum(item.quantity * item.unit_price for item in self.items)


# -------------------------------------------------------------------------
# Frozen/Immutable Model
# -------------------------------------------------------------------------

class ImmutableConfig(pd.BaseModel):
    """Immutable model (frozen)."""

    model_config = pd.ConfigDict(frozen=True)

    key: str
    value: str


# -------------------------------------------------------------------------
# Extra Fields Handling
# -------------------------------------------------------------------------

class StrictModel(pd.BaseModel):
    """Model that forbids extra fields."""

    model_config = pd.ConfigDict(extra="forbid")

    known_field: str


class FlexibleModel(pd.BaseModel):
    """Model that allows extra fields."""

    model_config = pd.ConfigDict(extra="allow")

    known_field: str
