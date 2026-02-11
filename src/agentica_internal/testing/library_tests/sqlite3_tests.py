# fmt: off

from .. import assert_raises
from types import ModuleType

__all__ = [
    'SQLITE3_UNIT_TESTS',
]

################################################################################

SQLITE3_UNIT_TESTS = []

def unit(fn):
    SQLITE3_UNIT_TESTS.append(fn)
    return fn

################################################################################

@unit
def connection_and_cursor_basics(sq: ModuleType):
    """Test basic connection creation, cursor operations, and context managers."""
    # In-memory database connection
    conn = sq.connect(":memory:")
    assert conn is not None

    # Cursor creation
    cursor = conn.cursor()
    assert cursor is not None

    # Execute returns the cursor itself (for chaining)
    result = cursor.execute("SELECT 1")
    assert result is cursor

    # Fetch single result
    row = cursor.fetchone()
    assert row == (1,)

    # Fetchone returns None when exhausted
    assert cursor.fetchone() is None

    # Multiple values in SELECT
    cursor.execute("SELECT 1, 2, 3")
    assert cursor.fetchone() == (1, 2, 3)

    # fetchall returns list of tuples
    cursor.execute("SELECT 1 UNION SELECT 2 UNION SELECT 3 ORDER BY 1")
    rows = cursor.fetchall()
    assert rows == [(1,), (2,), (3,)]

    # fetchall on exhausted cursor returns empty list
    assert cursor.fetchall() == []

    # fetchmany with size
    cursor.execute("SELECT 1 UNION SELECT 2 UNION SELECT 3 ORDER BY 1")
    assert cursor.fetchmany(2) == [(1,), (2,)]
    assert cursor.fetchmany(2) == [(3,)]
    assert cursor.fetchmany(2) == []

    # Connection as context manager
    with sq.connect(":memory:") as ctx_conn:
        ctx_conn.execute("SELECT 1")
    # Connection should still be usable after context exit (commit happened)
    # but we just verify the context manager works

    # Cursor close
    cursor.close()
    conn.close()


