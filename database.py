
import sqlite3
from pathlib import Path

import sqlglot
from sqlglot import exp


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "sales.db"

ALLOWED_TABLES = {"customers", "products", "orders"}

SCHEMA_DESCRIPTION = """
Table: customers
- customer_id: INTEGER
- name: TEXT
- city: TEXT

Table: products
- product_id: INTEGER
- product_name: TEXT
- category: TEXT
- price: REAL

Table: orders
- order_id: INTEGER
- customer_id: INTEGER
- product_id: INTEGER
- quantity: INTEGER
- status: TEXT

Relationships:
- orders.customer_id = customers.customer_id
- orders.product_id = products.product_id
"""


def get_connection():
    """Create a new connection to the SQLite database."""
    conn = sqlite3.connect(str(DB_PATH), timeout=5)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    """Create tables and insert sample data on first run."""
    conn = get_connection()

    try:
        conn.execute("PRAGMA foreign_keys = ON")

        conn.executescript("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            city TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY,
            product_name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (customer_id)
                REFERENCES customers(customer_id),
            FOREIGN KEY (product_id)
                REFERENCES products(product_id)
        );
        """)

        if conn.execute(
            "SELECT COUNT(*) FROM customers"
        ).fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO customers VALUES (?, ?, ?)",
                [
                    (1, "Asha", "Hyderabad"),
                    (2, "Rahul", "Bengaluru"),
                    (3, "Priya", "Hyderabad"),
                    (4, "Arjun", "Chennai"),
                    (5, "Sneha", "Bengaluru"),
                ],
            )

        if conn.execute(
            "SELECT COUNT(*) FROM products"
        ).fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO products VALUES (?, ?, ?, ?)",
                [
                    (101, "Laptop", "Electronics", 55000),
                    (102, "Headphones", "Accessories", 2000),
                    (103, "Keyboard", "Accessories", 1500),
                    (104, "Mouse", "Accessories", 800),
                ],
            )

        if conn.execute(
            "SELECT COUNT(*) FROM orders"
        ).fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO orders VALUES (?, ?, ?, ?, ?)",
                [
                    (1001, 1, 101, 1, "Delivered"),
                    (1002, 2, 102, 2, "Delivered"),
                    (1003, 1, 104, 2, "Delivered"),
                    (1004, 3, 103, 3, "Cancelled"),
                    (1005, 4, 101, 1, "Delivered"),
                    (1006, 5, 102, 1, "Pending"),
                    (1007, 2, 104, 3, "Delivered"),
                    (1008, 3, 101, 1, "Delivered"),
                ],
            )

        conn.commit()

    finally:
        conn.close()


def validate_sql(query: str) -> str:
    """Validate SQL and return a normalized, limited SELECT query."""
    try:
        statements = sqlglot.parse(query, read="sqlite")
    except Exception as exc:
        raise ValueError("Invalid SQL syntax.") from exc

    if (
        len(statements) != 1
        or not statements
        or statements[0] is None
    ):
        raise ValueError("Only one SQL statement is allowed.")

    tree = statements[0]

    if not isinstance(tree, exp.Select):
        raise ValueError("Only SELECT queries are allowed.")

    tables = list(tree.find_all(exp.Table))

    if not tables:
        raise ValueError(
            "The query must reference an approved table."
        )

    for table in tables:
        if table.db or table.catalog:
            raise ValueError(
                "Qualified table names are not allowed."
            )

        if table.name.lower() not in ALLOWED_TABLES:
            raise ValueError(
                f"Table not allowed: {table.name}"
            )

    if not tree.args.get("limit"):
        tree = tree.limit(100)

    return tree.sql(dialect="sqlite")


def execute_safe_sql(query: str) -> dict:
    """Execute a validated query with SQLite read-only safeguards."""
    validated_query = validate_sql(query)
    conn = get_connection()

    allowed_functions = {
        "count", "sum", "avg", "min", "max",
        "lower", "upper", "length", "round",
        "coalesce", "ifnull", "nullif",
        "substr", "replace", "trim",
    }

    def authorizer(action, arg1, arg2, database, source):
        if action in (
            sqlite3.SQLITE_SELECT,
            sqlite3.SQLITE_RECURSIVE,
        ):
            return sqlite3.SQLITE_OK

        if action == sqlite3.SQLITE_READ:
            if arg1 and arg1.lower() in ALLOWED_TABLES:
                return sqlite3.SQLITE_OK
            return sqlite3.SQLITE_DENY

        if action == sqlite3.SQLITE_FUNCTION:
            function_name = (arg2 or arg1 or "").lower()
            if function_name in allowed_functions:
                return sqlite3.SQLITE_OK
            return sqlite3.SQLITE_DENY

        return sqlite3.SQLITE_DENY

    try:
        conn.set_authorizer(authorizer)

        # Abort expensive queries after enough SQLite VM operations.
        conn.set_progress_handler(lambda: 1, 1_000_000)

        cursor = conn.execute(validated_query)
        rows = cursor.fetchmany(101)

        if len(rows) > 100:
            raise ValueError("Query returned more than 100 rows.")

        if cursor.description is None:
            raise ValueError("Query did not return a result set.")

        return {
            "sql": validated_query,
            "rows": [dict(row) for row in rows],
        }

    except sqlite3.DatabaseError as exc:
        raise ValueError(
            f"SQL execution rejected: {exc}"
        ) from exc

    finally:
        conn.set_progress_handler(None, 0)
        conn.set_authorizer(None)
        conn.close()
