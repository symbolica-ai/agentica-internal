# fmt: off

from types import ModuleType
from agentica_internal.core.asserts import assert_raises

from decimal import Decimal
from typing import TYPE_CHECKING

__all__ = [
    'PYDANTIC_UNIT_TESTS',
    'PYDANTIC_MODELS',
    'load_models'
]
# you have to explicitly

################################################################################

PYDANTIC_UNIT_TESTS = []

def unit(fn):
    PYDANTIC_UNIT_TESTS.append(fn)
    fn.__defaults__ = None
    return fn

################################################################################

if TYPE_CHECKING:
    # this let type checking work against the models argument
    import agentica_internal.testing.examples.models as PYDANTIC_MODELS
else:
    PYDANTIC_MODELS = ModuleType('models')
    PYDANTIC_MODELS.__loaded__ = False

################################################################################

def load_models():
    if PYDANTIC_MODELS.__loaded__: return
    import agentica_internal.testing.examples.models as models
    mod_keys = [
        '__file__', '__name__', '__all__', '__package__', '__spec__', '__builtins__', '__loader__'
    ]
    for key in models.__all__ + mod_keys:
        setattr(PYDANTIC_MODELS, key, getattr(models, key))
    PYDANTIC_MODELS.__loaded__ = True
    return PYDANTIC_MODELS

################################################################################

# =============================================================================
# Basic Validation Tests
# =============================================================================


@unit
def simple_model_valid_construction(models=PYDANTIC_MODELS):
    """Test that a simple model constructs with valid data."""
    SimpleUser = models.SimpleUser

    user = SimpleUser(name="Alice", age=30)

    assert user.name == "Alice"
    assert user.age == 30


@unit
def simple_model_missing_required_field(models=PYDANTIC_MODELS):
    """Test that missing required fields raise ValidationError."""
    SimpleUser = models.SimpleUser
    ValidationError = models.ValidationError

    with assert_raises(ValidationError) as exc_info:
        SimpleUser(name="Alice")  # missing age

    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == ("age",)
    assert errors[0]["type"] == "missing"


@unit
def simple_model_wrong_type(models=PYDANTIC_MODELS):
    """Test that wrong types raise ValidationError."""
    SimpleUser = models.SimpleUser
    ValidationError = models.ValidationError

    with assert_raises(ValidationError) as exc_info:
        SimpleUser(name="Alice", age="not a number")

    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == ("age",)
    assert "int" in errors[0]["type"]


@unit
def defaults_are_applied(models=PYDANTIC_MODELS):
    """Test that default values are properly applied."""
    UserWithDefaults = models.UserWithDefaults

    user = UserWithDefaults(name="Bob")

    assert user.name == "Bob"
    assert user.age == 0
    assert user.active is True
    assert user.tags == []


@unit
def defaults_can_be_overridden(models=PYDANTIC_MODELS):
    """Test that defaults can be overridden."""
    UserWithDefaults = models.UserWithDefaults

    user = UserWithDefaults(name="Bob", age=25, active=False, tags=["admin"])

    assert user.age == 25
    assert user.active is False
    assert user.tags == ["admin"]


@unit
def optional_fields(models=PYDANTIC_MODELS):
    """Test optional field handling."""
    UserWithOptional = models.UserWithOptional

    user = UserWithOptional(name="Carol")

    assert user.name == "Carol"
    assert user.nickname is None
    assert user.bio is None

    user2 = UserWithOptional(name="Carol", nickname="CC", bio="A person")
    assert user2.nickname == "CC"
    assert user2.bio == "A person"


# =============================================================================
# Type Coercion Tests
# =============================================================================


@unit
def type_coercion(models=PYDANTIC_MODELS):
    """Test that Pydantic coerces compatible types."""
    CoercibleTypes = models.CoercibleTypes

    obj = CoercibleTypes(
        integer="42",  # str -> int
        floating="3.14",  # str -> float
        string="hello",  # str stays str
        boolean=1,  # int -> bool
    )

    assert obj.integer == 42
    assert obj.floating == 3.14
    assert obj.string == "hello"
    assert obj.boolean is True