@unit
def table_creation_and_crud(sq: ModuleType):
    """Test DDL operations and basic CRUD functionality."""
    conn = sq.connect(":memory:")
    cursor = conn.cursor()

    # CREATE TABLE
    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            age INTEGER
        )
    """)

    # INSERT with positional parameters (?)
    cursor.execute(
        "INSERT INTO users (name, email, age) VALUES (?, ?, ?)",
        ("Alice", "alice@example.com", 30)
    )
    assert cursor.rowcount == 1
    assert cursor.lastrowid == 1

    # INSERT with named parameters (:name)
    cursor.execute(
        "INSERT INTO users (name, email, age) VALUES (:name, :email, :age)",
        {"name": "Bob", "email": "bob@example.com", "age": 25}
    )
    assert cursor.lastrowid == 2

    # SELECT with WHERE
    cursor.execute("SELECT name, age FROM users WHERE age > ?", (20,))
    rows = cursor.fetchall()
    assert len(rows) == 2
    assert ("Alice", 30) in rows
    assert ("Bob", 25) in rows

    # UPDATE
    cursor.execute("UPDATE users SET age = ? WHERE name = ?", (31, "Alice"))
    assert cursor.rowcount == 1

    cursor.execute("SELECT age FROM users WHERE name = ?", ("Alice",))
    assert cursor.fetchone() == (31,)

    # DELETE
    cursor.execute("DELETE FROM users WHERE name = ?", ("Bob",))
    assert cursor.rowcount == 1

    cursor.execute("SELECT COUNT(*) FROM users")
    assert cursor.fetchone() == (1,)

    # INSERT with NULL
    cursor.execute("INSERT INTO users (name, email, age) VALUES (?, ?, ?)",
        ("Charlie", None, None))
    cursor.execute("SELECT email, age FROM users WHERE name = ?", ("Charlie",))
    assert cursor.fetchone() == (None, None)

    conn.close()


@unit
def transactions_and_isolation(sq: ModuleType):
    """Test transaction handling, commit, rollback, and isolation levels."""
    conn = sq.connect(":memory:")
    cursor = conn.cursor()

    cursor.execute("CREATE TABLE accounts (id INTEGER PRIMARY KEY, balance INTEGER)")
    cursor.execute("INSERT INTO accounts (balance) VALUES (100)")
    conn.commit()

    # Changes visible after commit
    cursor.execute("SELECT balance FROM accounts WHERE id = 1")
    assert cursor.fetchone() == (100,)

    # Rollback undoes uncommitted changes
    cursor.execute("UPDATE accounts SET balance = 200 WHERE id = 1")
    cursor.execute("SELECT balance FROM accounts WHERE id = 1")
    assert cursor.fetchone() == (200,)  # Visible within same connection

    conn.rollback()
    cursor.execute("SELECT balance FROM accounts WHERE id = 1")
    assert cursor.fetchone() == (100,)  # Rolled back to committed state

    # isolation_level attribute exists
    assert hasattr(conn, 'isolation_level')

    # Test autocommit mode (isolation_level = None)
    conn.isolation_level = None
    cursor.execute("UPDATE accounts SET balance = 150 WHERE id = 1")
    # In autocommit, changes are immediately committed

    conn.isolation_level = ""  # Back to default
    cursor.execute("SELECT balance FROM accounts WHERE id = 1")
    assert cursor.fetchone() == (150,)

    conn.close()


@unit
def executemany_and_executescript(sq: ModuleType):
    """Test batch operations: executemany and executescript."""
    conn = sq.connect(":memory:")
    cursor = conn.cursor()

    cursor.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, value TEXT)")

    # executemany with list of tuples
    data = [("a",), ("b",), ("c",), ("d",)]
    cursor.executemany("INSERT INTO items (value) VALUES (?)", data)
    assert cursor.rowcount == 4

    cursor.execute("SELECT COUNT(*) FROM items")
    assert cursor.fetchone() == (4,)

    # executemany with generator
    def gen():
        for i in range(3):
            yield (f"gen_{i}",)

    cursor.executemany("INSERT INTO items (value) VALUES (?)", gen())

    cursor.execute("SELECT COUNT(*) FROM items")
    assert cursor.fetchone() == (7,)

    # executescript runs multiple statements
    conn2 = sq.connect(":memory:")
    conn2.executescript("""
        CREATE TABLE t1 (x INTEGER);
        INSERT INTO t1 VALUES (1);
        INSERT INTO t1 VALUES (2);
        CREATE TABLE t2 (y TEXT);
        INSERT INTO t2 VALUES ('hello');
    """)

    cur2 = conn2.cursor()
    cur2.execute("SELECT * FROM t1 ORDER BY x")
    assert cur2.fetchall() == [(1,), (2,)]

    cur2.execute("SELECT * FROM t2")
    assert cur2.fetchone() == ("hello",)

    conn.close()
    conn2.close()


@unit
def row_factory_and_description(sq: ModuleType):
    """Test row_factory, cursor.description, and Row objects."""
    conn = sq.connect(":memory:")
    cursor = conn.cursor()

    cursor.execute("CREATE TABLE products (id INTEGER, name TEXT, price REAL)")
    cursor.execute("INSERT INTO products VALUES (1, 'Widget', 9.99)")

    # cursor.description after SELECT
    cursor.execute("SELECT id, name, price FROM products")
    desc = cursor.description
    assert desc is not None
    assert len(desc) == 3

    # Each description item is a 7-tuple (name, type_code, ...)
    # At minimum, name should be accessible
    assert desc[0][0].lower() == "id"
    assert desc[1][0].lower() == "name"
    assert desc[2][0].lower() == "price"

    # Default row factory returns tuples
    row = cursor.fetchone()
    assert row == (1, "Widget", 9.99)
    assert isinstance(row, tuple)

    # sqlite3.Row factory
    conn.row_factory = sq.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price FROM products")
    row = cursor.fetchone()

    # Row supports index access
    assert row[0] == 1
    assert row[1] == "Widget"
    assert row[2] == 9.99

    # Row supports column name access (case-insensitive)
    assert row["id"] == 1
    assert row["name"] == "Widget"
    assert row["price"] == 9.99
    assert row["ID"] == 1  # Case insensitive

    # Row has keys() method
    keys = row.keys()
    assert "id" in [k.lower() for k in keys]
    assert "name" in [k.lower() for k in keys]

    conn.close()


@unit
def type_handling_and_adapters(sq: ModuleType):
    """Test SQLite type affinity and Python type conversions."""
    conn = sq.connect(":memory:")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE types_test (
            int_col INTEGER,
            real_col REAL,
            text_col TEXT,
            blob_col BLOB,
            null_col TEXT
        )
    """)

    # Insert various Python types
    cursor.execute(
        "INSERT INTO types_test VALUES (?, ?, ?, ?, ?)",
        (42, 3.14159, "hello", b"\x00\x01\x02\xff", None)
    )

    cursor.execute("SELECT * FROM types_test")
    row = cursor.fetchone()

    # Type conversions
    assert row[0] == 42 and isinstance(row[0], int)
    assert abs(row[1] - 3.14159) < 0.0001 and isinstance(row[1], float)
    assert row[2] == "hello" and isinstance(row[2], str)
    assert row[3] == b"\x00\x01\x02\xff" and isinstance(row[3], bytes)
    assert row[4] is None

    # Boolean handling (stored as INTEGER 0/1)
    cursor.execute("INSERT INTO types_test (int_col) VALUES (?)", (True,))
    cursor.execute("INSERT INTO types_test (int_col) VALUES (?)", (False,))
    cursor.execute("SELECT int_col FROM types_test WHERE int_col IS NOT NULL ORDER BY rowid DESC LIMIT 2")
    rows = cursor.fetchall()
    assert rows[0][0] == 0  # False -> 0
    assert rows[1][0] == 1  # True -> 1

    # Large integers
    big_int = 2 ** 62
    cursor.execute("INSERT INTO types_test (int_col) VALUES (?)", (big_int,))
    cursor.execute("SELECT int_col FROM types_test ORDER BY rowid DESC LIMIT 1")
    assert cursor.fetchone()[0] == big_int

    conn.close()


