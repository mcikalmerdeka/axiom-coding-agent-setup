---
name: building-metabase-dashboards
description: Use when building, bulk-provisioning, filtering, versioning, or backing up the Airbnb Berlin Metabase dashboards, including collections, native SQL cards, Field Filters, dashboard filters, API seeding, Git-friendly JSON export, and application-database backup/restore.
compatibility: Requires a running Metabase 0.64+ connected to PostgreSQL. Provisioning and export need an admin API key. Docker/PostgreSQL installation and ETL are out of scope; application-database backup is in scope.
metadata:
  author: axiom
  version: "2.0"
---

# Building Metabase Dashboards

## Overview

Build and persist Metabase work in three phases:

1. **Design** — an analysis-ready table/model with a known grain and filter columns.
2. **Provision** — collections, saved questions, dashboards, and filters.
3. **Persist** — Git-friendly JSON export and an exact application-database backup.

Use the manual UI for one dashboard or exploratory work. Use the API seeder for
multi-dashboard builds, reruns, and repeatable delivery. Export after every
definition change; back up before upgrades, resets, and bulk writes.

The bundled references use the Airbnb Berlin project as the single worked
example: 5 dashboards, 66 cards, the `analytics` schema, and the full filter
map. The API and persistence references use the same project.

Assume Metabase and the database are running. **Do not include Docker,
PostgreSQL installation, or ETL setup in the plan.** Application-database backup
is in scope; installing the database is not.

UI labels in this skill are from Metabase 0.64.x. Newer versions may rename
controls, but the concepts (Field Filter, variable mapping, dashboard filter
type) are the same.

## When to use

Use this skill when:

- The user wants a new Metabase dashboard, KPI row, chart set, or detail table.
- The user needs many collections, questions, or dashboards created repeatedly.
- An existing Metabase dashboard needs filters that work across multiple cards.
- A native SQL card shows `A text variable in this card can only be connected...`.
- A native SQL card shows `Cannot run the query: missing required parameters`.
- A native SQL card shows `argument of AND must be type boolean`.
- The user needs to save, version, export, or back up Metabase content.
- The user needs an exact restore path for the Metabase application database.

Do not use this skill for Docker/PostgreSQL setup, data cleaning, ETL, or
database schema design. Application-database backup/restore is in scope.

## Preconditions

- Metabase is running and reachable.
- The database connection already exists in Metabase.
- An analysis-ready table or model exists.
- You know the table grain (for example, one row per listing, host, or review).
- You know which columns should become filters and whether they are text,
  category, boolean, number, or date fields.
- For the API path: an API key in the Administrators group, and a project
  `.env` with `METABASE_URL=http://127.0.0.1:3000` and `METABASE_API_KEY`.
  Never commit `.env`.
- For an exact backup: the Metabase application database runs on PostgreSQL or
  MySQL, not embedded H2.
- Ask owners to save in-progress editor drafts; the API cannot see unsaved work.

## Choose the path

| Situation | Path | Where |
| --- | --- | --- |
| One dashboard, few cards, exploratory | Manual UI + query builder | This file |
| Many collections/dashboards, repeatable build | API seeder + definitions JSON | [API provisioning](references/metabase-api-provisioning.md) |
| Complex SQL | Native SQL + Field Filters | This file + [SQL reference](references/dashboard-sql-with-filters.md) |
| Save definitions to Git | JSON export | [Export and backup](references/metabase-export-and-backup.md) |
| Exact restore of users/settings/dashboards | Application DB dump | [Export and backup](references/metabase-export-and-backup.md) |
| Native YAML import/export | Pro/Enterprise serialization | [Export and backup](references/metabase-export-and-backup.md) |

Do not API-seed a single exploratory card. Do not hand-build 66 cards in the UI
when the inventory is already documented.

## First decision: query builder or native SQL

| Need | Build with | How dashboard filters attach |
| --- | --- | --- |
| Simple count, average, group-by, filter | Query builder on the model | Map the filter directly to the column |
| `CROSS JOIN LATERAL`, CTEs, window functions, complex SQL | Native SQL | Add one **Field Filter** variable per filter and map to the variable |
| Mixed dashboard | Query builder for simple cards; native SQL only where needed | Keep filter names and types consistent |

Prefer the query builder for simple entity-level cards. Native SQL is not a
shortcut for filters: it makes filters harder because every card needs its own
variables. The bundled API seeder creates native SQL cards only; create
query-builder cards in the UI or extend the seeder with MBQL.