@unit
def type_coercion_bool_values(models=PYDANTIC_MODELS):
    """Test boolean coercion from various values."""
    CoercibleTypes = models.CoercibleTypes

    # Test truthy int
    obj1 = CoercibleTypes(integer=1, floating=1.0, string="s", boolean=1)
    assert obj1.boolean is True

    # Test falsy int
    obj2 = CoercibleTypes(integer=0, floating=0.0, string="s", boolean=0)
    assert obj2.boolean is False


@unit
def strict_mode_rejects_coercion(models=PYDANTIC_MODELS):
    """Test that strict mode rejects type coercion."""
    StrictTypes = models.StrictTypes
    ValidationError = models.ValidationError

    with assert_raises(ValidationError) as exc_info:
        StrictTypes(integer="42", string="hello")

    errors = exc_info.value.errors()
    assert any(e["loc"] == ("integer",) for e in errors)


@unit
def strict_mode_accepts_correct_types(models=PYDANTIC_MODELS):
    """Test that strict mode accepts correct types."""
    StrictTypes = models.StrictTypes

    obj = StrictTypes(integer=42, string="hello")

    assert obj.integer == 42
    assert obj.string == "hello"


# =============================================================================
# Constrained Field Tests
# =============================================================================


@unit
def constrained_fields_valid(models=PYDANTIC_MODELS):
    """Test constrained fields with valid values."""
    ConstrainedFields = models.ConstrainedFields

    obj = ConstrainedFields(
        positive_int=1,
        bounded_float=0.5,
        short_string="hello",
        fixed_list=[1, 2, 3],
    )

    assert obj.positive_int == 1
    assert obj.bounded_float == 0.5
    assert obj.short_string == "hello"
    assert obj.fixed_list == [1, 2, 3]


@unit
def constrained_fields_gt_violation(models=PYDANTIC_MODELS):
    """Test that gt constraint is enforced."""
    ConstrainedFields = models.ConstrainedFields
    ValidationError = models.ValidationError

    with assert_raises(ValidationError) as exc_info:
        ConstrainedFields(
            positive_int=0,  # must be > 0
            bounded_float=0.5,
            short_string="hello",
            fixed_list=[1],
        )

    errors = exc_info.value.errors()
    assert errors[0]["loc"] == ("positive_int",)
    assert errors[0]["type"] == "greater_than"


@unit
def constrained_fields_range_violation(models=PYDANTIC_MODELS):
    """Test that range constraints are enforced."""
    ConstrainedFields = models.ConstrainedFields
    ValidationError = models.ValidationError

    with assert_raises(ValidationError) as exc_info:
        ConstrainedFields(
            positive_int=1,
            bounded_float=1.5,  # must be <= 1.0
            short_string="hello",
            fixed_list=[1],
        )

    errors = exc_info.value.errors()
    assert errors[0]["loc"] == ("bounded_float",)


@unit
def constrained_fields_string_length(models=PYDANTIC_MODELS):
    """Test string length constraints."""
    ConstrainedFields = models.ConstrainedFields
    ValidationError = models.ValidationError

    # Too short
    with assert_raises(ValidationError):
        ConstrainedFields(
            positive_int=1, bounded_float=0.5, short_string="", fixed_list=[1]
        )

    # Too long
    with assert_raises(ValidationError):
        ConstrainedFields(
            positive_int=1,
            bounded_float=0.5,
            short_string="this is way too long",
            fixed_list=[1],
        )