@unit
def exceptions_and_error_handling(sq: ModuleType):
    """Test that appropriate exceptions are raised for various error conditions."""
    conn = sq.connect(":memory:")
    cursor = conn.cursor()

    # Module-level exception hierarchy
    assert issubclass(sq.Warning, Exception)
    assert issubclass(sq.Error, Exception)
    assert issubclass(sq.InterfaceError, sq.Error)
    assert issubclass(sq.DatabaseError, sq.Error)
    assert issubclass(sq.DataError, sq.DatabaseError)
    assert issubclass(sq.OperationalError, sq.DatabaseError)
    assert issubclass(sq.IntegrityError, sq.DatabaseError)
    assert issubclass(sq.InternalError, sq.DatabaseError)
    assert issubclass(sq.ProgrammingError, sq.DatabaseError)
    assert issubclass(sq.NotSupportedError, sq.DatabaseError)

    # Syntax error raises OperationalError
    with assert_raises(sq.OperationalError):
        cursor.execute("SELEKT * FORM table")

    # Table doesn't exist
    with assert_raises(sq.OperationalError):
        cursor.execute("SELECT * FROM nonexistent_table")

    # Integrity error (UNIQUE constraint)
    cursor.execute("CREATE TABLE unique_test (id INTEGER PRIMARY KEY, val TEXT UNIQUE)")
    cursor.execute("INSERT INTO unique_test (val) VALUES ('duplicate')")
    with assert_raises(sq.IntegrityError):
        cursor.execute("INSERT INTO unique_test (val) VALUES ('duplicate')")

    # NOT NULL constraint
    cursor.execute("CREATE TABLE notnull_test (required TEXT NOT NULL)")
    with assert_raises(sq.IntegrityError):
        cursor.execute("INSERT INTO notnull_test (required) VALUES (NULL)")

    # Wrong number of bindings
    with assert_raises((sq.ProgrammingError, sq.OperationalError)):
        cursor.execute("SELECT ?, ?", (1,))  # Too few

    with assert_raises((sq.ProgrammingError, sq.OperationalError)):
        cursor.execute("SELECT ?", (1, 2, 3))  # Too many

    conn.close()

    # Operations on closed connection/cursor
    with assert_raises(sq.ProgrammingError):
        cursor.execute("SELECT 1")


@unit
def cursor_iteration_and_arraysize(sq: ModuleType):
    """Test cursor as iterator and arraysize behavior."""
    conn = sq.connect(":memory:")
    cursor = conn.cursor()

    cursor.execute("CREATE TABLE nums (n INTEGER)")
    cursor.executemany("INSERT INTO nums VALUES (?)", [(i,) for i in range(10)])
    conn.commit()

    # Cursor is iterable
    cursor.execute("SELECT n FROM nums ORDER BY n")
    collected = []
    for row in cursor:
        collected.append(row[0])
    assert collected == list(range(10))

    # arraysize affects fetchmany default
    cursor.execute("SELECT n FROM nums ORDER BY n")
    cursor.arraysize = 3
    batch = cursor.fetchmany()  # No argument uses arraysize
    assert len(batch) == 3
    assert batch == [(0,), (1,), (2,)]

    # Explicit size overrides arraysize
    batch = cursor.fetchmany(5)
    assert len(batch) == 5

    # Fetch remaining
    batch = cursor.fetchmany()
    assert len(batch) == 2  # Only 2 left

    conn.close()


