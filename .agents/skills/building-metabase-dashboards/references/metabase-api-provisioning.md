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
`definitions.json` uses placeholder `root_collection_id` and `database_id`; fill
them from the API discovery below.

## Preconditions

- Metabase is running and connected to the analytics database.
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
numeric field ID, not a table/column string.

```text
analytics.dim_listings.room_type      -> 95
analytics.dim_listings.price          -> 96
analytics.dim_listings.price_band     -> 97
analytics.fct_reviews.review_date     -> 113
analytics.mart_executive_kpis.month_start -> 122
```

Record the `database_id` too. A native SQL card's `dataset_query.database` is
this numeric ID.

## 3. Definitions file

Use one JSON file as the source of truth for the build. The seeder reads it; do
not edit generated metadata by hand.

```json
{
  "root_collection_id": 5,
  "root_collection_name": "Airbnb Analytics",
  "database_id": 2,
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

### Field meanings

| Field | Meaning |
| --- | --- |
| `root_collection_id` | Existing parent collection; its children are the dashboard collections |
| `database_id` | Metabase database ID used by every native SQL card |
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
  "field_id": 95,
  "widget_type": "string/=",
  "display_name": "Room Type"
}
```

- The SQL must contain `{{room_type}}` in a `WHERE` clause.
- The tag's `field_id` must belong to a table present in the query.
- `widget_type`: `string/=`, `boolean/=`, `number/=`, or `date/all-options`.
- If the SQL aliases a table, either add the alias to the tag or rewrite the
  SQL to use the unaliased table name. Prefer unaliased SQL for generated cards.
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
4. Confirm every `field_id` exists and belongs to the query's source table.
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

- Finds a collection by name under the root; creates it if missing.
- Finds a card by target name in the collection; reuses it.
- If not found, checks each alias; adopts the first match and renames it.
- Creates missing cards with native SQL and Field Filter tags.
- Finds a dashboard by name; creates it if missing.
- Adds missing cards to the dashboard; preserves extra cards, dashboard
  parameters, tabs, and existing filter mappings.
- If every target card is already on the dashboard, leaves the layout alone
  unless `--relayout` is passed.
- Skips dashboards with `"skip": true`.

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
      "native": "SELECT COUNT(*) AS total_listings FROM analytics.dim_listings",
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
  "dimension": ["field", {"lib/uuid": "11111111-1111-1111-1111-111111111111"}, 95]
}
```

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

### Dashboard filters (optional second pass)

Dashboard parameter:

```json
{
  "name": "Room Type",
  "slug": "room_type",
  "id": "a1b2c3d4",
  "type": "string/=",
  "sectionId": "string"
}
```

Dashcard mapping:

```json
{
  "parameter_id": "a1b2c3d4",
  "card_id": 40,
  "target": ["dimension", ["template-tag", "room_type"], {"stage-number": 0}]
}
```

Boolean filters use `type: "boolean/="`; date filters use
`date/all-options`; numbers use `number/=` or `number/between`.

A filter only affects cards where it is mapped. Do not map a filter to a card
whose query lacks the variable.

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

## 8. Verification checklist

- [ ] `--dry-run` succeeds and lists expected create/adopt actions.
- [ ] Second run reports every card/dashboard as existing.
- [ ] Collection counts match the definitions.
- [ ] Every card opens without an error.
- [ ] Representative cards return expected totals.
- [ ] Dashboard GET returns the expected number of dashcards and positions.
- [ ] Existing dashboards outside the target set are untouched.
- [ ] No duplicate card names within a collection.
- [ ] Filters can be added later; card `parameters` expose the tags.

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

## 10. Security

- The API key is a password. Keep it in `.env`, never in `definitions.json`,
  exported JSON, or Git.
- Use a dedicated key name so it can be rotated.
- Take an app-database backup before the first bulk write and before reruns
  that update existing cards.
- Review the definitions file before running against a shared instance; a
  wrong `database_id` or field ID can create plausible but incorrect cards.

## 11. Worked example

The Airbnb project used this exact path:

- Root collection `5` (`Airbnb Analytics`), database `2`.
- 5 child collections and 5 dashboards.
- 66 native SQL cards; 4 partially-created Supply cards adopted by alias.
- Field IDs from `/api/database/2/metadata`.
- Cards created with Field Filter tags; dashboard filters deferred to a later
  pass.
- Second `--dry-run` reported all 66 cards existing.
- Export manifest: 6 collections, 66 cards, 5 dashboards, ~237 KB JSON.
- App DB dump: ~1.2 MB.