@unit
def constrained_fields_list_length(models=PYDANTIC_MODELS):
    """Test list length constraints."""
    ConstrainedFields = models.ConstrainedFields
    ValidationError = models.ValidationError

    # Too short (empty)
    with assert_raises(ValidationError):
        ConstrainedFields(
            positive_int=1, bounded_float=0.5, short_string="hi", fixed_list=[]
        )

    # Too long
    with assert_raises(ValidationError):
        ConstrainedFields(
            positive_int=1,
            bounded_float=0.5,
            short_string="hi",
            fixed_list=[1, 2, 3, 4, 5, 6],
        )


@unit
def annotated_constraints_valid(models=PYDANTIC_MODELS):
    """Test Annotated-style constraints with valid values."""
    AnnotatedConstraints = models.AnnotatedConstraints

    obj = AnnotatedConstraints(score=85, name="Alice")

    assert obj.score == 85
    assert obj.name == "Alice"


@unit
def annotated_constraints_invalid(models=PYDANTIC_MODELS):
    """Test Annotated-style constraints with invalid values."""
    AnnotatedConstraints = models.AnnotatedConstraints
    ValidationError = models.ValidationError

    # Score out of range
    with assert_raises(ValidationError):
        AnnotatedConstraints(score=101, name="Alice")

    # Name doesn't match pattern
    with assert_raises(ValidationError):
        AnnotatedConstraints(score=50, name="alice")  # must start with uppercase


# =============================================================================
# Nested Model Tests
# =============================================================================


@unit
def nested_model_construction(models=PYDANTIC_MODELS):
    """Test nested model construction."""
    Person = models.Person
    Address = models.Address

    person = Person(
        name="Alice",
        address=Address(street="123 Main St", city="Boston", postal_code="02101"),
    )

    assert person.name == "Alice"
    assert person.address.street == "123 Main St"
    assert person.address.city == "Boston"
    assert person.address.country == "USA"  # default


@unit
def nested_model_from_dict(models=PYDANTIC_MODELS):
    """Test nested model construction from dict."""
    Person = models.Person

    person = Person(
        name="Bob",
        address={"street": "456 Oak Ave", "city": "Seattle", "postal_code": "98101"},
    )

    assert person.name == "Bob"
    assert person.address.street == "456 Oak Ave"


@unit
def nested_model_validation_error(models=PYDANTIC_MODELS):
    """Test that nested model validation errors propagate."""
    Person = models.Person
    ValidationError = models.ValidationError

    with assert_raises(ValidationError) as exc_info:
        Person(
            name="Carol",
            address={"street": "789 Pine Rd", "city": "Portland"},  # missing postal_code
        )

    errors = exc_info.value.errors()
    assert errors[0]["loc"] == ("address", "postal_code")


@unit
def list_of_nested_models(models=PYDANTIC_MODELS):
    """Test list of nested models."""
    Company = models.Company
    ValidationError = models.ValidationError

    company = Company(
        name="TechCorp",
        employees=[
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
        ],
        headquarters={
            "street": "1 Tech Way",
            "city": "San Francisco",
            "postal_code": "94105",
        },
    )

    assert company.name == "TechCorp"
    assert len(company.employees) == 2
    assert company.employees[0].name == "Alice"
    assert company.headquarters.city == "San Francisco"


# =============================================================================
# Inheritance Tests
# =============================================================================


@unit
def inherited_model(models=PYDANTIC_MODELS):
    """Test basic model inheritance."""
    Product = models.Product
    product = Product(id=1, name="Widget", price=Decimal("9.99"))
    assert product.id == 1
    assert product.name == "Widget"
    assert product.price == Decimal("9.99")
    assert product.in_stock is True
    assert product.created_at is not None


@unit
def deep_inheritance(models=PYDANTIC_MODELS):
    """Test multi-level inheritance."""
    DigitalProduct = models.DigitalProduct

    product = DigitalProduct(
        id=1,
        name="E-Book",
        price=Decimal("14.99"),
        download_url="https://example.com/book.pdf",
        file_size_mb=5.2,
    )

    assert product.id == 1
    assert product.name == "E-Book"
    assert product.download_url == "https://example.com/book.pdf"
    assert product.created_at is not None


