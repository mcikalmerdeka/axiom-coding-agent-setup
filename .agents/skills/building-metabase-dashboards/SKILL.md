---
name: building-metabase-dashboards
description: Use when building or extending a Metabase dashboard from SQL tables, especially when adding KPI/chart cards, native SQL, dashboard filters, Field Filter variables, or validating filter behavior and dashboard QA.
compatibility: Requires a running Metabase instance connected to PostgreSQL. Docker, PostgreSQL, and ETL setup are out of scope.
metadata:
  author: gym-membership-metabase
  version: "1.0"
---

# Building Metabase Dashboards

## Overview

Build a Metabase dashboard in this order:

**analysis-ready table -> model -> saved questions -> dashboard -> filters -> format -> QA**

The bundled references use the Gym Membership dataset as a complete worked
example. For a new project, substitute the real table and column names, but keep
the same structure: one wide/analysis-ready table, a model, saved questions,
one dashboard, dashboard filters mapped to every intended card, and a QA pass.

Assume Metabase and the database are already running. **Do not include Docker,
PostgreSQL installation, or ETL setup in the plan.**

UI labels in this skill are from Metabase 0.64.x. Newer versions may rename
controls, but the concepts (Field Filter, variable mapping, dashboard filter
type) are the same.

## When to use

Use this skill when:

- The user wants a new Metabase dashboard, KPI row, chart set, or detail table.
- An existing Metabase dashboard needs filters that work across multiple cards.
- A native SQL card shows `A text variable in this card can only be connected...`.
- A native SQL card shows `Cannot run the query: missing required parameters`.
- A native SQL card shows `argument of AND must be type boolean`.
- The user needs a repeatable layout, visualization choices, filter mapping, or
  QA checklist for an operational dashboard.

Do not use this skill for Docker/PostgreSQL setup, data cleaning, ETL, or
database schema design.

## Preconditions

- Metabase is running and reachable.
- The database connection already exists in Metabase.
- An analysis-ready table or model exists.
- You know the table grain (for example, one row per member or per order).
- You know which columns should become filters and whether they are text,
  category, boolean, number, or date fields.

## First decision: query builder or native SQL

| Need | Build with | How dashboard filters attach |
| --- | --- | --- |
| Simple count, average, group-by, filter | Query builder on the model | Map the filter directly to the column |
| `CROSS JOIN LATERAL`, CTEs, window functions, complex SQL | Native SQL | Add one **Field Filter** variable per filter and map to the variable |
| Mixed dashboard | Query builder for simple cards; native SQL only where needed | Keep filter names and types consistent |

Prefer the query builder for simple member-level cards. Native SQL is not a
shortcut for filters: it makes filters harder because every card needs its own
variables.

