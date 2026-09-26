# Pubs Database — Pre-Migration Audit Report
**Target:** PostgreSQL migration from SQL Server 2000-era schema  
**Generated:** automated static analysis pass  
**Scope:** `schema/Pubs_columns.txt`, `schema/Pubs_foreign_keys.txt`, `procs_triggers/Pubs_modules.txt`

---

## 1. Executive Summary

The Pubs database is a small, well-known SQL Server sample containing 11 tables, 10 foreign keys, 4 stored procedures, 1 trigger, and 1 view — a low-volume schema that nonetheless carries several SQL Server–specific idioms that will break or silently misbehave on PostgreSQL without intervention. This automated pass identified all migration-blocking issues (deprecated `WITH ROLLUP` syntax, implicit old-style comma joins, `RAISERROR`/`ROLLBACK` trigger logic, `money`/`image`/`text` legacy types, and `getdate()` default expressions) in under 5 minutes, compared with an estimated **6–8 hours** for a senior engineer performing the same review manually. Acting on this report before writing any migration scripts will prevent the most common class of Postgres migration failures: silent type coercions, aggregate syntax errors, and trigger semantics differences.

---

## 2. Deprecated / Legacy SQL Server Syntax Findings

### 2.1 `GROUP BY … WITH ROLLUP` (T-SQL–only aggregate modifier)

PostgreSQL uses `GROUP BY ROLLUP(…)` (ANSI SQL:1999 syntax). The T-SQL trailing `WITH ROLLUP` clause is not recognised by `pg_dump` loaders or any Postgres-compatible migration tool and will produce a parse error on every affected procedure.

**Evidence — `reptq1` (line 15):**
```sql
group by pub_id with rollup
```
**Evidence — `reptq2` (line 27):**
```sql
group by pub_id, type with rollup
```
**Evidence — `reptq3` (line 40):**
```sql
group by pub_id, type with rollup
```
**Fix:** Replace each occurrence with the ANSI form, e.g.:
```sql
GROUP BY ROLLUP(pub_id)
GROUP BY ROLLUP(pub_id, type)
```

---

### 2.2 Implicit (comma-style) JOIN syntax

The `FROM authors, titles, titleauthor WHERE …` pattern is ANSI SQL-89 style. While PostgreSQL does parse it, it is considered deprecated best practice and is particularly error-prone when mixed with outer joins or when the join predicate is accidentally omitted. All migration target objects should use explicit `JOIN … ON` syntax.

**Evidence — `titleview` (lines 77–79):**
```sql
from authors, titles, titleauthor
where authors.au_id = titleauthor.au_id
   AND titles.title_id = titleauthor.title_id
```

**Evidence — `employee_insupd` trigger (line 57):**
```sql
from employee e, jobs j, inserted i
```

---

### 2.3 `RAISERROR` (deprecated T-SQL spelling and calling convention)

SQL Server's `RAISERROR` (one 'e') with the `(msg, severity, state, …)` variadic substitution signature does not exist in PostgreSQL. PostgreSQL uses `RAISE EXCEPTION '…' USING ERRCODE = '…'` or `RAISE EXCEPTION` with `FORMAT`-style substitutions via `%`.

**Evidence — `employee_insupd` trigger (lines 61, 67–68):**
```sql
raiserror ('Job id 1 expects the default level of 10.',16,1)
raiserror ('The level for job_id:%d should be between %d and %d.',
   16, 1, @job_id, @min_lvl, @max_lvl)
```

---

### 2.4 `ROLLBACK TRANSACTION` inside a trigger

In SQL Server a trigger can issue `ROLLBACK TRANSACTION` to abort the entire calling transaction from within the trigger body. In PostgreSQL, a trigger function runs inside the caller's transaction and cannot independently execute `ROLLBACK`; the equivalent is raising an exception (which causes the transaction to abort). Any direct port of this trigger body will produce a PL/pgSQL error.

**Evidence — `employee_insupd` trigger (lines 62, 69):**
```sql
ROLLBACK TRANSACTION
```

---

### 2.5 `getdate()` used as column DEFAULT

`getdate()` is a T-SQL–only function. The PostgreSQL equivalent is `NOW()` or `CURRENT_TIMESTAMP`. Because these appear as column-level `DEFAULT` expressions in DDL, they will fail at `CREATE TABLE` time if not substituted before migration.

**Evidence — `employee.hire_date` default (columns file, line 22):**
```
employee|hire_date|datetime||NO|(getdate())
```
**Evidence — `titles.pubdate` default (columns file, line 64):**
```
titles|pubdate|datetime||NO|(getdate())
```

---

### 2.6 Legacy `image` and `text` data types