@unit
def inherited_model_missing_parent_field(models=PYDANTIC_MODELS):
    """Test that parent fields are required in inherited models."""
    Product = models.Product
    ValidationError = models.ValidationError

    with assert_raises(ValidationError) as exc_info:
        Product(name="Widget", price=Decimal("9.99"))  # missing id

    errors = exc_info.value.errors()
    assert any(e["loc"] == ("id",) for e in errors)


# =============================================================================
# Enum and Literal Tests
# =============================================================================


@unit
def enum_fields(models=PYDANTIC_MODELS):
    """Test enum field handling."""
    Task = models.Task
    Status = models.Status
    Priority = models.Priority

    task = Task(title="Fix bug", status=Status.ACTIVE, priority=Priority.HIGH)

    assert task.status == Status.ACTIVE
    assert task.priority == Priority.HIGH


@unit
def enum_from_value(models=PYDANTIC_MODELS):
    """Test enum construction from raw value."""
    Task = models.Task
    Status = models.Status

    task = Task(title="Review PR", status="pending")

    assert task.status == Status.PENDING


@unit
def enum_invalid_value(models=PYDANTIC_MODELS):
    """Test that invalid enum values are rejected."""
    Task = models.Task
    ValidationError = models.ValidationError

    with assert_raises(ValidationError) as exc_info:
        Task(title="Task", status="invalid_status")

    errors = exc_info.value.errors()
    assert errors[0]["loc"] == ("status",)


@unit
def literal_fields(models=PYDANTIC_MODELS):
    """Test Literal type handling."""
    HttpMethod = models.HttpMethod

    method = HttpMethod(method="GET", path="/api/users")

    assert method.method == "GET"


@unit
def literal_invalid_value(models=PYDANTIC_MODELS):
    """Test that invalid Literal values are rejected."""
    HttpMethod = models.HttpMethod
    ValidationError = models.ValidationError

    with assert_raises(ValidationError):
        HttpMethod(method="PATCH", path="/api/users")  # PATCH not in Literal


# =============================================================================
# Validator Tests
# =============================================================================


@unit
def field_validator_transforms(models=PYDANTIC_MODELS):
    """Test that field validators can transform values."""
    ValidatedUser = models.ValidatedUser

    user = ValidatedUser(username="ALICE123", email="alice@example.com", age=30)

    assert user.username == "alice123"  # lowercased by validator


@unit
def field_validator_rejects_invalid(models=PYDANTIC_MODELS):
    """Test that field validators reject invalid values."""
    ValidatedUser = models.ValidatedUser
    ValidationError = models.ValidationError

    with assert_raises(ValidationError) as exc_info:
        ValidatedUser(
            username="alice@123",  # not alphanumeric
            email="alice@example.com",
            age=30,
        )

    errors = exc_info.value.errors()
    assert errors[0]["loc"] == ("username",)
    assert "alphanumeric" in str(errors[0]["msg"])


@unit
def field_validator_age_bounds(models=PYDANTIC_MODELS):
    """Test age validator bounds."""
    ValidatedUser = models.ValidatedUser
    ValidationError = models.ValidationError

    with assert_raises(ValidationError):
        ValidatedUser(username="alice", email="alice@example.com", age=-1)

    with assert_raises(ValidationError):
        ValidatedUser(username="alice", email="alice@example.com", age=200)


@unit
def model_validator(models=PYDANTIC_MODELS):
    """Test model-level validator."""
    CrossValidatedModel = models.CrossValidatedModel
    ValidationError = models.ValidationError

    # Valid: passwords match
    obj = CrossValidatedModel(password="secret123", password_confirm="secret123")
    assert obj.password == "secret123"

    # Invalid: passwords don't match
    with assert_raises(ValidationError) as exc_info:
        CrossValidatedModel(password="secret123", password_confirm="different")

    assert "passwords do not match" in str(exc_info.value)


# =============================================================================
# Alias Tests
# =============================================================================


