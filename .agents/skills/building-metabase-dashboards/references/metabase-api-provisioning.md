# Metabase API Provisioning

Create Metabase collections, questions, dashboards, and optional filters through
the HTTP API. Use this path for multi-dashboard builds, repeatable delivery, and
reruns. Use the UI for one dashboard or exploratory work.

Tested against Metabase **0.64.x**. The API is not versioned; pin the Metabase
image and re-verify the payload shapes after an upgrade.

## Scaffold a new project

The bundled `scripts/scaffold_metabase.py` creates the project structure. Run it
from the skill directory, targeting the project root:

```powershell
uv run python .agents\skills\building-metabase-dashboards\scripts\scaffold_metabase.py --target "C:\path\to\project"
```

It writes:

```text
scripts/seed_metabase.py
scripts/export_metabase.py
scripts/backup_metabase.ps1
scripts/restore_metabase.ps1
metabase/README.md
metabase/.gitignore
metabase/definitions.json      # placeholder IDs; edit before use
metabase/backups/.gitkeep
metabase/export/.gitkeep
```

It skips existing files unless `--force` is passed. The starter
`definitions.json` uses a root collection **name** and a database **name**, and
resolves field IDs from live metadata at seed time. No instance-local IDs need
to be committed.

## Preconditions

- Metabase is running and connected to the analytics database (PostgreSQL or
  BigQuery; see [`bigquery-workspace.md`](bigquery-workspace.md)).
- An analysis-ready table/model exists with a known grain.
- You have an **API key** in the Administrators group.
- The project `.env` contains:

```dotenv
METABASE_URL=http://127.0.0.1:3000
METABASE_API_KEY=mb_...
```

Use `127.0.0.1`, not `localhost`, in scripts. On Windows, Python resolves
`localhost` to IPv6 first and falls back to IPv4, adding about two seconds per
request. The browser can still use `localhost`.

Never commit `.env`, the API key, or an application-database dump.

## 1. Create the API key

1. Metabase → **Admin** → **Settings** → **Authentication** → **API Keys**.
2. **Create API Key**, name it for the automation (`seed-export`), and assign
   the **Administrators** group.
3. Copy the key into `.env`.

The key has the permissions of its group. Use a dedicated key so it can be
rotated without changing a user password.

## 2. Discover the IDs

Everything in Metabase is ID-based. Collect these before writing definitions.

| Need | Endpoint |
| --- | --- |
| Databases | `GET /api/database` |
| Tables and fields for a database | `GET /api/database/{database-id}/metadata` |
| Collection tree | `GET /api/collection/tree` |
| Items in a collection | `GET /api/collection/{id}/items?models=collection&models=card&models=dashboard` |
| A card | `GET /api/card/{id}` |
| A dashboard | `GET /api/dashboard/{id}` |

Build a map of `schema.table.column` → `field_id`. Field Filters need the
numeric field ID at API time, but definitions should store the stable
`schema.table.column` string and let the seeder resolve the current ID.

```text
analytics.dim_listings.room_type      -> 95
analytics.dim_listings.price          -> 96
analytics.dim_listings.price_band     -> 97
analytics.fct_reviews.review_date     -> 113
analytics.mart_executive_kpis.month_start -> 122
```

The database is also instance-local. Store its **name** (for example
`Airbnb Analytics`) in the definitions and have the seeder look up the numeric
`dataset_query.database` ID at runtime.

## 3. Definitions file

Use one JSON file as the source of truth for the build. The seeder reads it; do
not edit generated metadata by hand.

```json
{
  "root_collection_name": "Airbnb Analytics",
  "database_name": "Airbnb Analytics",
  "dashboards": [
    {
      "key": "supply",
      "collection": "Supply and Pricing Collection",
      "dashboard": "Supply and Pricing Dashboard",
      "description": "Price distribution, room-type benchmarks, minimum-night segments, and superhost pricing comparisons.",
      "skip": false,
      "cards": [
        {
          "key": "2.1",
          "name": "KPI - Total Listings",
          "description": "Count of listings in the current snapshot. One row per listing.",
          "display": "scalar",
          "sql": "SELECT COUNT(*) AS total_listings FROM analytics.dim_listings",
          "tags": [],
          "aliases": [],
          "visualization_settings": {},
          "full_width": false
        }
      ]
    }
  ]
}
```