@unit
def connection_attributes_and_methods(sq: ModuleType):
    """Test various connection attributes and utility methods."""
    conn = sq.connect(":memory:")

    # total_changes tracks all changes
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE changes_test (x INTEGER)")
    initial = conn.total_changes

    cursor.execute("INSERT INTO changes_test VALUES (1)")
    cursor.execute("INSERT INTO changes_test VALUES (2)")
    cursor.execute("UPDATE changes_test SET x = 10 WHERE x = 1")

    assert conn.total_changes >= initial + 3

    # in_transaction property (if available)
    if hasattr(conn, 'in_transaction'):
        conn.commit()
        assert not conn.in_transaction
        cursor.execute("INSERT INTO changes_test VALUES (3)")
        assert conn.in_transaction
        conn.commit()
        assert not conn.in_transaction

    # execute on connection directly (convenience method)
    result = conn.execute("SELECT COUNT(*) FROM changes_test")
    assert result.fetchone()[0] >= 3

    # executemany on connection
    conn.executemany("INSERT INTO changes_test VALUES (?)", [(100,), (200,)])

    # interrupt() method exists
    assert hasattr(conn, 'interrupt')
    assert callable(conn.interrupt)

    conn.close()


@unit
def pragmas_and_database_info(sq: ModuleType):
    """Test PRAGMA statements and database introspection."""
    conn = sq.connect(":memory:")
    cursor = conn.cursor()

    # PRAGMA queries work
    cursor.execute("PRAGMA table_info(sqlite_master)")
    # Should return info about sqlite_master columns
    info = cursor.fetchall()
    assert len(info) > 0

    # Create a table and inspect it
    cursor.execute("CREATE TABLE inspectable (col1 INTEGER, col2 TEXT, col3 REAL)")
    cursor.execute("PRAGMA table_info(inspectable)")
    columns = cursor.fetchall()

    assert len(columns) == 3
    # Each row: (cid, name, type, notnull, dflt_value, pk)
    col_names = [col[1] for col in columns]
    assert "col1" in col_names
    assert "col2" in col_names
    assert "col3" in col_names

    # PRAGMA for settings
    cursor.execute("PRAGMA cache_size")
    cache_size = cursor.fetchone()
    assert cache_size is not None

    # Set and read back
    cursor.execute("PRAGMA cache_size = 2000")
    cursor.execute("PRAGMA cache_size")
    # Value might be stored differently, just verify it's readable

    conn.close()


@unit
def null_and_empty_handling(sq: ModuleType):
    """Test edge cases around NULL values and empty strings."""
    conn = sq.connect(":memory:")
    cursor = conn.cursor()

    cursor.execute("CREATE TABLE nulls (a TEXT, b INTEGER, c BLOB)")

    # Explicit NULLs
    cursor.execute("INSERT INTO nulls VALUES (NULL, NULL, NULL)")
    cursor.execute("INSERT INTO nulls VALUES (?, ?, ?)", (None, None, None))

    # Empty string is NOT NULL
    cursor.execute("INSERT INTO nulls VALUES ('', 0, X'')")

    cursor.execute("SELECT * FROM nulls WHERE a IS NULL")
    assert len(cursor.fetchall()) == 2

    cursor.execute("SELECT * FROM nulls WHERE a = ''")
    assert len(cursor.fetchall()) == 1

    # Empty blob
    cursor.execute("SELECT c FROM nulls WHERE c = X''")
    row = cursor.fetchone()
    assert row[0] == b""

    # Comparison with NULL
    cursor.execute("SELECT * FROM nulls WHERE a = NULL")  # Always false
    assert cursor.fetchall() == []

    cursor.execute("SELECT * FROM nulls WHERE a IS NOT NULL")
    assert len(cursor.fetchall()) == 1

    conn.close()


@unit
def connection_factory_and_detect_types(sq: ModuleType):
    """Test connection factory parameter and detect_types for date/time."""
    import datetime

    # Basic connection with detect_types
    conn = sq.connect(
        ":memory:",
        detect_types=sq.PARSE_DECLTYPES | sq.PARSE_COLNAMES
    )
    cursor = conn.cursor()

    # Register adapter and converter for datetime
    if hasattr(sq, 'register_adapter') and hasattr(sq, 'register_converter'):
        # These may already be registered for datetime types
        cursor.execute("CREATE TABLE times (ts TIMESTAMP, d DATE)")

        now = datetime.datetime.now()
        today = datetime.date.today()

        # Insert datetime objects
        cursor.execute("INSERT INTO times VALUES (?, ?)", (now, today))

        cursor.execute("SELECT ts, d FROM times")
        row = cursor.fetchone()

        # With PARSE_DECLTYPES, should get datetime objects back
        # (behavior may vary based on registered converters)
        assert row is not None

    # PARSE_COLNAMES allows type hints in column names
    cursor.execute("SELECT 1 as 'value [integer]'")
    row = cursor.fetchone()
    assert row[0] == 1

    conn.close()