@unit
def field_alias_construction(models=PYDANTIC_MODELS):
    """Test construction with field aliases."""
    AliasedFields = models.AliasedFields

    # Using aliases
    obj = AliasedFields(id=1, userName="alice", isActive=False)

    assert obj.internal_id == 1
    assert obj.user_name == "alice"
    assert obj.is_active is False


@unit
def field_alias_by_field_name(models=PYDANTIC_MODELS):
    """Test construction with field names (populate_by_name=True)."""
    AliasedFields = models.AliasedFields

    obj = AliasedFields(internal_id=2, user_name="bob")

    assert obj.internal_id == 2
    assert obj.user_name == "bob"


@unit
def serialization_alias(models=PYDANTIC_MODELS):
    """Test serialization with aliases."""
    SerializationAlias = models.SerializationAlias

    obj = SerializationAlias(snake_case="hello", another_field=42)

    # Regular dump uses field names
    data = obj.model_dump()
    assert "snake_case" in data

    # Dump with by_alias uses serialization aliases
    data_aliased = obj.model_dump(by_alias=True)
    assert "snakeCase" in data_aliased
    assert "anotherField" in data_aliased


# =============================================================================
# Serialization Tests
# =============================================================================


@unit
def model_dump_basic(models=PYDANTIC_MODELS):
    """Test basic model_dump functionality."""
    SimpleUser = models.SimpleUser

    user = SimpleUser(name="Alice", age=30)
    data = user.model_dump()

    assert data == {"name": "Alice", "age": 30}


@unit
def model_dump_exclude_unset(models=PYDANTIC_MODELS):
    """Test model_dump with exclude_unset."""
    UserWithDefaults = models.UserWithDefaults

    user = UserWithDefaults(name="Bob")
    data = user.model_dump(exclude_unset=True)

    assert data == {"name": "Bob"}
    assert "age" not in data
    assert "active" not in data


@unit
def model_dump_exclude_defaults(models=PYDANTIC_MODELS):
    """Test model_dump with exclude_defaults."""
    UserWithDefaults = models.UserWithDefaults

    user = UserWithDefaults(name="Carol", age=0, active=True)  # matches defaults
    data = user.model_dump(exclude_defaults=True)

    assert data == {"name": "Carol"}


@unit
def model_dump_exclude_none(models=PYDANTIC_MODELS):
    """Test model_dump with exclude_none."""
    UserWithOptional = models.UserWithOptional

    user = UserWithOptional(name="Dave", nickname="D")
    data = user.model_dump(exclude_none=True)

    assert data == {"name": "Dave", "nickname": "D"}
    assert "bio" not in data


@unit
def model_dump_include_exclude(models=PYDANTIC_MODELS):
    """Test model_dump with include and exclude."""
    SimpleUser = models.SimpleUser

    user = SimpleUser(name="Eve", age=25)

    # Include only specific fields
    data = user.model_dump(include={"name"})
    assert data == {"name": "Eve"}

    # Exclude specific fields
    data = user.model_dump(exclude={"age"})
    assert data == {"name": "Eve"}


@unit
def model_dump_nested(models=PYDANTIC_MODELS):
    """Test model_dump with nested models."""
    Person = models.Person

    person = Person(
        name="Frank",
        address={"street": "1 Main St", "city": "NYC", "postal_code": "10001"},
    )

    data = person.model_dump()

    assert data == {
        "name": "Frank",
        "address": {
            "street": "1 Main St",
            "city": "NYC",
            "postal_code": "10001",
            "country": "USA",
        },
    }


@unit
def model_dump_json(models=PYDANTIC_MODELS):
    """Test model_dump_json functionality."""
    import json

    SimpleUser = models.SimpleUser

    user = SimpleUser(name="Grace", age=28)
    json_str = user.model_dump_json()

    parsed = json.loads(json_str)
    assert parsed == {"name": "Grace", "age": 28}


