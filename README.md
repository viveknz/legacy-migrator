# Legacy Migration Risk Assistant — Bug Squash (IBM Bob 2.0 Hackathon)

## What this is
An IBM Bob 2.0-assisted tool that audits a legacy SQL Server database (Microsoft's
official Northwind + Pubs sample databases — genuinely SQL Server 2000-era schemas,
still carrying deprecated syntax, business logic buried in stored procedures and
triggers, and no test coverage) and produces:

1. An **onboarding brief** — a new engineer's map of the schema, its stored
   procedures/triggers, and where the real business logic lives.
2. A **migration risk score** — evidence-backed score per object (deprecated
   syntax, FK complexity, logic embedded in procs/triggers, missing tests) plus a
   time-saved estimate (manual audit vs. Bob-run audit).
3. A **working Postgres migration** of the schema + data, generated and validated
   with Bob's help, as proof the risk assessment translates into real migration
   work — not just a report.

## Why this maps to the brief
Matches the hackathon's official example use cases:
- **#5 Legacy Application Modernization Accelerator** (Application Maintenance) — core scope.
- **#1 Smart Developer Onboarding Assistant** (Onboarding) — the onboarding brief.

## Source material
- `schema/` — column-level schema dumps (table, column, type, nullability, default)
  and foreign-key maps for both databases, extracted via `sqlcmd`.
- `procs_triggers/` — the exact `CREATE PROCEDURE` / `CREATE TRIGGER` / `CREATE VIEW`
  text for every object with a body, pulled straight from `sys.sql_modules`
  (i.e. the real legacy code, not a paraphrase).
- Source databases: Microsoft's official `instnwnd.sql` / `instpubs.sql` from
  github.com/microsoft/sql-server-samples, running in a `bugsquash-sqlserver`
  Docker container (SQL Server 2019 engine, but the schema/scripts themselves are
  unmodified 2000-era Microsoft sample code).
- Target: `bugsquash-postgres` Docker container (Postgres 16, db `northwind_target`).

## Bob's role (what goes in bob_sessions/)
Bob is run via Bob Shell (`bob run`), one task per audit dimension, orchestrated as
subagents where possible:
1. Deprecated/legacy syntax scan across `procs_triggers/*.txt`.
2. Business-logic extraction — what each proc/trigger actually *does*, in plain
   English, flagging anything a migration could silently break.
3. Risk scoring per table/object, with evidence lines quoted from the source.
4. Postgres migration script generation (DDL + data type mapping + any logic that
   needs a Postgres-native equivalent, e.g. triggers).
5. Synthesis into the final report (`reports/audit_report.md`).

Each task's session summary is screenshotted into `bob_sessions/` per the
submission requirements (team name + task number + description in the filename).