A complete filtered example with tags, aliases, and visualization settings is
in [`assets/definitions.example.json`](../assets/definitions.example.json).

A companion file, `metabase/dashboard_filters.json`, defines dashboard-level
filters and their tag mappings. Its schema is in
[`assets/dashboard_filters.example.json`](../assets/dashboard_filters.example.json);
`scripts/add_dashboard_filters.py` consumes it.

### Field meanings

| Field | Meaning |
| --- | --- |
| `root_collection_name` | Existing top-level collection; its children are the dashboard collections |
| `database_name` | Metabase database name; resolved to an ID at seed time |
| `skip` | `true` for a dashboard that is already complete and must not be touched |
| `key` | Stable internal key for logging and filtering |
| `collection` | Child collection name; created under the root if missing |
| `dashboard` | Dashboard name; created in the collection if missing |
| `cards[].display` | `scalar`, `line`, `bar`, `pie`, `table`, `scatter` |
| `cards[].tags` | Field Filter template tags (see below) |
| `cards[].aliases` | Legacy names to adopt and rename, avoiding duplicates |
| `cards[].full_width` | `true` for a 24-column card; otherwise charts are 12 columns |
| `visualization_settings` | Metabase viz settings, e.g. `graph.dimensions` |

### Tag shape

```json
{
  "name": "room_type",
  "field": "analytics.dim_listings.room_type",
  "alias": "dim_listings.room_type",
  "widget_type": "string/=",
  "display_name": "Room Type"
}
```

- The SQL must contain `{{room_type}}` in a `WHERE` clause.
- `field` is stable and instance-independent; the seeder resolves it to a field
  ID from `GET /api/database/{id}/metadata`.
- `alias` is optional on PostgreSQL, but **required on BigQuery**: SQL must use
  `FROM analytics.dim_listings AS dim_listings` and the alias must be the full
  `dim_listings.room_type`.
- `widget_type`: `string/=`, `boolean/=`, `number/=`, or `date/all-options`.
- For a joined card, map each tag to the correct source field; a tag named
  `room_type` may belong to the joined dimension, not the fact table.

### Display mapping

| Inventory label | Metabase `display` |
| --- | --- |
| Number | `scalar` |
| Line | `line` |
| Bar / stacked bar | `bar` |
| Pie | `pie` |
| Table | `table` |
| Scatter | `scatter` |
| Histogram | `bar` (choose the histogram view in the UI) |

### Basic visualization settings

```json
{"graph.dimensions": ["month_start"], "graph.metrics": ["reviews"]}
{"graph.dimensions": ["month_start", "room_type"], "graph.metrics": ["reviews"]}
{"pie.dimension": "review_sentiment", "pie.metric": "reviews"}
{"graph.dimensions": ["price"], "graph.metrics": ["review_count"]}
```

`graph.dimensions` holds the X-axis plus any series breakout; `graph.metrics`
holds the numeric measure.

## 4. Validate before calling the API

1. Run every SQL block directly in the database; confirm column names, row
   counts, and expected values.
2. Check every `{{tag}}` in the SQL has a matching tag entry, and vice versa.
3. Remove optional text-search blocks (`[[AND LOWER(...) LIKE ...]]`) unless you
   also create a plain Text template tag. A Text tag is not a Field Filter.
4. Confirm every `field` reference resolves and belongs to the query's source
   table; on BigQuery confirm every tag has an `alias`.
5. Check for duplicate question names across dashboards. Matching is by name
   within a collection; duplicate names in different collections are fine.

## 5. Run the seeder

The bundled `scripts/seed_metabase.py` is idempotent:

```powershell
# Preview every action; no writes
uv run python scripts\seed_metabase.py --definitions path\to\definitions.json --dry-run

# Create one dashboard
uv run python scripts\seed_metabase.py --definitions ... --dashboard supply

# Create everything not marked skip
uv run python scripts\seed_metabase.py --definitions ...

# Reposition all cards to the generated grid
uv run python scripts\seed_metabase.py --definitions ... --dashboard supply --relayout
```

