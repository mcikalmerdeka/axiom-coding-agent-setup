# BigQuery Workspace for Metabase Dashboards

Use this reference when Metabase reads Google BigQuery. The dashboard workflow
is the same as PostgreSQL; this file covers the differences that break cards or
filters.

## 1. Create the Metabase connection

Metabase 0.64 names the BigQuery driver `bigquery-cloud-sdk`, **not**
`bigquery`. A database payload looks like:

```json
{
  "name": "Airbnb Analytics",
  "engine": "bigquery-cloud-sdk",
  "details": {
    "project-id": "your-gcp-project-id",
    "service-account-json": "<contents of the service-account JSON key>",
    "dataset-filters-type": "inclusion",
    "dataset-filters-patterns": "analytics"
  }
}
```

- `service-account-json` is the **JSON text**, not the file path.
- The dataset filter keeps `raw`, `staging`, and `snapshots` out of the
  Metabase UI even though the account may see the dataset names.
- Use a dedicated service account, never a personal user key.
- Trigger `POST /api/database/{id}/sync_schema` and poll
  `GET /api/database/{id}/metadata` until the expected tables appear.

## 2. Service-account IAM

Minimum practical permissions for a read-only Metabase connection:

| Role / ACL | Scope | Why |
| --- | --- | --- |
| `roles/bigquery.jobUser` | project | Run SELECT jobs |
| Dataset `READER` (equivalent to `roles/bigquery.dataViewer`) | `analytics` dataset only | Read tables and table metadata |

**Do not grant project-level `roles/bigquery.metadataViewer`.** It lets the
account list tables in every dataset, including `raw`, `staging`, and
`snapshots`, which violates least privilege even if data queries are denied.
Dataset `READER` on `analytics` supplies the metadata the driver needs.

Also remove the default `projectReaders` ACL from non-analytics datasets if
project viewers should not gain read access through project-level roles. The
account will still see dataset **names** via BigQuery's project dataset list;
it must not be able to list tables or query data outside `analytics`.

Verify both metadata and data boundaries:

```python
# uv run python scripts/check_metabase_access.py
from google.api_core.exceptions import Forbidden
from google.cloud import bigquery

client = bigquery.Client.from_service_account_json("key.json", project="your-project")
assert len(list(client.list_tables("analytics"))) > 0
for dataset in ("raw", "staging", "snapshots"):
    try:
        list(client.list_tables(dataset))
        raise SystemExit(f"{dataset} metadata unexpectedly visible")
    except Forbidden:
        pass

client.query("SELECT COUNT(*) FROM `your-project.analytics.dim_listings`").result()
try:
    client.query("SELECT COUNT(*) FROM `your-project.raw.raw_listings`").result()
    raise SystemExit("raw data unexpectedly readable")
except Forbidden:
    pass
```

## 3. Field Filters require table aliases

This is the failure that looks like a SQL bug:

```text
Unrecognized name: `analytics.dim_listings` at [4:8]
```

Metabase renders a Field Filter as `alias.column`. With unaliased SQL the
BigQuery driver treats the dataset path as one quoted identifier. Every native
card must alias its table and every tag must store the full `alias.column`.

```sql
SELECT COUNT(*) AS total_listings
FROM analytics.dim_listings AS dim_listings
WHERE 1 = 1
  AND {{room_type}}
  AND {{is_superhost}};
```

| Template tag | Type | Field to map to | Table and field alias |
| --- | --- | --- | --- |
| `room_type` | Field Filter (`string/=`) | `analytics.dim_listings.room_type` | `dim_listings.room_type` |
| `is_superhost` | Field Filter (`boolean/=`) | `analytics.dim_listings.is_superhost` | `dim_listings.is_superhost` |

For a join, alias each table and use its alias in the tag:

```sql
SELECT l.room_type, COUNT(*) AS reviews
FROM analytics.fct_reviews AS r
INNER JOIN analytics.dim_listings AS l ON r.listing_id = l.listing_id
WHERE {{review_date}}
  AND {{room_type}}
GROUP BY l.room_type;
```

Tag aliases: `r.review_date`, `l.room_type`.

Dashboard filter mappings still use the three-element dimension target:

```json
["dimension", ["template-tag", "room_type"], {"stage-number": 0}]
```

## 4. GoogleSQL conversion rules

| PostgreSQL | GoogleSQL |
| --- | --- |
| `COUNT(*) FILTER (WHERE cond)` | `COUNTIF(cond)` |
| `AVG(x) FILTER (WHERE cond)` | `AVG(IF(cond, x, NULL))` |
| `x::numeric` | `CAST(x AS FLOAT64)` (or `NUMERIC` when exact decimals matter) |
| `x::text` | `CAST(x AS STRING)` |
| `PERCENTILE_CONT(p) WITHIN GROUP (ORDER BY x)` | exact window CTE: `PERCENTILE_CONT(x, p) OVER (PARTITION BY ...)` then `MAX(...)` + `GROUP BY` |
| `DATE '2021-11-19' - ts::date` | `DATE_DIFF(DATE '2021-11-19', DATE(ts), DAY)` |
| `date + INTERVAL '1 month'` | `DATE_ADD(date, INTERVAL 1 MONTH)` |
| `date - INTERVAL '12 months'` | `DATE_SUB(date, INTERVAL 12 MONTH)` |
| `date + INTERVAL '1 month - 1 day'` | `LAST_DAY(date)` |
| `TO_CHAR(d, 'Month')` | `FORMAT_DATE('%B', d)` |
| `TO_CHAR(d, 'Mon')` | `FORMAT_DATE('%b', d)` |
| `TO_CHAR(d, 'Day')` | `FORMAT_DATE('%A', d)` |
| `TO_CHAR(d, 'YYYYMMDD')` | `FORMAT_DATE('%Y%m%d', d)` |
| `EXTRACT(WEEK FROM d)` | `EXTRACT(ISOWEEK FROM d)` |
| `EXTRACT(ISODOW FROM d)` | `CAST(FORMAT_DATE('%u', d) AS INT64)` |
| `EXTRACT(ISODOW FROM d) IN (6, 7)` | `EXTRACT(DAYOFWEEK FROM d) IN (1, 7)` |
| `DATE_TRUNC('month', d)::date` | `DATE_TRUNC(d, MONTH)` |
| `a / NULLIF(b, 0)` | `SAFE_DIVIDE(a, b)` |
| `x ~* regex` | `REGEXP_CONTAINS(LOWER(x), LOWER(regex))` |
| `NULL::bigint` | `CAST(NULL AS INT64)` |
| `ORDER BY x NULLS LAST` | supported; no change needed |
| `a \|\| b` | supported; no change needed |

