"""
migrate_northwind_data.py

Copies all data from the SQL Server Northwind database into the already-created
PostgreSQL schema in northwind_target, migrating tables in FK-safe order.

Requirements:
    pip install pyodbc psycopg2-binary

Usage:
    python migration/migrate_northwind_data.py
"""

import sys
import pyodbc
import psycopg2
from psycopg2.extras import execute_values

# ---------------------------------------------------------------------------
# Connection parameters
# ---------------------------------------------------------------------------

MSSQL_CONN_STR = (
    "DRIVER={SQL Server};"
    "SERVER=localhost,1433;"
    "DATABASE=Northwind;"
    "UID=sa;"
    "PWD=BugSquash!2026x;"
    "TrustServerCertificate=yes;"
)

PG_CONN_PARAMS = {
    "host": "localhost",
    "port": 5432,
    "dbname": "northwind_target",
    "user": "postgres",
    "password": "BugSquash2026",
}

# ---------------------------------------------------------------------------
# Migration order (FK-safe: parents before children)
# ---------------------------------------------------------------------------

TABLES = [
    "Categories",
    "Suppliers",
    "Shippers",
    "Employees",
    "Customers",
    "Products",
    "Region",
    "Territories",
    "Orders",
    "Order Details",
    "CustomerDemographics",
    "CustomerCustomerDemo",
    "EmployeeTerritories",
]

# Tables whose PK is GENERATED ALWAYS AS IDENTITY in Postgres.
# We must use OVERRIDING SYSTEM VALUE to insert explicit ID values.
IDENTITY_TABLES = {
    "Categories",
    "Employees",
    "Orders",
    "Products",
    "Region",
    "Shippers",
    "Suppliers",
}


def quote_pg(name: str) -> str:
    """Return a double-quoted PostgreSQL identifier."""
    return '"' + name.replace('"', '""') + '"'


def fetch_mssql_table(mssql_cur, table: str):
    """
    Return (column_names, rows) for the given SQL Server table.
    Uses square-bracket quoting for the table name.
    """
    mssql_cur.execute(f"SELECT * FROM [{table}]")
    columns = [desc[0] for desc in mssql_cur.description]
    rows = mssql_cur.fetchall()
    return columns, rows


def coerce_row(row):
    """
    Convert a pyodbc Row to a plain tuple, converting any bytearray values
    (SQL Server image/varbinary) to bytes for psycopg2.
    """
    return tuple(
        bytes(v) if isinstance(v, (bytearray, memoryview)) else v
        for v in row
    )


def insert_table(pg_cur, table: str, columns: list, rows: list) -> int:
    """
    Bulk-insert rows into the PostgreSQL table using execute_values.
    Returns the number of rows inserted.
    """
    if not rows:
        return 0

    quoted_table = quote_pg(table)
    quoted_cols = ", ".join(quote_pg(c) for c in columns)
    placeholders = "(" + ", ".join(["%s"] * len(columns)) + ")"

    if table in IDENTITY_TABLES:
        sql = (
            f"INSERT INTO {quoted_table} ({quoted_cols}) "
            f"OVERRIDING SYSTEM VALUE VALUES %s"
        )
    else:
        sql = f"INSERT INTO {quoted_table} ({quoted_cols}) VALUES %s"

    coerced = [coerce_row(r) for r in rows]
    execute_values(pg_cur, sql, coerced, template=placeholders, page_size=500)
    return len(coerced)