Behavior:

- Resolves the database by `database_name` and the root collection by
  `root_collection_name`.
- Finds a collection by name under the root; creates it if missing.
- Finds a card by target name in the collection; reuses it and updates its SQL
  or tags when the definition changed.
- If not found, checks each alias; adopts the first match and renames it.
- Creates missing cards with native SQL and Field Filter tags; resolves every
  `field` reference from live metadata and applies the tag `alias`.
- Finds a dashboard by name; creates it if missing.
- Adds missing cards to the dashboard; preserves extra cards, dashboard
  parameters, tabs, and existing filter mappings.
- If every target card is already on the dashboard, leaves the layout alone
  unless `--relayout` is passed.
- Skips dashboards with `"skip": true`.
- Does not create or map dashboard filters. Cards are built filter-ready; run
  `scripts/add_dashboard_filters.py` in a second pass.

## 6. API mechanics

### Collections

```http
POST /api/collection
{"name": "Supply and Pricing Collection", "description": "...", "parent_id": 5}
```

### Cards

The bundled seeder creates **native SQL cards only**. Query-builder cards need
MBQL (`source-table`, `aggregation`, `breakout`, filters) and are a manual
exception or a seeder extension.

```http
POST /api/card
{
  "name": "KPI - Total Listings",
  "description": "Count of listings. One row per listing.",
  "collection_id": 7,
  "display": "scalar",
  "dataset_query": { ... },
  "visualization_settings": {},
  "parameters": [],
  "type": "question"
}
```

Native dataset query for 0.64:

```json
{
  "database": 2,
  "lib/type": "mbql/query",
  "stages": [
    {
      "lib/type": "mbql.stage/native",
      "native": "SELECT COUNT(*) AS total_listings FROM analytics.dim_listings AS dim_listings",
      "template-tags": []
    }
  ]
}
```

Field Filter tag:

```json
{
  "id": "00000000-0000-0000-0000-000000000000",
  "type": "dimension",
  "widget-type": "string/=",
  "name": "room_type",
  "display-name": "Room Type",
  "dimension": ["field", {"lib/uuid": "11111111-1111-1111-1111-111111111111"}, 95],
  "alias": "dim_listings.room_type"
}
```

The numeric `95` is resolved from the live field map at seed time. The `alias`
is optional on PostgreSQL but required for BigQuery.

The card's `parameters` array mirrors each tag:

```json
{
  "id": "00000000-0000-0000-0000-000000000000",
  "type": "string/=",
  "target": ["dimension", ["template-tag", "room_type"]],
  "name": "Room Type",
  "slug": "room_type",
  "isMultiSelect": true
}
```

Use a fresh UUID for each tag. The `id` must match between the template tag and
the parameter entry.

### Dashboards

```http
POST /api/dashboard
{"name": "Supply and Pricing Dashboard", "description": "...", "collection_id": 7, "parameters": []}
```

### Dashcards and layout

Add or update cards with a full `dashcards` list:

```http
PUT /api/dashboard/3
{
  "dashcards": [
    {
      "id": -1,
      "card_id": 40,
      "row": 0,
      "col": 0,
      "size_x": 5,
      "size_y": 3,
      "parameter_mappings": [],
      "visualization_settings": {},
      "inline_parameters": []
    }
  ],
  "parameters": [],
  "tabs": []
}
```

- **New dashcard:** use a unique negative `id` (`-1`, `-2`, ...).
- **Existing dashcard:** use its real `id`; preserve `parameter_mappings` and
  `visualization_settings`.
- **Grid:** 24 columns. Five KPI cards → widths `5,5,5,5,4`, height 3. Charts →
  width 12, height 6. Tables/full-width → width 24, height 7.
- **Do not delete unrelated cards:** append existing dashcards that are not in
  the target set back into the payload.

### Dashboard filters

Add filters in a second API pass, after the cards and dashboards exist. The
bundled `scripts/add_dashboard_filters.py` reconciles
`metabase/dashboard_filters.json` against the live dashboards. The payloads
below document what the script sends and what to send if you implement it
yourself.

