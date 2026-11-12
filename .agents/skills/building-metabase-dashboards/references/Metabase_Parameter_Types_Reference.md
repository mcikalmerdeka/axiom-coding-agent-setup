# Metabase Parameter Types Reference

This project uses native SQL questions on PostgreSQL or Google BigQuery. There
are three common ways to add parameters/filters to a native SQL question in
Metabase.

For copy-paste-ready PostgreSQL queries for all 66 dashboard cards, see
[Dashboard SQL with Field Filters](dashboard-sql-with-filters.md). For BigQuery
connection, dialect, and Field Filter alias rules, see
[BigQuery Workspace](bigquery-workspace.md).

## 1. Basic variables (`{{parameter}}`)

```sql
-- Syntax
WHERE column = {{parameter_name}}

-- Example
WHERE room_type = {{room_type}}
```

### Setup

- Add the variable to the SQL.
- In the Variables panel, set the variable type to Text, Number, or Date.
- Do not choose **Field Filter**.

### Dashboard behavior

- A basic variable can be connected to a dashboard filter, but only to a
  filter type that selects a single value.
- It does not support multi-select dashboard filters.
- You must write the column and operator yourself in the SQL.

### Use case

- Simple single-value filters.
- Filters on custom expressions that are not database fields.

## 2. Optional variables (`[[...]]`)

```sql
-- Syntax
WHERE 1=1 [[AND column = {{parameter_name}}]]

-- Example
WHERE 1=1 [[AND room_type = {{room_type}}]]
```

Optional variables are basic variables wrapped in optional SQL clauses. The
clause is omitted when no value is supplied in the question editor.

### Dashboard behavior

- They can be connected to a dashboard filter, but the same single-value
  limitation applies.
- They do not "disappear" when added to a dashboard. The dashboard filter
  supplies a value, so the optional clause is included.

### Use case

- Questions where some filters should be optional when used on their own.

## 3. Field filters (`{{parameter}}` with Variable type = Field Filter)

```sql
-- Syntax
WHERE {{parameter_name}}

-- Example
WHERE {{room_type}} AND {{price_band}}
```

### Setup

- Add the variable to the SQL.
- In the Variables panel, set the variable type to **Field Filter**.
- Choose the database field the variable should filter.
- If the table is aliased in the SQL, fill in **Table and field alias**
  (for example, `l.room_type`).
- **BigQuery:** the alias field is required even when you would otherwise leave
  it blank. Write `FROM analytics.dim_listings AS dim_listings`, map the field
  to `analytics.dim_listings.room_type`, and set the alias to
  `dim_listings.room_type`. An unaliased card fails with
  `Unrecognized name: \`analytics.dim_listings\``; a tag alias containing only
  `dim_listings` compares a whole row STRUCT to a scalar.
- **BigQuery engine:** use `bigquery-cloud-sdk`, not `bigquery`.

### Dashboard behavior

- Field Filters work in the question editor and on dashboards.
- They support single-value and multi-select dashboard filters for
  text/category fields.
- They provide dropdown/search widgets based on the field.
- Metabase writes the column, operator, and value handling for you.

### Use case

- Recommended for any native SQL card that should respond to dashboard
  filters.

## Recommended approach for dashboards

Use Field Filters for native SQL cards that need dashboard filtering.

```sql
SELECT COUNT(*) AS total_listings
FROM analytics.dim_listings
WHERE {{room_type}}
  AND {{price_band}}
  AND {{minimum_nights_band}}
  AND {{is_superhost}}
  AND {{price}};
```

### Setup steps

1. Add the `{{...}}` variables to the SQL.
2. Set each variable type to **Field Filter**.
3. Map each variable to the matching database field.
4. Save the question.
5. Add the dashboard filters and map each one to the matching variable on
   each card.
6. Save the dashboard and test.

> **Important:** Field Filters do **not** automatically create dashboard
> filters. They make the card eligible for mapping. You still add the
> dashboard filter and connect it to the card's variable.

## Why the warning appears

If a native SQL card has no variables, a dashboard filter has nothing to
connect to. Metabase may show:

> "A text variable in this card can only be connected to a text filter with
> Is operator."

This is a generic warning. It does not mean the dashboard filter operator is
wrong. The card needs a Field Filter variable, or it should be built with the
query builder instead of native SQL.

## Troubleshooting

### "Cannot run the query: missing required parameters"

The variables are still type **Text**, or **Always require a value** is on.
Change each variable to **Field Filter**, map it to a field, and turn off
**Always require a value** if you want the query to run without filters.

### "argument of AND must be type boolean, not type character varying"

A Text variable was used inside `[[AND {{room_type}}]]` and a value was supplied.
Metabase replaced the variable with just the value, producing
`AND 'Entire home/apt'`. Change the variable to **Field Filter** and map it to
the field.

## Requiring a value

The **Always require a value** toggle makes a filter mandatory. If it is on,
you must set a default value; the default overrides optional `[[...]]` syntax.
For optional dashboard filters, leave it off.

## Dashboard filters vs question parameters

- **Dashboard filters:** Created at the dashboard level. They can affect
  multiple cards, but only the cards they are mapped to.
- **Question parameters:** Created inside a question. They can be used in the
  question editor and can be mapped to dashboard filters.
- **Field filters:** Question parameters connected to database fields. They
  are the best choice for dashboard filtering.

### API filter pass

Dashboard filters can also be created and mapped through the API with
`scripts/add_dashboard_filters.py` and `metabase/dashboard_filters.json`. The
dashboard parameter type controls the widget and SQL operator:

| Filter | Dashboard `type` | `sectionId` |
| --- | --- | --- |
| Category dropdown | `string/=` | `string` |
| Text contains | `string/contains` | `string` |
| Boolean | `boolean/=` | `boolean` |
| Number range | `number/between` | `number` |
| Minimum number | `number/>=` | `number` |
| Date | `date/all-options` | `date` |

Field Filter tags map with
`["dimension", ["template-tag", "tag"], {"stage-number": 0}]`. Plain Text
variables map with `["variable", ["template-tag", "tag"]]` (exactly two
elements). Full payloads and verification steps are in
[Metabase API Provisioning](metabase-api-provisioning.md#dashboard-filters).

## Aliases and CTEs

If the SQL aliases the table, for example:

```sql
FROM analytics.fct_reviews AS r
INNER JOIN analytics.dim_listings AS l ON r.listing_id = l.listing_id
```

set **Table and field alias** in each Field Filter's settings to:

```text
r.review_date
r.review_sentiment
r.has_comment
l.room_type
```

If the SQL uses a CTE and the field filter is outside the CTE, use the CTE
alias instead. Most updated queries in
[Dashboard SQL with Field Filters](dashboard-sql-with-filters.md) avoid table
aliases; Guest Experience card 3.9 is the joined exception.

## Multiple values

- Field Filters support multiple values for text/category fields.
- Boolean filters are typically single-value (True/False).
- Basic Text variables support only a single value.
- If you want a multi-select text filter, use a Field Filter.

## Boolean columns

For TRUE/FALSE columns such as `is_superhost`, `has_comment`,
`is_active_last_12m`, and `is_price_outlier`:

- Use a Field Filter with the Boolean widget type.
- Use a Boolean dashboard filter.
- Do not use a Text or Category filter for a boolean column.

## Remember

If you want a native SQL card to respond to a dashboard filter, it must contain
a Field Filter variable. A raw SQL column cannot be mapped directly.
