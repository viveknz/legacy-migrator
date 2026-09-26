```
 ___ ____  __  __   ____   ___  ____    ____    ___
|_ _| __ )|  \/  | | __ ) / _ \| __ )  |___ \  / _ \
 | ||  _ \| |\/| | |  _ \| | | |  _ \    __) || | | |
 | || |_) | |  | | | |_) | |_| | |_) |  / __/ | |_| |
|___|____/|_|  |_| |____/ \___/|____/  |_____(_)___/
```

<p align="center"><strong>H A C K A T H O N</strong> &nbsp;×&nbsp; <strong>L A B L A B . A I</strong></p>

<p align="center"><code>[ team: BUG SQUASH ]</code></p>

<p align="center">
  <strong>Legacy Migration Risk Assistant</strong>
  <br>
  Sept 25–27, 2026 · Solo entry
</p>

<p align="center">
  <img alt="IBM Bob 2.0" src="https://img.shields.io/badge/built%20with-IBM%20Bob%202.0-052FAD?style=for-the-badge">
  <img alt="lablab.ai" src="https://img.shields.io/badge/hackathon-lablab.ai-FF6A3D?style=for-the-badge">
  <img alt="status" src="https://img.shields.io/badge/status-working%20prototype-2ea44f?style=for-the-badge">
</p>

---

## ⚡ TL;DR

A legacy SQL Server database walks in. Bob walks it out — **audited, risk-scored,
and actually migrated to Postgres**, not just described in a slide.

```
┌──────────────────────┐         ┌──────────────────────────┐        ┌───────────────────────┐
│   LEGACY SQL SERVER  │         │      IBM BOB 2.0         │        │       POSTGRES        │
│  ─────────────────── │         │  ───────────────────     │        │  ───────────────────  │
│  Northwind (1998)    │  ───▶   │  • Deprecated-syntax    │  ───▶  │  Schema created       │
│  Pubs (1998)         │         │     scan                │        │  13 tables + 13 FKs    │
│  13 procs/triggers   │         │  • Business-logic       │        │  3,308 rows migrated   │
│  16 views            │         │    extraction           │        │  row counts verified   │
│  no docs, no tests   │         │  • Risk scoring         │        │  = exact match to      │
│                      │         │  • DDL + data-copy      │        │    source              │
│                      │         │    script generation    │        │                        │
└──────────────────────┘         └─────────────────────────┘        └────────────────────────┘
```

## 🧩 The problem

Every team inherits a database nobody wants to touch: no docs, deprecated syntax,
business logic buried three stored procedures deep, and a migration that "someone
should really do at some point." Manually auditing that before migrating it is a
full day of a senior engineer's time — per database — before a single line of the
actual migration gets written.

## 🎯 What Bob actually did here

| # | Task | Bob's output | Verified |
|---|------|---------------|----------|
| 1 | Audit Northwind | `reports/audit_report_northwind.md` — 12 risk categories, evidence-quoted | ✅ manual review |
| 2 | Audit Pubs | `reports/audit_report_pubs.md` | ✅ manual review |
| 3 | Generate Postgres DDL | `migration/northwind_postgres_ddl.sql` | ✅ applied — 13 tables, 13 FKs, zero errors |
| 4 | Generate data-migration script | `migration/migrate_northwind_data.py` | ✅ run — 3,308 rows, exact row-count match to source |

Bob's own task-session summaries (cost, duration, tool calls) are in
[`bob_sessions/`](./bob_sessions) — one screenshot per task above.

## 🏗️ Why this approach

- **Real legacy code, not a toy example** — Northwind and Pubs are Microsoft's own
  official 1998-era sample databases, genuinely carrying deprecated syntax
  (`SET ROWCOUNT`, `ntext`, `image`, comma-joins) and real business logic in
  procs/triggers.
- **A working migration, not just a report** — the differentiator: the audit
  feeds directly into a generated, executed, and verified Postgres migration.
  Data is actually sitting in Postgres by the end, with counts proven to match.
- **Onboarding + risk, in one pass** — maps to both of the hackathon's official
  example use cases: *Legacy Application Modernization Accelerator* and
  *Smart Developer Onboarding Assistant*.

## 📂 Repo layout

```
legacy-migrator/
├── schema/              # extracted column/FK metadata (Northwind + Pubs)
├── procs_triggers/      # exact CREATE PROCEDURE/TRIGGER/VIEW source (sys.sql_modules)
├── reports/             # Bob-generated audit reports
├── migration/           # Bob-generated Postgres DDL + data-migration script
├── bob_sessions/        # required: Bob task session summary screenshots
├── demo_assets/         # screenshots for the video
├── slide_assets/        # screenshots + images for the slide deck
└── README.md
```

## 🛠️ Stack

SQL Server 2019 (Docker) · PostgreSQL 16 (Docker) · IBM Bob 2.0 (Bob Shell CLI) ·
Python (pyodbc, psycopg2)

---

<p align="center"><sub>Built solo, driven hard, one Bob task at a time. 🐛🔨</sub></p>