@unit
def model_dump_json_with_options(models=PYDANTIC_MODELS):
    """Test model_dump_json with options."""
    import json

    UserWithDefaults = models.UserWithDefaults

    user = UserWithDefaults(name="Henry")
    json_str = user.model_dump_json(exclude_unset=True)

    parsed = json.loads(json_str)
    assert parsed == {"name": "Henry"}


# =============================================================================
# Parsing Tests
# =============================================================================


@unit
def model_validate(models=PYDANTIC_MODELS):
    """Test model_validate class method."""
    SimpleUser = models.SimpleUser

    data = {"name": "Ivy", "age": 22}
    user = SimpleUser.model_validate(data)

    assert user.name == "Ivy"
    assert user.age == 22


@unit
def model_validate_json(models=PYDANTIC_MODELS):
    """Test model_validate_json class method."""
    SimpleUser = models.SimpleUser

    json_str = '{"name": "Jack", "age": 35}'
    user = SimpleUser.model_validate_json(json_str)

    assert user.name == "Jack"
    assert user.age == 35


@unit
def model_validate_invalid(models=PYDANTIC_MODELS):
    """Test model_validate with invalid data."""
    SimpleUser = models.SimpleUser
    ValidationError = models.ValidationError

    with assert_raises(ValidationError):
        SimpleUser.model_validate({"name": "Kim"})  # missing age


@unit
def model_validate_json_invalid(models=PYDANTIC_MODELS):
    """Test model_validate_json with invalid JSON."""
    SimpleUser = models.SimpleUser
    ValidationError = models.ValidationError

    with assert_raises(ValidationError):
        SimpleUser.model_validate_json("not valid json")


# =============================================================================
# Schema Tests
# =============================================================================


@unit
def model_json_schema_basic(models=PYDANTIC_MODELS):
    """Test basic JSON schema generation."""
    SimpleUser = models.SimpleUser

    schema = SimpleUser.model_json_schema()

    assert schema["type"] == "object"
    assert "name" in schema["properties"]
    assert "age" in schema["properties"]
    assert schema["properties"]["name"]["type"] == "string"
    assert schema["properties"]["age"]["type"] == "integer"
    assert set(schema["required"]) == {"name", "age"}


@unit
def model_json_schema_with_defaults(models=PYDANTIC_MODELS):
    """Test JSON schema includes default values."""
    UserWithDefaults = models.UserWithDefaults

    schema = UserWithDefaults.model_json_schema()

    assert schema["properties"]["age"]["default"] == 0
    assert schema["properties"]["active"]["default"] is True
    assert schema["required"] == ["name"]


@unit
def model_json_schema_with_constraints(models=PYDANTIC_MODELS):
    """Test JSON schema includes constraints."""
    ConstrainedFields = models.ConstrainedFields

    schema = ConstrainedFields.model_json_schema()

    assert schema["properties"]["positive_int"]["exclusiveMinimum"] == 0
    assert schema["properties"]["bounded_float"]["minimum"] == 0.0
    assert schema["properties"]["bounded_float"]["maximum"] == 1.0
    assert schema["properties"]["short_string"]["minLength"] == 1
    assert schema["properties"]["short_string"]["maxLength"] == 10


@unit
def model_json_schema_nested(models=PYDANTIC_MODELS):
    """Test JSON schema for nested models."""
    Person = models.Person

    schema = Person.model_json_schema()

    # Should have $defs for nested Address model
    assert "$defs" in schema
    assert "Address" in schema["$defs"]


@unit
def model_json_schema_enum(models=PYDANTIC_MODELS):
    """Test JSON schema for enum fields."""
    Task = models.Task

    schema = Task.model_json_schema()

    # Status enum should be referenced
    assert "$defs" in schema
    assert "Status" in schema["$defs"]
    assert schema["$defs"]["Status"]["enum"] == ["pending", "active", "inactive"]


# =============================================================================
# Configuration Tests
# =============================================================================