#### Filter definitions schema

```json
{
  "root_collection_name": "Airbnb Analytics",
  "dashboards": [
    {
      "key": "supply",
      "collection": "Supply and Pricing Collection",
      "dashboard": "Supply and Pricing Dashboard",
      "filters": [
        {
          "name": "Room type",
          "slug": "room_type",
          "tag": "room_type",
          "type": "string/=",
          "section_id": "string",
          "values_query_type": "list",
          "is_multi": true,
          "expected_cards": 12
        }
      ]
    }
  ]
}
```

Filter fields:

| Field | Meaning |
| --- | --- |
| `name` | Display name in the dashboard filter bar |
| `slug` | Stable identity; existing parameters are matched by it |
| `tag` | Template-tag name inside the native SQL card |
| `type` | Dashboard parameter type (see table below) |
| `section_id` | Widget section: `string`, `number`, `date`, `boolean`, `id`, `location`, `temporal-unit` |
| `values_query_type` | `list` (dropdown), `search` (search box), or `none` |
| `is_multi` | Multi-select for string/category filters |
| `expected_cards` | Optional drift guard; abort if the live tag count differs |
| `exclude_cards` | Optional card names that expose the tag but must not be mapped |
| `default` | Optional default value |
| `values_source_type` / `values_source_config` | Optional `static-list` or `card` value source |
| `filteringParameters` / `temporal_units` | Optional linked-filter and time-grouping settings |

#### Parameter types

| Goal | `type` | `section_id` | `values_query_type` |
| --- | --- | --- | --- |
| Category / dropdown | `string/=` | `string` | `list` |
| Category / search box | `string/=` | `string` | `search` |
| Text contains | `string/contains` | `string` | `none` |
| Boolean | `boolean/=` | `boolean` | `none` |
| Exact number | `number/=` | `number` | `none` |
| Number range | `number/between` | `number` | `none` |
| Minimum number | `number/>=` | `number` | `none` |
| Date picker | `date/all-options` | `date` | `none` |

`sectionId` is what the frontend uses to choose the widget
(`getParameterType` prefers `sectionId` over the type prefix). A boolean filter
with `sectionId: "string"` can produce
`operator does not exist: boolean = character varying`.

#### Dashboard parameter payload

```json
{
  "id": "a1b2c3d4",
  "name": "Room type",
  "slug": "room_type",
  "type": "string/=",
  "sectionId": "string",
  "values_query_type": "list",
  "isMultiSelect": true,
  "default": null
}
```

Generate a fresh 8-character hex `id` for a new parameter. Reuse the existing
`id` when the `slug` already exists. Omit `values_source_type` to use live
distinct values from the mapped field(s); `values_query_type: "list"` makes
that a dropdown. Use `static-list` or `card` only when you want a fixed set.

#### Dashcard mapping payload

Field Filter / dimension tag:

```json
{
  "parameter_id": "a1b2c3d4",
  "card_id": 40,
  "target": ["dimension", ["template-tag", "room_type"], {"stage-number": 0}]
}
```

Plain Text / basic variable tag (`type` is not `dimension`):

```json
{
  "parameter_id": "e5f6a7b8",
  "card_id": 93,
  "target": ["variable", ["template-tag", "host_name"]]
}
```

The variable target has exactly two elements. A `stage-number` object on a
variable target is rejected by Metabase 0.64. Field Filters always use the
three-element dimension target.

A filter only affects cards where it is mapped. Map it to every card that
exposes the tag and should respond; skip cards whose meaning would change.

#### PUT mechanics

`PUT /api/dashboard/{id}` replaces the full `dashcards` and `parameters`
collections:

```json
{
  "dashcards": [
    {
      "id": 51,
      "card_id": 54,
      "row": 0,
      "col": 0,
      "size_x": 5,
      "size_y": 3,
      "parameter_mappings": [
        {
          "parameter_id": "a1b2c3d4",
          "card_id": 54,
          "target": ["dimension", ["template-tag", "room_type"], {"stage-number": 0}]
        }
      ],
      "visualization_settings": {},
      "inline_parameters": []
    }
  ],
  "parameters": [],
  "tabs": []
}
```