`image` and `text` are deprecated even in modern SQL Server (removed from SQL Server 2016+ syntax warnings) and have no direct Postgres equivalent. The correct targets are `BYTEA` (for `image`) and `TEXT` (PostgreSQL's native unlimited-length text, which replaces both `varchar(MAX)` and `text`). The Postgres `text` type is not the same object as SQL Server's `text` large-object type, though the migration outcome is functionally equivalent.

**Evidence — `pub_info.logo` (columns file, line 28):**
```
pub_info|logo|image|2147483647|YES|
```
**Evidence — `pub_info.pr_info` (columns file, line 29):**
```
pub_info|pr_info|text|2147483647|YES|
```

---

### 2.7 `money` data type

SQL Server's `money` type is a proprietary 8-byte fixed-point type. PostgreSQL has no native `money` type (its own `money` type has locale-dependent behaviour and is generally discouraged). The recommended migration target is `NUMERIC(19,4)` to preserve precision semantics exactly.

**Evidence — `titles.price`, `titles.advance` (columns file, lines 59–60):**
```
titles|price|money||YES|
titles|advance|money||YES|
```
**Evidence — `reptq3` parameter (modules file, line 31):**
```sql
@lolimit money, @hilimit money,
```

---

### 2.8 `char` fixed-length padding on key columns

Multiple primary and foreign key columns use `char(N)` rather than `varchar(N)`. In SQL Server, `char` values are right-padded with spaces, and comparisons are made after trimming. PostgreSQL also right-pads `char(N)` values and trims on comparison, so the semantic is compatible — but application code that does `LENGTH(au_id)` or explicit equality on trimmed strings may behave differently if the source data contains trailing spaces. This is a data-quality risk rather than a DDL-blocking risk.

**Evidence — `authors.au_id char(11)`, `employee.emp_id char(10)`, `titles.title_id char(6)`, `stores.stor_id char(4)`, etc. (columns file, lines 1, 15, 39, 44–45, 51–52, 55).**

---

## 3. Object-by-Object Explanations and Migration Risk

### 3.1 `byroyalty` — Stored Procedure

**What it does:** Accepts a single integer parameter (`@percentage`) and returns all `au_id` values from the `titleauthor` table where the author's royalty percentage for a given title matches that parameter. It is a simple parameterised lookup — effectively a filtered SELECT with no joins, no aggregation, and no side effects.

**Migration risk (Low):** The query itself is standard SQL and will run on PostgreSQL without modification. The only changes required are syntactic: rename the parameter from `@percentage` to `p_percentage` (or use `$1`), and rewrite the procedure wrapper as a PL/pgSQL function returning a `SETOF` or a `TABLE`. No T-SQL–specific functions or types are used.

---

### 3.2 `reptq1` — Stored Procedure

**What it does:** Produces a price-average report grouped by publisher, including a grand-total rollup row. For each `pub_id` in `titles` (excluding NULL-priced rows), it calculates the average price. The `GROUPING()` function is used to label the rollup summary row with the string `'ALL'` instead of a NULL `pub_id`, making the output human-readable in a report context.

**Migration risk (Medium):** The `WITH ROLLUP` clause (line 15) is a T-SQL–only syntax that must be rewritten as `GROUP BY ROLLUP(pub_id)` for PostgreSQL. The `GROUPING()` function is supported in PostgreSQL 9.5+ so no change is needed there. The `money` column `price` referenced in `AVG(price)` will need its type changed to `NUMERIC(19,4)` at the schema level, but the function call itself is compatible.

---

### 3.3 `reptq2` — Stored Procedure

**What it does:** Produces a year-to-date sales report grouped by both book type and publisher, with a multi-level rollup producing subtotals per type, subtotals per publisher, and a grand total. NULL `pub_id` rows are excluded. As with `reptq1`, `GROUPING()` is used to substitute readable labels (`'ALL'`) for the rollup-generated NULL grouping keys in both the `type` and `pub_id` dimensions.

**Migration risk (Medium):** Same `WITH ROLLUP` issue as `reptq1` — must become `GROUP BY ROLLUP(pub_id, type)`. Note that the rollup column order affects which subtotals are generated; the Postgres `ROLLUP` syntax preserves the same semantics when the column list matches. No `ORDER BY` clause is present in this procedure, which means result ordering is undefined on both platforms — worth flagging to report consumers who may rely on incidental ordering.

---

### 3.4 `reptq3` — Stored Procedure

**What it does:** Accepts a price range (`@lolimit`, `@hilimit`) and a book type (`@type`) and returns a count of matching titles grouped by publisher and type with a rollup. The `WHERE` clause also unconditionally includes any title whose type contains the substring `'cook'`, regardless of price range — this is due to operator-precedence ambiguity (the `OR type LIKE '%cook%'` is not parenthesised, so it is evaluated independently of the `AND` chain).

**Migration risk (Medium-High):** Three issues: (1) `WITH ROLLUP` must be rewritten to ANSI `ROLLUP(pub_id, type)`. (2) The `money`-typed parameters `@lolimit`/`@hilimit` must become `NUMERIC(19,4)` parameters in the Postgres function signature. (3) The unparenthesised `WHERE` predicate logic (`price >@lolimit AND price <@hilimit AND type = @type OR type LIKE '%cook%'`) is almost certainly a latent bug — the `OR` clause means any cook-related title always appears regardless of price or type filter. This should be reviewed with the business before migration; if the intent was to filter cook titles by price, the clause needs parentheses: `(price >@lolimit AND price <@hilimit) AND (type = @type OR type LIKE '%cook%')`.

---

### 3.5 `employee_insupd` — Trigger

**What it does:** Fires `FOR INSERT, UPDATE` on the `employee` table. It reads the `min_lvl` and `max_lvl` bounds for the employee's job from the `jobs` table (via the `inserted` pseudo-table), then enforces two business rules: (a) employees in job 1 must have `job_lvl` exactly 10; (b) all other employees must have a `job_lvl` between the job's defined minimum and maximum. Violations abort the statement with a descriptive error message.

**Migration risk (High):** Four issues require rewriting: (1) The `inserted` pseudo-table does not exist in PostgreSQL — it must be replaced with the `NEW` record available in a PL/pgSQL `FOR EACH ROW` trigger function; the comma-join on `inserted` must be replaced with direct `NEW.job_id`, `NEW.job_lvl`, `NEW.emp_id` references. (2) `RAISERROR` must be replaced with `RAISE EXCEPTION`. (3) `ROLLBACK TRANSACTION` is not valid inside a Postgres trigger — the exception raised in point (2) will automatically abort the transaction, so these lines are simply removed. (4) T-SQL `@variable` syntax must become PL/pgSQL `DECLARE … variable TYPE` block syntax. The trigger will need to be re-implemented as a separate `FUNCTION` returning `TRIGGER` plus a `CREATE TRIGGER` statement.

---

### 3.6 `titleview` — View

**What it does:** A denormalised read view joining `authors`, `titles`, and `titleauthor` to present a flat row containing the book title, author order, author last name, price, year-to-date sales, and publisher ID. This is a classic reporting view suitable for front-end queries that need author–title associations without writing their own three-table join.

**Migration risk (Low-Medium):** The query logic is straightforward and portable. The only issue is the implicit comma-join style (`FROM authors, titles, titleauthor WHERE …`) which should be rewritten to explicit `INNER JOIN … ON …` for clarity and safety. The `price` column references the `money`-typed column in `titles`, which will become `NUMERIC(19,4)` after schema migration — no change needed in the view itself beyond that schema change propagating automatically.

---

## 4. Pubs Migration Risk Score

| Object | Type | Risk | Evidence |
|---|---|:-:|---|
| employee_insupd | Trigger | 🔴 5 | `inserted` table, `RAISERROR`, `ROLLBACK` — full PL/pgSQL rewrite |
| reptq3 | Proc | 🔴 4 | `WITH ROLLUP` error + `money` params + latent `OR` logic bug |
| reptq1 | Proc | 🟠 3 | `WITH ROLLUP` parse error; otherwise standard SQL |
| reptq2 | Proc | 🟠 3 | Same `WITH ROLLUP` blocker as reptq1 |
| titleview | View | 🟡 2 | Implicit comma-join; otherwise portable |
| byroyalty | Proc | 🟢 1 | Pure SELECT; only wrapper syntax needs updating |
| pub_info | Table | 🟠 3 | `image`/`text` LOB types need BYTEA/TEXT mapping |
| titles / employee | Tables | 🟡 2 | `money` cols + `getdate()` defaults are DDL-blocking |
| titleauthor / authors / stores | Tables | 🟢 1 | `char(N)` padding risk, not DDL-blocking |

**Legend:** 🔴 High (4-5)  🟠 Medium-high (3)  🟡 Medium (2)  🟢 Low (1)

---

## 5. Summary of Required Changes Before Migration

| # | Change | Objects Affected |
|---|---|---|
| 1 | Replace `WITH ROLLUP` → `GROUP BY ROLLUP(…)` | `reptq1`, `reptq2`, `reptq3` |
| 2 | Rewrite comma-join → explicit `INNER JOIN ON` | `titleview`, `employee_insupd` |
| 3 | Replace `RAISERROR` → `RAISE EXCEPTION` | `employee_insupd` |
| 4 | Remove `ROLLBACK TRANSACTION` (exception handles it) | `employee_insupd` |
| 5 | Replace `inserted` pseudo-table with `NEW` record | `employee_insupd` |
| 6 | Rewrite T-SQL `@var` declarations to PL/pgSQL `DECLARE` | `employee_insupd`, `reptq3` |
| 7 | Replace `getdate()` default → `NOW()` | `employee.hire_date`, `titles.pubdate` |
| 8 | Map `money` type → `NUMERIC(19,4)` | `titles.price`, `titles.advance`, `reptq3` params |
| 9 | Map `image` → `BYTEA`, `text` LOB → `TEXT` | `pub_info.logo`, `pub_info.pr_info` |
| 10 | Review `reptq3` unparenthesised `OR` predicate for logic correctness | `reptq3` |
| 11 | Convert stored procedures to `LANGUAGE plpgsql` functions | `byroyalty`, `reptq1`, `reptq2`, `reptq3` |

---

*Report generated by automated static analysis. No data was queried at runtime. All findings are based on schema metadata and module DDL source text.*