@unit
def frozen_model(models=PYDANTIC_MODELS):
    """Test that frozen models are immutable."""
    ImmutableConfig = models.ImmutableConfig
    ValidationError = models.ValidationError

    config = ImmutableConfig(key="api_key", value="secret123")

    with assert_raises(ValidationError):
        config.key = "new_key"


@unit
def extra_forbid(models=PYDANTIC_MODELS):
    """Test that extra='forbid' rejects unknown fields."""
    StrictModel = models.StrictModel
    ValidationError = models.ValidationError

    with assert_raises(ValidationError) as exc_info:
        StrictModel(known_field="hello", unknown_field="world")

    errors = exc_info.value.errors()
    assert errors[0]["type"] == "extra_forbidden"


@unit
def extra_allow(models=PYDANTIC_MODELS):
    """Test that extra='allow' accepts unknown fields."""
    FlexibleModel = models.FlexibleModel
    ValidationError = models.ValidationError

    obj = FlexibleModel(known_field="hello", custom="world", another=123)

    assert obj.known_field == "hello"
    assert obj.custom == "world"
    assert obj.another == 123


# =============================================================================
# Generic Model Tests
# =============================================================================


@unit
def generic_model_string(models=PYDANTIC_MODELS):
    """Test generic model with string type."""
    Container = models.Container

    StringContainer = Container[str]
    assert StringContainer.__name__ == "Container[str]"

    container = StringContainer(value="hello")

    assert container.value == "hello"


@unit
def generic_model_int(models=PYDANTIC_MODELS):
    """Test generic model with int type."""
    Container = models.Container

    IntContainer = Container[int]
    container = IntContainer(value=42)

    assert container.value == 42


@unit
def generic_model_validation(models=PYDANTIC_MODELS):
    """Test generic model type validation."""
    Container = models.Container
    ValidationError = models.ValidationError

    IntContainer = Container[int]

    with assert_raises(ValidationError):
        IntContainer(value="not an int")


@unit
def generic_paginated_response(models=PYDANTIC_MODELS):
    """Test generic paginated response model."""
    PaginatedResponse = models.PaginatedResponse
    SimpleUser = models.SimpleUser

    UserPage = PaginatedResponse[SimpleUser]

    page = UserPage(
        items=[
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
        ],
        total=100,
        page=1,
        page_size=2,
    )

    assert len(page.items) == 2
    assert page.items[0].name == "Alice"
    assert page.total == 100


# =============================================================================
# Complex Model Tests
# =============================================================================


@unit
def complex_order_model(models=PYDANTIC_MODELS):
    """Test complex order model with all features."""
    Order = models.Order
    Status = models.Status

    order = Order(
        id=1001,
        customer_name="John Doe",
        items=[
            {"product_id": 1, "quantity": 2, "unit_price": Decimal("10.00")},
            {"product_id": 2, "quantity": 1, "unit_price": Decimal("25.00")},
        ],
        shipping_address={
            "street": "123 Delivery St",
            "city": "Portland",
            "postal_code": "97201",
        },
        status="active",
        notes="Handle with care",
    )

    assert order.id == 1001
    assert len(order.items) == 2
    assert order.status == Status.ACTIVE
    assert order.total == Decimal("45.00")
    assert order.shipping_address.country == "USA"
    assert order.created_at is not None


@unit
def complex_order_model_dump(models=PYDANTIC_MODELS):
    """Test complex order model serialization."""
    Order = models.Order

    order = Order(
        id=1002,
        customer_name="Jane Smith",
        items=[{"product_id": 3, "quantity": 1, "unit_price": Decimal("50.00")}],
        shipping_address={
            "street": "456 Ship Ln",
            "city": "Seattle",
            "postal_code": "98101",
        },
    )

    data = order.model_dump(exclude_unset=True, exclude={"created_at"})

    assert data["id"] == 1002
    assert data["customer_name"] == "Jane Smith"
    assert len(data["items"]) == 1
    # status is not in data because exclude_unset=True and we didn't set it
    assert "status" not in data
    assert "notes" not in data  # excluded because not set

    # Without exclude_unset, status should be present
    data_full = order.model_dump(exclude={"created_at"}, mode="json")
    assert order.status == models.Status.PENDING
    assert data_full["status"] == "pending"


