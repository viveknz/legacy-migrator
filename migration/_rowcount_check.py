"""
_rowcount_check.py – compare row counts between SQL Server Northwind and
the migrated PostgreSQL northwind_target database.
"""
import sys

try:
    import pyodbc
except ImportError:
    print("ERROR: pyodbc not installed")
    sys.exit(1)

try:
    import psycopg2
except ImportError:
    print("ERROR: psycopg2 not installed")
    sys.exit(1)

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

MSSQL_CONN_STR = (
    "DRIVER={SQL Server};"
    "SERVER=localhost,1433;"
    "DATABASE=Northwind;"
    "UID=sa;"
    "PWD=BugSquash!2026x;"
    "TrustServerCertificate=yes;"
)

PG_CONN_PARAMS = dict(
    host="localhost", port=5432,
    dbname="northwind_target",
    user="postgres", password="BugSquash2026",
)

# ── connect ──────────────────────────────────────────────────────────────────
try:
    mssql_conn = pyodbc.connect(MSSQL_CONN_STR, timeout=10)
    mssql_cur  = mssql_conn.cursor()
    print("SQL Server : connected")
except Exception as e:
    print("SQL Server connect FAILED:", e)
    sys.exit(1)

try:
    pg_conn = psycopg2.connect(**PG_CONN_PARAMS)
    pg_cur  = pg_conn.cursor()
    print("PostgreSQL : connected")
except Exception as e:
    print("PostgreSQL connect FAILED:", e)
    mssql_conn.close()
    sys.exit(1)

# ── count rows ───────────────────────────────────────────────────────────────
print()
print(f"{'Table':<28}  {'MSSQL':>8}  {'PG':>8}  Result")
print("-" * 60)

all_ok  = True
total_src = 0
total_dst = 0

for table in TABLES:
    try:
        mssql_cur.execute(f"SELECT COUNT(*) FROM [{table}]")
        src = mssql_cur.fetchone()[0]
    except Exception as e:
        src = None
        src_label = "ERR"
    else:
        src_label = str(src)

    try:
        pg_cur.execute(f'SELECT COUNT(*) FROM "{table}"')
        dst = pg_cur.fetchone()[0]
    except Exception as e:
        dst = None
        dst_label = "ERR"
    else:
        dst_label = str(dst)

    if src is not None and dst is not None:
        ok = src == dst
        result = "OK" if ok else "MISMATCH <<<"
        if not ok:
            all_ok = False
        total_src += src
        total_dst += dst
    else:
        result = "ERROR <<<"
        all_ok = False

    print(f"  {table:<26}  {src_label:>8}  {dst_label:>8}  {result}")

print("-" * 60)
print(f"  {'TOTAL':<26}  {total_src:>8}  {total_dst:>8}")
print()
if all_ok:
    print("RESULT: ALL TABLES MATCH — migration verified successfully.")
else:
    print("RESULT: DISCREPANCIES DETECTED — see rows marked <<<")

mssql_cur.close()
mssql_conn.close()
pg_cur.close()
pg_conn.close()