- Read the dashboard first and send back every existing dashcard.
- Preserve `id`, position, `visualization_settings`, `inline_parameters`, and
  mappings for filters the script does not manage.
- Send the existing `tabs` array whenever you send `dashcards`; omitting it can
  orphan tab references or fail the update.
- Use real IDs for existing dashcards; negative IDs only for new ones.
- Match parameters by `slug`, not by array position or name.

#### Commands

```powershell
# Backup first
.\\scripts\\backup_metabase.ps1

# Preview every filter and mapping; no writes
uv run python scripts\\add_dashboard_filters.py --definitions metabase\\dashboard_filters.json --dry-run

# Apply one dashboard, then the rest
uv run python scripts\\add_dashboard_filters.py --definitions metabase\\dashboard_filters.json --dashboard supply
uv run python scripts\\add_dashboard_filters.py --definitions metabase\\dashboard_filters.json
```

#### Verify filters

```powershell
# Confirm parameters and mappings persisted
GET /api/dashboard/{id}

# Confirm a dropdown has values
GET /api/dashboard/{id}/params/{parameter-id}/values

# Execute one mapped card with a filter
POST /api/dashboard/{id}/dashcard/{dashcard-id}/card/{card-id}/query
{"parameters": [{"id": "a1b2c3d4", "type": "string/=", "target": ["dimension", ["template-tag", "room_type"], {"stage-number": 0}], "value": ["Private room"]}], "ignore_cache": true}
```

Compare the filtered result with the unfiltered baseline, then clear the
filter and run the card again. Check every filter type at least once.

#### Filter gotchas

- Use `boolean/=` plus `sectionId: "boolean"` for boolean columns.
- `number/between` and `number/>=` work against a card tag whose widget type is
  `number/=`. The dashboard parameter type controls the SQL operator.
- Date range values use `YYYY-MM-DD~YYYY-MM-DD` with `date/all-options`.
- Category values come from the data. If the stored values are lowercase
  (`positive`, `neutral`), a manually typed `Positive` returns zero rows.
- `values_query_type: "list"` on a filter mapped to several fields merges the
  distinct values; confirm the fields share a domain.
- Mapping a text variable with a dimension target makes the filter silently do
  nothing or error; use the variable target.
- Do not map a filter to a card whose query lacks the tag.
- Do not run a bulk filter update without an app-DB backup and a dry-run plan.

#### Text-search filters

Text search needs a plain **Text** template tag in the card SQL, not a Field
Filter. Add the optional clause first:

```sql
WHERE 1 = 1
  [[AND LOWER(host_name) LIKE '%' || LOWER({{host_name}}) || '%']]
```

Then create the card parameter with type `string/contains`, target
`["variable", ["template-tag", "host_name"]]`, and the dashboard filter with
type `string/contains`, `sectionId: "string"`, `values_query_type: "none"`.
The filter script maps cards whose tag type is not `dimension` with the variable
target automatically.

### Verify a card

```http
POST /api/card/40/query
{"parameters": [], "ignore_cache": true}
```

The endpoint may return HTTP `202` with the result payload. Check
`data.rows`; a scalar KPI returns one row. Heavy raw histograms can return
hundreds of thousands of rows; do not execute those just to verify metadata.

## 7. Adoption and idempotency

- Match cards by exact target name first.
- On a partial build, adopt legacy names listed in `aliases`; update the name,
  description, display, SQL, tags, and parameters.
- Never overwrite an existing card that already has the target name; it may
  contain a user's manual changes.
- Preserve extra dashboard cards. The seeder includes them in the PUT payload.
- On rerun, if every target card is present, do not reposition the dashboard.
- `--relayout` is destructive to the grid layout; use it only when intended.
- `--dry-run` must make no writes.
- Match dashboard filters by `slug`; update the existing parameter instead of
  creating a duplicate.
- Preserve parameters and mappings the filter script does not manage.
- Add or update the mapping for every card that exposes the tag; remove stale
  mappings for managed filters whose tag disappeared.
- Enforce `expected_cards` when provided so a changed card tag aborts the run.

## 8. Verification checklist