@unit
def complex_order_json_roundtrip(models=PYDANTIC_MODELS):
    """Test complex order JSON serialization roundtrip."""
    import json

    Order = models.Order

    order = Order(
        id=1003,
        customer_name="Test User",
        items=[{"product_id": 1, "quantity": 3, "unit_price": Decimal("15.00")}],
        shipping_address={
            "street": "789 Test Blvd",
            "city": "Austin",
            "postal_code": "78701",
        },
    )

    # Serialize
    json_str = order.model_dump_json(exclude={"created_at"})

    # Deserialize
    parsed = json.loads(json_str)
    order2 = Order.model_validate(parsed)

    assert order2.id == order.id
    assert order2.customer_name == order.customer_name
    assert len(order2.items) == len(order.items)


# =============================================================================
# Error Details Tests
# =============================================================================


@unit
def validation_error_details(models=PYDANTIC_MODELS):
    """Test validation error provides detailed information."""
    SimpleUser = models.SimpleUser
    ValidationError = models.ValidationError

    with assert_raises(ValidationError) as exc_info:
        SimpleUser(name=123, age="invalid")

    errors = exc_info.value.errors()

    assert len(errors) == 2

    # Check error structure
    for error in errors:
        assert "loc" in error
        assert "msg" in error
        assert "type" in error


@unit
def nested_validation_error_location(models=PYDANTIC_MODELS):
    """Test nested validation errors show correct location."""
    Company = models.Company
    ValidationError = models.ValidationError

    with assert_raises(ValidationError) as exc_info:
        Company(
            name="Corp",
            employees=[
                {"name": "Alice", "age": 30},
                {"name": "Bob"},  # missing age
            ],
            headquarters={"street": "1 Main", "city": "NYC", "postal_code": "10001"},
        )

    errors = exc_info.value.errors()

    # Should point to employees[1].age
    assert errors[0]["loc"] == ("employees", 1, "age")


@unit
def multiple_validation_errors(models=PYDANTIC_MODELS):
    """Test that multiple validation errors are collected."""
    ConstrainedFields = models.ConstrainedFields
    ValidationError = models.ValidationError

    with assert_raises(ValidationError) as exc_info:
        ConstrainedFields(
            positive_int=-1,  # invalid
            bounded_float=2.0,  # invalid
            short_string="",  # invalid
            fixed_list=[],  # invalid
        )

    errors = exc_info.value.errors()
    assert len(errors) == 4


# =============================================================================
# Model Copying Tests
# =============================================================================


@unit
def model_copy(models=PYDANTIC_MODELS):
    """Test model copying."""
    SimpleUser = models.SimpleUser

    user1 = SimpleUser(name="Alice", age=30)
    user2 = user1.model_copy()

    assert user2.name == "Alice"
    assert user2.age == 30
    assert user1 is not user2


@unit
def model_copy_update(models=PYDANTIC_MODELS):
    """Test model copying with updates."""
    SimpleUser = models.SimpleUser

    user1 = SimpleUser(name="Alice", age=30)
    user2 = user1.model_copy(update={"age": 31})

    assert user1.age == 30
    assert user2.age == 31
    assert user2.name == "Alice"


@unit
def model_copy_deep(models=PYDANTIC_MODELS):
    """Test deep model copying."""
    Person = models.Person

    person1 = Person(
        name="Bob",
        address={"street": "1 Main", "city": "NYC", "postal_code": "10001"},
    )

    person2 = person1.model_copy(deep=True)

    # Modifying nested object shouldn't affect original
    assert person1 is not person2
    assert person1.address is not person2.address