@unit
def backup_functionality(sq: ModuleType):
    """Test database backup functionality if available."""
    source = sq.connect(":memory:")
    source.execute("CREATE TABLE data (x INTEGER)")
    source.executemany("INSERT INTO data VALUES (?)", [(i,) for i in range(100)])
    source.commit()

    target = sq.connect(":memory:")

    # backup method (Python 3.7+)
    if hasattr(source, 'backup'):
        source.backup(target)

        cursor = target.cursor()
        cursor.execute("SELECT COUNT(*) FROM data")
        assert cursor.fetchone()[0] == 100

        cursor.execute("SELECT SUM(x) FROM data")
        assert cursor.fetchone()[0] == sum(range(100))

    source.close()
    target.close()


@unit
def module_constants(sq: ModuleType):
    """Test that required module-level constants exist."""
    # Version info
    assert hasattr(sq, 'version')
    assert hasattr(sq, 'version_info')
    assert hasattr(sq, 'sqlite_version')
    assert hasattr(sq, 'sqlite_version_info')

    # Useful constants
    assert hasattr(sq, 'PARSE_DECLTYPES')
    assert hasattr(sq, 'PARSE_COLNAMES')

    # Check that version strings are strings
    assert isinstance(sq.version, str)
    assert isinstance(sq.sqlite_version, str)

    # version_info should be tuple-like
    assert len(sq.version_info) >= 3
    assert len(sq.sqlite_version_info) >= 3


@unit
def blob_operations(sq: ModuleType):
    """Test binary data (BLOB) handling thoroughly."""
    conn = sq.connect(":memory:")
    cursor = conn.cursor()

    cursor.execute("CREATE TABLE blobs (id INTEGER PRIMARY KEY, data BLOB)")

    # Various binary data
    test_data = [
        b"",  # Empty
        b"\x00",  # Single null byte
        b"\x00\x00\x00",  # Multiple null bytes
        b"\xff\xfe\xfd",  # High bytes
        bytes(range(256)),  # All byte values
        b"hello\x00world",  # Embedded null
    ]

    for data in test_data:
        cursor.execute("INSERT INTO blobs (data) VALUES (?)", (data,))

    cursor.execute("SELECT data FROM blobs ORDER BY id")
    results = [row[0] for row in cursor.fetchall()]

    assert results == test_data

    # Blob literals
    cursor.execute("SELECT X'48454C4C4F'")  # 'HELLO' in hex
    assert cursor.fetchone()[0] == b"HELLO"

    conn.close()


@unit
def aggregate_functions(sq: ModuleType):
    """Test built-in aggregate functions and GROUP BY."""
    conn = sq.connect(":memory:")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE sales (
            region TEXT,
            product TEXT,
            amount REAL
        )
    """)

    data = [
        ("North", "Widget", 100.0),
        ("North", "Gadget", 150.0),
        ("South", "Widget", 200.0),
        ("South", "Gadget", 50.0),
        ("North", "Widget", 75.0),
    ]
    cursor.executemany("INSERT INTO sales VALUES (?, ?, ?)", data)

    # COUNT
    cursor.execute("SELECT COUNT(*) FROM sales")
    assert cursor.fetchone()[0] == 5

    cursor.execute("SELECT COUNT(DISTINCT region) FROM sales")
    assert cursor.fetchone()[0] == 2

    # SUM, AVG, MIN, MAX
    cursor.execute("SELECT SUM(amount), AVG(amount), MIN(amount), MAX(amount) FROM sales")
    row = cursor.fetchone()
    assert row[0] == 575.0  # SUM
    assert row[1] == 115.0  # AVG
    assert row[2] == 50.0  # MIN
    assert row[3] == 200.0  # MAX

    # GROUP BY
    cursor.execute("""
        SELECT region, SUM(amount) as total
        FROM sales
        GROUP BY region
        ORDER BY region
    """)
    rows = cursor.fetchall()
    assert rows[0] == ("North", 325.0)
    assert rows[1] == ("South", 250.0)

    # HAVING
    cursor.execute("""
        SELECT product, COUNT(*) as cnt
        FROM sales
        GROUP BY product
        HAVING COUNT(*) > 2
    """)
    rows = cursor.fetchall()
    assert len(rows) == 1
    assert rows[0] == ("Widget", 3)

    conn.close()