### Exact median

```sql
WITH listing_median AS (
    SELECT
        room_type,
        MAX(median_price) AS median_price
    FROM (
        SELECT
            room_type,
            PERCENTILE_CONT(price, 0.5) OVER (PARTITION BY room_type) AS median_price
        FROM analytics.dim_listings
        WHERE NOT is_price_outlier
    )
    GROUP BY room_type
)
SELECT * FROM listing_median;
```

`APPROX_QUANTILES(x, 100)[OFFSET(50)]` is acceptable for profiling, not when
the dashboard contract expects an exact median.

### Timestamp versus date

- BigQuery does not implicitly compare `TIMESTAMP` to `DATE`.
- `DATE(ts)` (or `DATE_TRUNC(DATE(ts), MONTH)`) is explicit and preserves
  Postgres `ts::date` behavior.
- `dbt_utils.date_spine` returns `DATETIME` on BigQuery. Cast the spine to
  `DATE` before exposing `date_day`, otherwise every `month_start` becomes
  `DATETIME`.

## 5. Regex and Unicode

Postgres `~*` and RE2 both support `\b`, but **RE2 `\b` is ASCII-only** while
Postgres `\y` treats accented letters as word characters. A keyword list that
works in Postgres can overcount on BigQuery (for example German `bedürfnis`
matching `\bbed\b`).

For parity, replace word boundaries in keyword seeds with explicit Unicode
classes:

```regex
(?:^|[^\p{L}\p{N}_])keyword(?:$|[^\p{L}\p{N}_])
```

Verify topic totals, not just row counts.

## 6. Cost guardrails

Set these before leaving a dashboard build unattended:

- Project budget alert (for example ~$1 equivalent, 50% and 100% thresholds).
- Daily query quota (`QueryUsagePerDay`).
- Per-query cap in `profiles.yml`:
  `maximum_bytes_billed: 1000000000`.
- Keep Dagster schedules stopped by default.

## 7. Bootstrap and operations

```powershell
# Local config from committed examples
Copy-Item .env.example .env
Copy-Item profiles.yml.example profiles.yml

# Datasets, service account, dataset ACL, key, guardrails
.\scripts\provision_bigquery.ps1
.\scripts\set_bigquery_guardrails.ps1

# Raw CSV load (truncate + reload)
.\scripts\load_raw_data.ps1

# dbt
cd airbnb_dbt
uv run dbt deps --profiles-dir ..
uv run dbt build --profiles-dir ..

# Metabase
cd ..
docker compose up -d
uv run python scripts\setup_metabase.py
uv run python scripts\seed_metabase.py
uv run python scripts\add_dashboard_filters.py
uv run python scripts\export_metabase.py
.\scripts\backup_metabase.ps1
```

## 8. Validation checklist

- [ ] Engine is `bigquery-cloud-sdk`.
- [ ] Metabase metadata shows only the `analytics` dataset.
- [ ] Service account is denied table listing and queries in `raw`, `staging`,
      `snapshots`.
- [ ] Every native card aliases its table.
- [ ] Every Field Filter tag stores `alias.column`.
- [ ] A real filtered query returns the expected value (not just HTTP 200).
- [ ] `dim_date`/month columns are `DATE`, not `DATETIME`.
- [ ] Exact medians use `PERCENTILE_CONT ... OVER (...)`.
- [ ] Topic totals match the Postgres baseline.
- [ ] All cards execute unfiltered after seeding and after filters.
- [ ] Export and app-DB backup succeed.

## 9. Common BigQuery errors

| Symptom | Cause | Fix |
| --- | --- | --- |
| `value must be a valid database engine` | Used engine `bigquery` | Use `bigquery-cloud-sdk` |
| `Unrecognized name: \`analytics.table\`` | No table alias; Field Filter emitted a dataset path | Alias table; set tag alias `table.column` |
| `No matching signature for operator =` with `STRUCT<...>` | Tag alias is only the table name | Use full `alias.column` |
| `No matching signature for operator >=: TIMESTAMP, DATE` | Compared timestamp to date literal | Wrap with `DATE(column)` |
| `Invalid table-valued function GENERATE_DATE_ARRAY` / month type wrong | Date spine returned DATETIME | Cast to DATE |
| `Syntax error: Illegal escape sequence: \$` | BigQuery string literal regex | Use a character class such as `^[$]?` |
| `Access Denied: region-...INFORMATION_SCHEMA.TABLES` | Region-level metadata permission not granted | Use per-dataset `INFORMATION_SCHEMA` or `__TABLES__` |
| `bq` query fails only from a script | Windows `.cmd` shim and multi-line argument quoting | Send SQL on stdin via `subprocess.run(..., input=sql)` or use a single-line argument |