The Airbnb project uses a star schema and pre-aggregated marts. Prefer the
listing/host/review models for filterable cards; use the marts for
pre-aggregated benchmarks. The full source map is in
[Dashboard Build Guide](references/dashboard-build-guide.md).

## Build sequence

1. **Inspect the schema.** Confirm the grain, key columns, filter columns, and
   expected unfiltered totals.
2. **Choose the path.** Manual UI for one dashboard; API seeder for a repeatable
   multi-dashboard build. Use the table above.
3. **Create the collection/model.** Point the model at the analysis-ready table;
   give it a clear name and description.
4. **Plan the card inventory.** KPI row, then demographics, usage,
   engagement/popularity, and the detail table.
5. **Build and save questions** in the collection. Use `KPI - ...`,
   `Chart - ...`, `Table - ...`.
6. **Create the dashboard** and add saved questions in section order.
7. **Add dashboard filters** and map each filter to every card that should
   respond. Use `scripts/add_dashboard_filters.py` for the API pass, or the UI
   for exploratory work. Leave a card unmapped when filtering changes its
   meaning.
8. **Format** numbers, legends, sorting, colors, and table columns.
9. **Run QA** with no filters, each filter individually, and after clearing.
10. **Export the definitions** to JSON and commit them.
11. **Back up the application database** at milestones and before resets.

## Bulk API path

Use this when the inventory has more than a handful of cards, or when the build
must be repeatable. The sources of truth are `metabase/definitions.json` (cards
and dashboards) and `metabase/dashboard_filters.json` (dashboard filters). The
bundled seeder creates/adopts collections, cards, and dashboards; the filter
script adds and maps the dashboard parameters.

Scaffold a new project (creates `scripts/`, `metabase/README.md`,
`metabase/.gitignore`, `metabase/definitions.json`,
`metabase/dashboard_filters.json`, and the export/backup folders):

```powershell
uv run python .agents\skills\building-metabase-dashboards\scripts\scaffold_metabase.py --target "C:\path\to\project"
```

The commands below assume the scaffold has created `scripts/` in the target
project. Then fill in both definitions files and run:

```powershell
uv run python scripts\seed_metabase.py --definitions metabase\definitions.json --dry-run
uv run python scripts\seed_metabase.py --definitions metabase\definitions.json --dashboard supply
uv run python scripts\seed_metabase.py --definitions metabase\definitions.json

uv run python scripts\add_dashboard_filters.py --definitions metabase\dashboard_filters.json --dry-run
uv run python scripts\add_dashboard_filters.py --definitions metabase\dashboard_filters.json --dashboard supply
uv run python scripts\add_dashboard_filters.py --definitions metabase\dashboard_filters.json
```

Rules:

- The API key must be in `.env`; never in the definitions file.
- The bundled seeder creates native SQL cards. Create query-builder cards in
  the UI, or extend the definitions schema with MBQL.
- Resolve `schema.table.column` to numeric field IDs from
  `GET /api/database/{id}/metadata`. Field IDs are instance-local.
- Native SQL cards use `WHERE {{filter}}` Field Filter tags, never
  `column = {{filter}}` or quoted variables.
- Match by exact name within a collection. Use `aliases` to adopt partial work;
  never create a duplicate.
- New dashcards use negative IDs. Existing dashcards keep their IDs, mappings,
  and visualization settings.
- Preserve unrelated cards and dashboard parameters; do not rewrite a completed
  dashboard.
- Run `scripts/add_dashboard_filters.py` after seeding to create and map
  dashboard filters. The seeder leaves filters to that pass.
- `--relayout` resets the grid; use it only when intended.
- On Windows, use `127.0.0.1`; Python's `localhost` can add ~2s per request.

Full payloads, definitions schema, filter schema, and adoption rules:
[Metabase API provisioning](references/metabase-api-provisioning.md).

### Dashboard filter pass

`metabase/dashboard_filters.json` maps one dashboard filter per template-tag
name. Each filter needs `name`, `slug`, `tag`, and `type`; optional keys are
`section_id`, `values_query_type`, `is_multi`, `expected_cards`,
`exclude_cards`, and `default`. The script maps the filter to every card that
exposes the tag, preserves unrelated parameters/mappings/layout/tabs, and is
idempotent by slug. `expected_cards` is an optional drift guard. Field Filters
use the three-element dimension target; plain Text tags use the two-element
variable target.