def reset_sequences(pg_conn, pg_cur):
    """
    After inserting with OVERRIDING SYSTEM VALUE the sequences are out of sync.
    Reset each identity sequence to max(id)+1 so future inserts work correctly.
    """
    sequence_cols = {
        "Categories":  "CategoryID",
        "Employees":   "EmployeeID",
        "Orders":      "OrderID",
        "Products":    "ProductID",
        "Region":      "RegionID",
        "Shippers":    "ShipperID",
        "Suppliers":   "SupplierID",
    }
    for table, col in sequence_cols.items():
        pg_cur.execute(
            f"SELECT setval("
            f"  pg_get_serial_sequence({quote_pg(table)!r}, {col!r}), "  # noqa: E501 – we build the SQL string ourselves below
            f"  COALESCE((SELECT MAX({quote_pg(col)}) FROM {quote_pg(table)}), 1), "
            f"  true"
            f")"
        )
    pg_conn.commit()


def reset_sequences_safe(pg_conn, pg_cur):
    """
    Reset identity sequences using a parameterised approach that avoids
    f-string quoting confusion.
    """
    sequence_cols = {
        "Categories":  "CategoryID",
        "Employees":   "EmployeeID",
        "Orders":      "OrderID",
        "Products":    "ProductID",
        "Region":      "RegionID",
        "Shippers":    "ShipperID",
        "Suppliers":   "SupplierID",
    }
    for table, col in sequence_cols.items():
        qt = quote_pg(table)
        qc = quote_pg(col)
        pg_cur.execute(
            f"SELECT setval("
            f"  pg_get_serial_sequence('{table}', '{col}'), "
            f"  COALESCE((SELECT MAX({qc}) FROM {qt}), 1), "
            f"  true"
            f")"
        )
    pg_conn.commit()


def migrate():
    print("Connecting to SQL Server …")
    try:
        mssql_conn = pyodbc.connect(MSSQL_CONN_STR, timeout=10)
    except pyodbc.Error as exc:
        print(f"ERROR: Could not connect to SQL Server: {exc}", file=sys.stderr)
        sys.exit(1)

    print("Connecting to PostgreSQL …")
    try:
        pg_conn = psycopg2.connect(**PG_CONN_PARAMS)
    except psycopg2.Error as exc:
        print(f"ERROR: Could not connect to PostgreSQL: {exc}", file=sys.stderr)
        mssql_conn.close()
        sys.exit(1)

    mssql_cur = mssql_conn.cursor()
    pg_cur = pg_conn.cursor()
    pg_conn.autocommit = False

    summary = {}
    total_rows = 0
    errors = []

    print()
    print(f"{'Table':<30}  {'Rows':>8}")
    print("-" * 42)

    for table in TABLES:
        try:
            columns, rows = fetch_mssql_table(mssql_cur, table)
            count = insert_table(pg_cur, table, columns, rows)
            pg_conn.commit()
            summary[table] = count
            total_rows += count
            print(f"  {table:<28}  {count:>8,}")
        except Exception as exc:  # noqa: BLE001
            pg_conn.rollback()
            msg = f"  {table:<28}  FAILED: {exc}"
            print(msg)
            errors.append((table, str(exc)))
            summary[table] = "ERROR"

    # Resync identity sequences so the target DB is usable after migration
    print()
    print("Resyncing identity sequences …")
    try:
        reset_sequences_safe(pg_conn, pg_cur)
        print("  Done.")
    except Exception as exc:  # noqa: BLE001
        print(f"  WARNING: sequence reset failed: {exc}", file=sys.stderr)

    mssql_cur.close()
    mssql_conn.close()
    pg_cur.close()
    pg_conn.close()

    # Final summary
    print()
    print("=" * 42)
    print("MIGRATION SUMMARY")
    print("=" * 42)
    for table, count in summary.items():
        if isinstance(count, int):
            print(f"  {table:<28}  {count:>8,} rows")
        else:
            print(f"  {table:<28}  {count}")
    print("-" * 42)
    print(f"  {'TOTAL':<28}  {total_rows:>8,} rows")
    if errors:
        print()
        print(f"  {len(errors)} table(s) failed:")
        for t, e in errors:
            print(f"    • {t}: {e}")
        sys.exit(1)
    else:
        print()
        print("  All tables migrated successfully.")


if __name__ == "__main__":
    migrate()