If the project uses a star schema, either build a wide table/model for the
filterable cards or join the bridge tables to the main table. See
[When to use the star schema instead](references/dashboard-build-guide.md#when-to-use-the-star-schema-instead).

## Build sequence

1. **Inspect the schema.** Confirm the grain, key columns, filter columns, and
   expected unfiltered totals.
2. **Create a model.** Point it at the analysis-ready wide table. Name it
   clearly and add a short description.
3. **Plan the card inventory.** Start with the KPI row, then demographics,
   usage, engagement/popularity, and the detail table.
4. **Build and save questions** in the collection. Use consistent names:
   `KPI - ...`, `Chart - ...`, `Table - ...`.
5. **Create the dashboard** and add saved questions in section order.
6. **Add dashboard filters** and map each filter to every card that should
   respond.
7. **Format** numbers, legends, sorting, colors, and table columns.
8. **Run QA** with no filters, with each filter individually, and after
   clearing filters.

## Card inventory

Adapt this inventory to the new dataset. The visualization column is a starting
point, not a hard requirement.

| # | Question name | Visualization | Source |
| ---: | --- | --- | --- |
| 1 | KPI - Total Members | Number | Wide table |
| 2 | KPI - Active Personal Trainers | Number | Wide table |
| 3 | KPI - Group Lessons | Number | Lesson list |
| 4 | KPI - Average Visits per Week | Number | Wide table |
| 5 | KPI - Average Session Duration | Number | Wide table |
| 6 | Chart - Membership Type | Pie or bar | Wide table |
| 7 | Chart - Gender Distribution | Pie or bar | Wide table |
| 8 | Chart - Age Groups | Bar | Wide table |
| 9 | Chart - Personal Training Usage | Pie or bar | Wide table |
| 10 | Chart - Sauna Usage | Pie or bar | Wide table |
| 11 | Chart - Group Lesson Attendance | Pie or bar | Wide table |
| 12 | Chart - Drink Package Adoption | Pie or bar | Wide table |
| 13 | Chart - Visit Frequency Distribution | Bar | Wide table |
| 14 | Chart - Session Duration Distribution | Bar | Wide table |
| 15 | Chart - Weekly Activity | Bar | Wide table |
| 16 | Chart - Hourly Check-in and Check-out | Line | Wide table |
| 17 | Chart - Lesson Popularity | Bar | Wide table |
| 18 | Chart - Drink Popularity | Bar | Wide table |
| 19 | Chart - Trainer Popularity | Bar | Wide table |
| 20 | Table - Member Detail | Table | Wide table |

Use the **Description** field on every saved question to explain what it
measures and whether members can appear more than once. Use the exact
descriptions in the
[Question descriptions](references/dashboard-build-guide.md#question-descriptions)
section of the build guide.

## Dashboard layout

```text
Row 1: 5 KPI number cards
Row 2: Membership type | Gender | Age groups
Row 3: Personal training | Sauna | Group lessons | Drink package
Row 4: Visit frequency | Session duration | Weekly activity
Row 5: Hourly trend (full width)
Row 6: Lesson popularity | Drink popularity | Trainer popularity
Row 7: Member detail table (full width)
```

Use **Text cards** as section headings:

- Overview
- Member Demographics
- Facility and Service Usage
- Engagement and Popularity
- Member Detail

## Native SQL filter recipe

Use this only when the card must stay as native SQL. Every card that should
respond to a dashboard filter needs the filter variable in its SQL.

### Worked example: six filters

| Dashboard filter | Filter type | Column |
| --- | --- | --- |
| Gender | Text or Category | `gender` |
| Membership Type | Text or Category | `abonoment_type` |
| Personal Training | Boolean | `personal_training` |
| Sauna Usage | Boolean | `uses_sauna` |
| Group Lesson Attendance | Boolean | `attend_group_lesson` |
| Drink Package | Boolean | `drink_abo` |

### SQL block

Add the filters to the `WHERE` clause of every native SQL card:

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

Notes:

- Use `WHERE {{gender}}`, **not** `WHERE gender = {{gender}}`. A Field Filter
  inserts the column, operator, and value handling.
- Field Filters are optional by default. `AND {{gender}}` is enough.
- `WHERE 1=1 [[AND {{gender}}]]` also works when the variables are Field
  Filters, but the direct `AND {{gender}}` form is simpler.
- Do not use `'{{gender}}'` or wrap the variable in quotes.

### Variable settings

For each variable in the Metabase **Variables** panel:

| Variable | Variable type | Field to map to | Widget type |
| --- | --- | --- | --- |
| `{{gender}}` | Field Filter | `gym_members_wide.gender` | Category / Dropdown list |
| `{{abonoment_type}}` | Field Filter | `gym_members_wide.abonoment_type` | Category / Dropdown list |
| `{{personal_training}}` | Field Filter | `gym_members_wide.personal_training` | Boolean |
| `{{uses_sauna}}` | Field Filter | `gym_members_wide.uses_sauna` | Boolean |
| `{{attend_group_lesson}}` | Field Filter | `gym_members_wide.attend_group_lesson` | Boolean |
| `{{drink_abo}}` | Field Filter | `gym_members_wide.drink_abo` | Boolean |

**Critical:** typing `{{gender}}` creates a template tag, but Metabase often
defaults it to **Text**. Change the variable type to **Field Filter**, choose
the matching field, and turn **Always require a value** off if the question
should run with no filters selected. Save the question before mapping it on a
dashboard.

### Dashboard filter settings

| Dashboard filter | Filter type | Maps to variable |
| --- | --- | --- |
| Gender | Text or Category | `gender` |
| Membership Type | Text or Category | `abonoment_type` |
| Personal Training | Boolean | `personal_training` |
| Sauna Usage | Boolean | `uses_sauna` |
| Group Lesson Attendance | Boolean | `attend_group_lesson` |
| Drink Package | Boolean | `drink_abo` |

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

- If the SQL aliases the table, for example `FROM gym_members_wide w`, fill in
  **Table and field alias** for each Field Filter, for example `w.gender`.
- If the SQL uses a CTE and the field filter is outside the CTE, use the CTE
  alias instead.
- The provided SQL avoids aliasing `gym_members_wide` so the alias field can be
  left blank.
- If a card's source table does not contain the filter columns, join it to the
  wide table or leave that card unfiltered. Example: the Group Lessons KPI
  reads `gym_member_lessons`, so join `gym_members_wide` on member ID to make it
  filterable.

## Common mistakes

- Converting a simple query-builder card to native SQL, then having to configure
  six variables. Use the query builder unless the SQL is genuinely complex.
- Leaving `{{gender}}` as a **Text** variable. It must be a **Field Filter**
  mapped to the field.
- Using Text or Category dashboard filters for boolean columns. Use **Boolean**.
- Mapping a filter to only some cards. Map it to every card that should respond.
- Writing `gender = {{gender}}` for a Field Filter. Use `WHERE {{gender}}`.
- Assuming a dashboard filter will apply to a card that has no matching
  variable. It will not.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `A text variable in this card can only be connected to a text filter with Is operator` | The card has no mappable variable, or the variable is still Text | Add the `{{...}}` tag, set type to **Field Filter**, map the field |
| `Cannot run the query: missing required parameters` | Variables are Text, or **Always require a value** is on | Change to **Field Filter**, map fields, turn off **Always require a value** |
| `argument of AND must be type boolean, not type character varying` | A Text variable was used where a Field Filter was needed; a value was substituted as `AND 'Female'` | Change the variable to **Field Filter** and map it |
| `operator does not exist: boolean = character varying` | Text/Category dashboard filter connected to a boolean column | Change the dashboard filter to **Boolean** |
| Field Filter does not appear in the dashboard mapping panel | Question not saved, or dashboard editor is stale | Save the question, reload the dashboard editor |
| Filter changes one card but not another | Other card lacks the matching variable or mapping | Add the variable to that card and map the filter |
| `column ... does not exist` | Field Filter mapped to the wrong field, or alias setting missing | Correct the field mapping or table/field alias |
| Filter works in the question but not on the dashboard | The dashboard filter is not connected to the card | Map the dashboard filter to the card's variable |

For the full error explanations and parameter behavior, read
[Metabase Parameter Types Reference](references/Metabase_Parameter_Types_Reference.md).

## Visualization and formatting

- **KPI cards:** one row, equal width, no unnecessary decimals.
- **Pie charts:** show the legend and percentage labels.
- **Bar charts:** sort descending for popularity; keep source order for days and
  visit frequency.
- **Line chart:** use `hour` on the X-axis, `members` on the Y-axis, `event` as
  the series breakout, and distinct colors for check-ins/check-outs.
- **Tables:** hide unnecessary columns, set a sensible row limit, and enable
  downloads if useful.
- Add a short description to each saved question explaining what it measures.

## QA checklist

- [ ] Total members equals the expected total.
- [ ] Category distributions sum to the total.
- [ ] Boolean distributions sum to the total.
- [ ] Popularity totals match the expected selections.
- [ ] Weekly activity totals match the expected member-days.
- [ ] Every filter changes its intended cards and can be cleared.
- [ ] No card shows an error or an unexpected empty result.
- [ ] Dashboard is saved in the project collection.

For the Gym Membership worked example, the expected unfiltered values are:

- Total Members: `1000`
- Membership Type totals: `1000`
- Gender totals: `1000`
- Active Personal Trainers: `4`
- Group Lessons: `11`
- Lesson Popularity rows total: `1003` selections
- Drink Popularity rows total: `719` selections
- Weekly Activity rows total: `2682` member-days

## Reusing the pattern on a new project

1. Identify the analysis-ready wide table and its grain.
2. Identify the filter columns and their types.
3. Build the KPI, demographic, usage, popularity, and detail cards.
4. Prefer the query builder for simple cards.
5. If a card must be native SQL, add one Field Filter per filter and map it to
   the matching field.
6. Use the same variable names and dashboard filter types on every card.
7. Map every dashboard filter to every intended card.
8. Run the QA checklist with no filters, one filter, and multiple filters.

## Shortcuts and limits

- Metabase has no built-in **copy variables** button.
- A practical UI shortcut: configure one native SQL card correctly, duplicate
  it, replace only the SQL with the next card's query, and verify the six Field
  Filter settings persist in the duplicate. Test with one duplicate first.
- The query builder is the best shortcut for simple cards because filters map
  directly to columns with no SQL variables.
- Do not force a filter onto a card where it changes the meaning of the card.
  It is valid to leave some cards unfiltered.
- If using the Metabase API or app database to copy template tags, back up the
  cards first and verify the JSON structure; this is advanced and not the
  normal UI path.

## References

Read the relevant reference before building. These are exact copies of the
project documentation.

- [Dashboard Build Guide](references/dashboard-build-guide.md) — build order,
  card inventory, visualizations, layout, filters, and QA.
- [Dashboard SQL with Field Filters](references/dashboard-sql-with-filters.md) —
  all 20 filtered SQL queries, variable settings, troubleshooting, and
  verification.
- [Metabase Parameter Types Reference](references/Metabase_Parameter_Types_Reference.md) —
  basic variables, optional variables, Field Filters, aliases, boolean fields,
  and the exact error explanations.

Maintenance: if the project docs change, re-copy the three files into
`references/` so the skill stays exact.