Schema: [`assets/dashboard_filters.example.json`](assets/dashboard_filters.example.json).
Detailed payloads and gotchas:
[Metabase API provisioning](references/metabase-api-provisioning.md#dashboard-filters).

## Save, export, and restore

| Need | Artifact | Commit? | Restores Metabase? |
| --- | --- | --- | --- |
| Review/version dashboard definitions | JSON export | Yes | No |
| Exact restore after upgrade/deletion | App DB dump | **No** | Yes |
| Native YAML import | Pro/Enterprise serialization | Yes | Yes (paid) |

```powershell
uv run python scripts\export_metabase.py --collection-id 5
.\scripts\backup_metabase.ps1
.\scripts\restore_metabase.ps1 -DumpFile .\metabase\backups\metabase_20261106_142757.dump
```

- The JSON export strips users, secrets, timestamps, and query metadata.
- The dump contains users, password hashes, settings, and sessions. Keep it
  private and gitignored.
- Test a dump by restoring into a scratch database before relying on it.
- Commit the JSON export and definitions; ignore `.env` and `*.dump`.
- Metabase's native serialization is Pro/Enterprise only; the OSS image uses JSON
  export + app DB dump.

Full persistence model, sizes, restore drill, and security:
[Metabase export and backup](references/metabase-export-and-backup.md).

## Card inventory

The project has five dashboards and 66 saved questions. The full card list,
descriptions, expected values, and layout for each dashboard are in the
[Dashboard Build Guide](references/dashboard-build-guide.md).

| # | Dashboard | Cards | Primary sources |
| ---: | --- | ---: | --- |
| 1 | Executive Overview | 14 | `dim_listings`, `dim_hosts`, `fct_reviews`, `mart_executive_kpis`, `mart_market_monthly` |
| 2 | Supply and Pricing | 13 | `mart_listing_performance`, `mart_price_bands`, `mart_room_type_benchmark` |
| 3 | Guest Experience | 14 | `fct_reviews`, `mart_review_topics`, `mart_market_monthly` |
| 4 | Host Portfolio | 13 | `mart_host_performance`, `dim_hosts` |
| 5 | Listing Explorer | 12 | `mart_listing_performance` |

Use the `KPI - ...`, `Chart - ...`, and `Table - ...` prefixes. Put each
dashboard's questions in its own subcollection under `Airbnb Analytics`. Names
repeat across dashboards, so the **Description** field is what distinguishes
them.

`Model - Listings` is the query-builder model over
`analytics.mart_listing_performance`. Native SQL cards may read
`analytics.dim_listings` directly where the build guide says so; both paths are
valid and must produce the same expected totals. Native SQL cannot read a
Metabase model, so it uses the underlying table.

Every question needs a description that states the measure and the grain. Use
the per-dashboard question-description tables in the build guide.

## Dashboard layout

The project uses a 24-column grid:

- 5 KPI cards on row 1: widths `5, 5, 5, 5, 4`, height 3.
- Two charts per row: width 12, height 6.
- Full-width trends and tables: width 24, height 6-8.
- Tables: width 24, height 7.

The exact per-dashboard layout is in the build guide. Use **Text cards** for
section headings only when the dashboard needs them.

## Native SQL filter recipe

Use this only when the card must stay as native SQL. Every card that should
respond to a dashboard filter needs the filter variable in its SQL.

### Worked example: Supply and Pricing filters

| Dashboard filter | Filter type | Column |
| --- | --- | --- |
| Room type | Text or Category | `room_type` |
| Price band | Text or Category | `price_band` |
| Minimum nights band | Text or Category | `minimum_nights_band` |
| Superhost | Boolean | `is_superhost` |
| Price range | Number | `price` |

### SQL block

Add the filters to the `WHERE` clause of every native SQL card:

```sql
SELECT COUNT(*) AS total_listings
FROM analytics.dim_listings
WHERE {{room_type}}
  AND {{price_band}}
  AND {{minimum_nights_band}}
  AND {{is_superhost}}
  AND {{price}};
```

Notes:

- Use `WHERE {{room_type}}`, **not** `WHERE room_type = {{room_type}}`. A Field
  Filter inserts the column, operator, and value handling.
- Field Filters are optional by default. `AND {{room_type}}` is enough.
- Do not use `'{{room_type}}'` or wrap the variable in quotes.
- The filter's field must belong to a table present in the query. For a card on
  a mart, map to the mart's own column.
- Map only the filters the card exposes. The SQL reference has a per-card
  availability table for every dashboard.

### Variable settings

For each variable in the Metabase **Variables** panel:

| Variable | Variable type | Field to map to | Widget type |
| --- | --- | --- | --- |
| `{{room_type}}` | Field Filter | `analytics.dim_listings.room_type` | Category / Dropdown list |
| `{{price_band}}` | Field Filter | `analytics.dim_listings.price_band` | Category / Dropdown list |
| `{{minimum_nights_band}}` | Field Filter | `analytics.dim_listings.minimum_nights_band` | Category / Dropdown list |
| `{{is_superhost}}` | Field Filter | `analytics.dim_listings.is_superhost` | Boolean |
| `{{price}}` | Field Filter | `analytics.dim_listings.price` | Number |

**Critical:** typing `{{room_type}}` creates a template tag, but Metabase often
defaults it to **Text**. Change the variable type to **Field Filter**, choose
the matching field, and turn **Always require a value** off if the question
should run with no filters selected. Save the question before mapping it on a
dashboard.

### Dashboard filter settings

| Dashboard filter | Filter type | Maps to variable |
| --- | --- | --- |
| Room type | Text or Category | `room_type` |
| Price band | Text or Category | `price_band` |
| Minimum nights band | Text or Category | `minimum_nights_band` |
| Superhost | Boolean | `is_superhost` |
| Price range | Number | `price` |

For text filters, keep **Filter operator: Is**. For the text filters, choose
**Multiple values** if multi-select is wanted. Boolean filters are typically
single-value (True/False).

### Mapping steps

1. Edit the dashboard.
2. Add the filter with the correct type.
3. For each card, choose the matching variable or column.
4. Save the dashboard.
5. Test the filter and clear it.

A filter only affects cards where it is mapped. If a native SQL card has no
matching variable, it cannot be mapped and will ignore the filter.

## Aliases and CTEs

- The filterable SQL in this project avoids table aliases wherever possible.
- The one joined card is Guest Experience `Chart - Reviews by Room Type`:
  `analytics.fct_reviews AS r` joined to `analytics.dim_listings AS l`.
  Set **Table and field alias** for each filter: `r.review_date`,
  `r.review_sentiment`, `r.has_comment`, and `l.room_type`.
- If you add a join, apply the same rule: alias plus column.
- If a card's source does not contain the filter field, join the table or leave
  the card unfiltered. Do not map a field from a table that is not in the query.
- The API seeder prefers unaliased SQL; if a definition includes a join, use the
  alias form or rewrite the SQL unaliased.

## Common mistakes

- Converting a simple query-builder card to native SQL, then having to configure
  many variables. Use the query builder unless the SQL is genuinely complex.
- Leaving `{{room_type}}` as a **Text** variable. It must be a **Field Filter**
  mapped to the field.
- Using Text or Category dashboard filters for boolean columns. Use **Boolean**.
- Forgetting the filter pass. The seeder creates cards and dashboards only; run
  `scripts/add_dashboard_filters.py` to create the dashboard parameters.
- Mapping a Text variable with a dimension target. Use
  `["variable", ["template-tag", "tag"]]` with exactly two elements.
- Setting a Boolean filter to `string/=` or `sectionId: "string"`. Use
  `boolean/=` and `sectionId: "boolean"`.
- Sending `dashcards` to `PUT /api/dashboard` without the existing `tabs`,
  unrelated mappings, or layout. GET the full dashboard and reconcile.
- Assuming a category value's casing. Read the values endpoint; the stored
  values may be lowercase.
- Mapping a filter to only some cards. Map it to every card that should respond.
- Writing `room_type = {{room_type}}` for a Field Filter. Use
  `WHERE {{room_type}}`.
- Assuming a dashboard filter will apply to a card that has no matching
  variable. It will not.
- Mapping a filter to a mart card that does not expose that column. Check the
  per-card availability table in the SQL reference first.
- Bulk-seeding without a recent application-database backup. Take one before
  the first write and before a rerun that updates existing cards.
- Hardcoding field IDs and reusing them across Metabase instances. Field IDs are
  instance-local; resolve them from `/api/database/{id}/metadata`.
- Matching cards by name globally. Match by name **within the target
  collection**, and use `aliases` for partial work.
- Creating new dashboard cards with positive IDs. Use negative IDs for new
  dashcards and real IDs for existing ones.
- Rewriting a completed dashboard. Skip it with `"skip": true` and preserve
  unrelated cards, parameters, and filter mappings.
- Committing `.env`, the API key, or `metabase/backups/*.dump` to Git.
- Assuming Metabase OSS has native YAML serialization. It is Pro/Enterprise.
- Editing generated JSON export files by hand; the next export replaces them.
- Treating the JSON export as a restorable backup. Use the application DB dump.
- Using `localhost` in Python scripts on Windows; every request can take ~2s.
  Use `127.0.0.1`.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `A text variable in this card can only be connected to a text filter with Is operator` | The card has no mappable variable, or the variable is still Text | Add the `{{...}}` tag, set type to **Field Filter**, map the field |
| `Cannot run the query: missing required parameters` | Variables are Text, or **Always require a value** is on | Change to **Field Filter**, map fields, turn off **Always require a value** |
| `argument of AND must be type boolean, not type character varying` | A Text variable was used where a Field Filter was needed; a value was substituted as `AND 'Entire home/apt'` | Change the variable to **Field Filter** and map it |
| `operator does not exist: boolean = character varying` | Text/Category dashboard filter connected to a boolean column | Change the dashboard filter to **Boolean** |
| Field Filter does not appear in the dashboard mapping panel | Question not saved, or dashboard editor is stale | Save the question, reload the dashboard editor |
| Filter changes one card but not another | Other card lacks the matching variable or mapping | Add the variable to that card and map the filter |
| `column ... does not exist` | Field Filter mapped to the wrong field, or alias setting missing | Correct the field mapping or table/field alias |
| Filter works in the question but not on the dashboard | The dashboard filter is not connected to the card | Map the dashboard filter to the card's variable |
| Filter returns 0 rows unexpectedly | Value casing/spacing differs from stored data | Read the values endpoint; use the exact stored value |
| `vector with exactly 2 items` | A `stage-number` was added to a variable target | Use `["variable", ["template-tag", "tag"]]` |
| Filter pass wipes layout or mappings | PUT omitted dashcards, tabs, or unrelated mappings | GET the full dashboard and resend everything |

For the full error explanations and parameter behavior, read
[Metabase Parameter Types Reference](references/Metabase_Parameter_Types_Reference.md).

## Visualization and formatting

- **KPI cards:** one row, equal width, no unnecessary decimals.
- **Pie charts:** room type or sentiment; show the legend and percentage labels.
- **Bar charts:** sort popularity descending. Keep the explicit order for price
  bands (`<30`, `30-49`, ...) and minimum-night bands (`1`, `2-6`, ...), not
  alphabetical.
- **Line charts:** month on the X-axis; reviews, sentiment, or share on the Y;
  room type or sentiment as the series breakout. Cap review trends at
  `2021-10-01`.
- **Tables:** listing and host detail; hide technical IDs, set a row limit, and
  enable downloads where useful.
- Add a short description to each saved question explaining what it measures.

## QA checklist

- [ ] `KPI - Total Listings` = `17,499`.
- [ ] `KPI - Total Hosts` = `14,111`.
- [ ] `KPI - Total Reviews` = `410,283`.
- [ ] Room type counts sum to `17,499`.
- [ ] Sentiment counts sum to `410,283`.
- [ ] Price band counts sum to `17,499`.
- [ ] Host segment counts on the host dashboard sum to `14,111`.
- [ ] Listing-grain host segment counts sum to `17,499`.
- [ ] Topic mentions total `588,037` (not unique reviews).
- [ ] Every filter changes its intended cards and can be cleared.
- [ ] Filter dry-run reports the documented parameter and mapping counts.
- [ ] A second filter dry-run reports every filter as existing.
- [ ] Every category filter returns dropdown values; every boolean/date/number
  filter returns rows for a representative value.
- [ ] No filter mapping references a tag that does not exist on its card.
- [ ] No card shows an error or an unexpected empty result.
- [ ] All five dashboards are saved under `Airbnb Analytics`.
- [ ] A second seeder `--dry-run` reports every card and dashboard as existing.
- [ ] Representative KPI/chart/table cards execute and match expected values.
- [ ] The export manifest counts match the collections/cards/dashboards.
- [ ] No email, API key, password, or `public_uuid` appears in the export.
- [ ] `.env` and `*.dump` are gitignored and not staged.
- [ ] A dump restores into a scratch database and Metabase reports healthy.

For the Airbnb Berlin worked example, the key unfiltered values are:

- Total Listings: `17,499`
- Total Hosts: `14,111`
- Total Reviews: `410,283`
- Active Listings (12m): `6,050`
- Avg Nightly Price: `70.41` (median `55`)
- Positive Review Share: `56.68%`
- Negative Review Share: `7.33%`
- Total Topic Mentions: `588,037`

## Reusing this project's pattern

1. Keep the five dashboard collections and the 66-card inventory as the contract.
2. Reuse the models: `Model - Listings`, `Model - Hosts`, `Model - Reviews`,
   and `Model - Reviews with listing attributes`.
3. Build the KPI, supply, guest, host, and listing cards in that order.
4. Prefer the query builder for simple cards; use native SQL for complex cards.
5. Use the same filter names and dashboard filter types across dashboards.
6. Map every filter to every intended card; leave semantically incompatible
   cards unmapped.
7. Run QA unfiltered, with each filter, and after clearing.
8. Export the definitions and back up the application database.

## Shortcuts and limits

- Metabase has no built-in **copy variables** button.
- A practical UI shortcut: configure one native SQL card correctly, duplicate
  it, replace only the SQL with the next card's query, and verify the Field
  Filter settings persist in the duplicate. Test with one duplicate first.
- The query builder is the best shortcut for simple cards because filters map
  directly to columns with no SQL variables.
- For multi-dashboard builds, the API seeder is the normal path. Create one
  golden card for each display/filter shape, export its JSON, and use that
  structure in the definitions file.
- For more than a handful of filters, use the filter script instead of the UI.
  It reconciles parameters and mappings from a JSON file and is idempotent.
- Do not force a filter onto a card where it changes the meaning of the card.
  It is valid to leave some cards unfiltered.
- Do not run a bulk API update without an application-database backup and a
  `--dry-run` plan.

## References

Read the relevant reference before building. The first three are the manual
UI/parameter references; the last two cover the API and persistence paths.

- [Dashboard Build Guide](references/dashboard-build-guide.md) — Airbnb Berlin
  manual build guide: five dashboards, 66 cards, question descriptions, expected
  values, layouts, filters, and gotchas.
- [Dashboard SQL with Field Filters](references/dashboard-sql-with-filters.md) —
  Airbnb native SQL for all 66 cards: per-dashboard variables, per-card filter
  availability, alias settings, troubleshooting, and verification.
- [Metabase Parameter Types Reference](references/Metabase_Parameter_Types_Reference.md) —
  basic variables, optional variables, Field Filters, aliases, boolean fields,
  and exact error explanations, using Airbnb examples.
- [Metabase API Provisioning](references/metabase-api-provisioning.md) —
  definitions schema, field-ID resolution, native SQL tags, collections, cards,
  dashboards, dashcards, filter schema and parameter mappings, idempotency,
  troubleshooting.
- [Metabase Export and Backup](references/metabase-export-and-backup.md) —
  JSON export, application-database dump/restore, Pro serialization, Git
  hygiene, restore drills, security.

Bundled tools:

- `scripts/scaffold_metabase.py` — create the `scripts/` + `metabase/` project
  structure and starter definitions.
- `scripts/seed_metabase.py` — idempotent API seeder for collections, cards,
  and dashboards.
- `scripts/add_dashboard_filters.py` — idempotent API filter pass for dashboard
  parameters and dashcard mappings.
- `scripts/export_metabase.py` — Git-friendly JSON export.
- `scripts/backup_metabase.ps1` / `scripts/restore_metabase.ps1` — exact app DB
  backup and restore.
- `assets/definitions.example.json` — card/dashboard definitions schema.
- `assets/dashboard_filters.example.json` — dashboard filter schema, with the
  full Airbnb filter map.

Maintenance: the first two references mirror the Airbnb
`Postgres Version/docs/METABASE_DASHBOARDS.md` and
`METABASE_SQL_WITH_FILTERS.md` files; re-copy them if those change. The
parameter reference uses Airbnb examples; the API and persistence references
are skill-owned and should be updated when the API payloads change. The filter
example mirrors `Postgres Version/metabase/dashboard_filters.json`.