- [ ] `--dry-run` succeeds and lists expected create/adopt actions.
- [ ] Second run reports every card/dashboard as existing.
- [ ] Collection counts match the definitions.
- [ ] Every card opens without an error.
- [ ] Representative cards return expected totals.
- [ ] Dashboard GET returns the expected number of dashcards and positions.
- [ ] Existing dashboards outside the target set are untouched.
- [ ] No duplicate card names within a collection.
- [ ] Every intended card exposes the tag used by its dashboard filter.
- [ ] Filter dry-run reports the expected parameter and mapping counts.
- [ ] A second filter dry-run reports every filter as existing.
- [ ] `GET /api/dashboard/{id}/params/{parameter-id}/values` returns values for
  category filters.
- [ ] Each filter changes a mapped card, returns rows, and clears without error.
- [ ] No mapping references a tag that does not exist on its card.
- [ ] Text-search filters use the two-element variable target.

## 9. Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `401 Unauthorized` | Missing/expired API key | Recreate the key; check `X-API-Key` |
| `404` on collection/card/dashboard | Wrong numeric ID | Re-read `/api/collection/{id}/items` |
| `400` "missing required parameters" | Tag has no field mapping or required value | Check `dimension` field ID and card `parameters` |
| `column ... does not exist` | Field Filter mapped to the wrong table | Map the field from the query's actual source |
| `missing FROM-clause entry` | SQL aliases the table but the tag has no alias | Rewrite unaliased or set the alias |
| Cards duplicated on rerun | Name matching missed | Use exact names; add `aliases` for legacy names |
| Dashboard cards overlap | New dashcards used non-negative IDs or wrong grid | Use negative IDs for new, 24-column rows |
| Every request takes ~2s | Python resolving `localhost` over IPv6 | Use `127.0.0.1` |
| `202` but no rows in the sample | Query still running or result capped | Poll/refresh; verify the SQL directly |
| App DB connection pool exhausted | Too many concurrent queries | Wait for prior queries; reduce parallelism |
| Filter returns 0 rows unexpectedly | Value casing/spacing differs from stored data | Read the values endpoint; use the exact stored value |
| `operator does not exist: boolean = character varying` | Boolean column mapped with a text filter | Use `boolean/=` and `sectionId: "boolean"` |
| Filter changes nothing | Dashboard filter not mapped to the card, or card tag is Text | Add the mapping; make the card tag a Field Filter |
| `vector with exactly 2 items` | A `stage-number` was added to a variable target | Use `["variable", ["template-tag", "tag"]]` |
| Dashboard layout or mappings disappear after filter pass | PUT omitted dashcards/tabs or mappings | GET the full dashboard; preserve and resend everything |
| Mapping count differs from the documented matrix | A card gained/lost a template tag | Fix the tag or `exclude_cards`; `expected_cards` aborts the run |

## 10. Security

- The API key is a password. Keep it in `.env`, never in `definitions.json`,
  exported JSON, or Git.
- Use a dedicated key name so it can be rotated.
- Take an app-database backup before the first bulk write and before reruns
  that update existing cards.
- Review the definitions file before running against a shared instance; a
  wrong field reference can create plausible but incorrect cards.

## 11. Worked example

The Airbnb project used this exact path:

- Root collection `5` (`Airbnb Analytics`), database `2`.
- 5 child collections and 5 dashboards.
- 66 native SQL cards; 4 partially-created Supply cards adopted by alias.
- Field IDs from `/api/database/2/metadata`.
- Cards created with Field Filter tags in the first pass.
- 22 dashboard filters and 183 mappings applied in the second pass with
  `scripts/add_dashboard_filters.py`: Supply 5/38, Guest 6/33, Host 4/32,
  Listing 7/80. The Executive Overview date filter was already manual.
- `expected_cards` matched every filter; a second dry-run reported every filter
  as existing with unchanged counts.
- Representative filtered queries matched the documented values: Private room
  `7,233`, price band `30-49` `4,849`, superhost `2,738`, active last 12m
  `6,050`.
- Export manifest: 6 collections, 66 cards, 5 dashboards, ~297 KB JSON.
- App DB dump: ~1.2 MB.
