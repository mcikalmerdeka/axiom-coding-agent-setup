# Metabase Parameter Types Reference

This project uses native SQL questions on PostgreSQL. There are three common
ways to add parameters/filters to a native SQL question in Metabase.

For copy-paste-ready queries for all 20 dashboard cards, see
[Dashboard SQL with Field Filters](dashboard-sql-with-filters.md).

## 1. Basic variables (`{{parameter}}`)

```sql
-- Syntax
WHERE column = {{parameter_name}}

-- Example
WHERE gender = {{gender}}
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
WHERE 1=1 [[AND gender = {{gender}}]]
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
WHERE {{gender}} AND {{abonoment_type}}
```

### Setup

- Add the variable to the SQL.
- In the Variables panel, set the variable type to **Field Filter**.
- Choose the database field the variable should filter.
- If the table is aliased in the SQL, fill in **Table and field alias**
  (for example, `w.gender`).

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
SELECT COUNT(*) AS total_members
FROM gym_members_wide
WHERE {{gender}}
  AND {{abonoment_type}}
  AND {{personal_training}}
  AND {{uses_sauna}}
  AND {{attend_group_lesson}}
  AND {{drink_abo}};
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

A Text variable was used inside `[[AND {{gender}}]]` and a value was supplied.
Metabase replaced the variable with just the value, producing `AND 'Female'`.
Change the variable to **Field Filter** and map it to the field.

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

## Aliases and CTEs

If the SQL aliases the table, for example:

```sql
FROM gym_members_wide w
```

set **Table and field alias** in each Field Filter's settings to:

```text
w.gender
w.abonoment_type
w.personal_training
w.uses_sauna
w.attend_group_lesson
w.drink_abo
```

If the SQL uses a CTE and the field filter is outside the CTE, use the CTE
alias instead. The updated queries in
[Dashboard SQL with Field Filters](dashboard-sql-with-filters.md) do not alias
`gym_members_wide`, so you can leave the alias blank for those.

## Multiple values

- Field Filters support multiple values for text/category fields.
- Boolean filters are typically single-value (True/False).
- Basic Text variables support only a single value.
- If you want a multi-select text filter, use a Field Filter.

## Boolean columns

For TRUE/FALSE columns such as `personal_training`, `uses_sauna`,
`attend_group_lesson`, and `drink_abo`:

- Use a Field Filter with the Boolean widget type.
- Use a Boolean dashboard filter.
- Do not use a Text or Category filter for a boolean column.

## Remember

If you want a native SQL card to respond to a dashboard filter, it must contain
a Field Filter variable. A raw SQL column cannot be mapped directly.
