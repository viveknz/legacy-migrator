# IBM Bob Usage Statement

IBM Bob 2.0 drove the entire build, used through both the Bob IDE and the Bob Shell CLI, for the parts of this job that would normally eat a full day of careful, tedious reading.

First, Bob was given the schema metadata and the exact source of every stored procedure, trigger, and view — pulled straight from `sys.sql_modules`, so it was working from the real code, not a summary — for both Northwind and Pubs. It flagged deprecated SQL Server syntax, quoted the specific offending line, and scored migration risk with reasoning that could actually be checked. This ran as two separate tasks, one per database, for a cleaner result on each.

From there, Bob generated PostgreSQL-compatible DDL for the whole Northwind schema, handling the data-type differences (SQL Server's `money` and `ntext` types, for example) and ordering the foreign keys correctly. Then it wrote the actual Python migration script, using pyodbc and psycopg2, including the identity-sequence resync Postgres needs after a bulk load like this.

The standout step: once the migration had run, Bob was handed a fresh task with no memory of having written the migration, and asked to independently query the Postgres target and confirm the row counts matched the source. Bob checking Bob's own work, not just trusting the first output.

Bob's output needed very little correction — the one manual fix was a connection-string driver name, since the generated script assumed a newer ODBC driver than was actually installed. Everything else — the DDL, the migration logic, the audit findings — was used as generated. Every one of these tasks has its session summary captured in `bob_sessions/` as evidence.

The Bob IDE was also used directly to review its analysis, including a dependency graph it built of the Northwind schema's foreign-key relationships. That's how a self-referencing foreign key on the Employees table (`ReportsTo`) got caught early — the kind of detail that would break a naive insert order and is easy to miss by hand.

Bob wasn't used here as a coding assistant filling in boilerplate. It did the analysis, wrote the migration, and then checked its own result — three genuinely different jobs, on one real pipeline that actually runs.
