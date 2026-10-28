# Dashboard SQL with Field Filters

Use this file if you want to keep the dashboard questions as **Native SQL** and
still make the six dashboard filters work. These queries target the PostgreSQL
`gym` database used in this project.

If you build a question with the **query builder** on the `Gym Members - Wide`
model, you do **not** need this file. The query builder exposes the columns
directly, so dashboard filters can be mapped without SQL variables.

## What changed

- Every member-level query now contains the same six Field Filter variables.
- `KPI - Group Lessons` now joins `gym_member_lessons` to `gym_members_wide`
  so it can be filtered by member attributes.
- `gym_members_wide` is **not aliased** in the filterable queries. This means
  you do not need to fill in the **Table and field alias** setting for the
  field filters.
- The LATERAL queries (`Weekly Activity`, `Lesson Popularity`, and
  `Drink Popularity`) were rewritten without the `w` alias for the same reason.

## The six variables

Every query below uses these variable names. When you paste a query into
Metabase, configure each variable in the **Variables** panel.

| Variable | Variable type | Field to map to | Widget type |
| --- | --- | --- | --- |
| `{{gender}}` | Field Filter | `gym_members_wide.gender` | Category / Dropdown list |
| `{{abonoment_type}}` | Field Filter | `gym_members_wide.abonoment_type` | Category / Dropdown list |
| `{{personal_training}}` | Field Filter | `gym_members_wide.personal_training` | Boolean |
| `{{uses_sauna}}` | Field Filter | `gym_members_wide.uses_sauna` | Boolean |
| `{{attend_group_lesson}}` | Field Filter | `gym_members_wide.attend_group_lesson` | Boolean |
| `{{drink_abo}}` | Field Filter | `gym_members_wide.drink_abo` | Boolean |

> **Important:** Typing `{{gender}}` creates a template tag, but Metabase may
> default it to the **Text** variable type. You must change each variable to
> **Field Filter** and choose the matching field. A plain Text variable only
> supports a single-value dashboard filter; a Field Filter on a text/category
> field supports multiple values and the field-aware dropdown.

## Dashboard filter settings

Use these types when you create the dashboard filters.

| Dashboard filter | Filter type | Maps to variable |
| --- | --- | --- |
| Gender | Text or Category | `gender` |
| Membership Type | Text or Category | `abonoment_type` |
| Personal Training | Boolean | `personal_training` |
| Sauna Usage | Boolean | `uses_sauna` |
| Group Lesson Attendance | Boolean | `attend_group_lesson` |
| Drink Package | Boolean | `drink_abo` |

If you already created these filters, edit their types rather than creating
duplicates.

For the text filters, keep **Filter operator: Is**. Choose **Multiple values**
for the text filters if you want multi-select. Boolean filters are typically
single-value (True/False).

## How to update each question

1. Open the question in Metabase.
2. Click **Edit** and switch to the SQL editor if needed.
3. Replace the SQL with the version for that question below.
4. Open the **Variables** panel.
5. For each of the six variables:
   - Set **Variable type** to **Field Filter**.
   - Set **Field to map to** to the matching `gym_members_wide` field.
   - Set the widget type to **Category** for `gender` and `abonoment_type`,
     and **Boolean** for the other four.
   - Turn **Always require a value** off if you want the question to run with
     no filters selected.
6. Save the question.
7. Repeat for all 20 questions.
8. Edit the dashboard and map each dashboard filter to the matching variable
   on each card.
9. Save the dashboard and test.

If the Variables panel still shows **Text** for these variables, you will get
`Cannot run the query: missing required parameters` when the widgets are
empty, or `argument of AND must be type boolean` when they contain a value.
The variable type must be **Field Filter**, not Text.

The queries below use `AND {{gender}}` without `[[...]]`. That is fine because
Field Filters are optional by default. If you already changed the SQL to
`WHERE 1=1 [[AND {{gender}}]]`, that also works once the variables are Field
Filters.

If a variable does not appear in the dashboard mapping panel, reload the
dashboard editor. Metabase needs the saved question to see the variable.

**Tip:** update and test **KPI - Total Members** first. Once the Gender filter
changes that card, repeat the same pattern for the remaining questions.

If you do not want one of the filters to affect a card, remove that
`AND {{...}}` line from that card's SQL. The dashboard filter will then have
nothing to map to for that card.

---

## 1. KPI - Total Members

**Visualization:** Number

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

## 2. KPI - Active Personal Trainers

**Visualization:** Number

```sql
SELECT COUNT(DISTINCT name_personal_trainer) AS personal_trainers
FROM gym_members_wide
WHERE personal_training = TRUE
  AND {{gender}}
  AND {{abonoment_type}}
  AND {{personal_training}}
  AND {{uses_sauna}}
  AND {{attend_group_lesson}}
  AND {{drink_abo}};
```

> This card is already restricted to members with personal training. If the
> dashboard Personal Training filter is set to **False**, this card correctly
> returns `0`.

## 3. KPI - Group Lessons

**Visualization:** Number

```sql
SELECT COUNT(DISTINCT ml.lesson) AS group_lessons
FROM gym_member_lessons ml
JOIN gym_members_wide ON gym_members_wide.id = ml.id
WHERE {{gender}}
  AND {{abonoment_type}}
  AND {{personal_training}}
  AND {{uses_sauna}}
  AND {{attend_group_lesson}}
  AND {{drink_abo}};
```

> The original query only used `gym_member_lessons`, which has no gender or
> membership columns. This version joins to `gym_members_wide` so the member
> filters can be applied. With no filters selected, it still returns `11`.

## 4. KPI - Average Visits per Week

**Visualization:** Number

```sql
SELECT ROUND(AVG(visit_per_week), 1) AS avg_visits_per_week
FROM gym_members_wide
WHERE {{gender}}
  AND {{abonoment_type}}
  AND {{personal_training}}
  AND {{uses_sauna}}
  AND {{attend_group_lesson}}
  AND {{drink_abo}};
```

## 5. KPI - Average Session Duration

**Visualization:** Number

```sql
SELECT ROUND(AVG(avg_time_in_gym)) AS avg_minutes_in_gym
FROM gym_members_wide
WHERE {{gender}}
  AND {{abonoment_type}}
  AND {{personal_training}}
  AND {{uses_sauna}}
  AND {{attend_group_lesson}}
  AND {{drink_abo}};
```

## 6. Chart - Membership Type Distribution

**Visualization:** Pie chart or Bar chart

```sql
SELECT abonoment_type, COUNT(*) AS members
FROM gym_members_wide
WHERE {{gender}}
  AND {{abonoment_type}}
  AND {{personal_training}}
  AND {{uses_sauna}}
  AND {{attend_group_lesson}}
  AND {{drink_abo}}
GROUP BY abonoment_type
ORDER BY members DESC;
```

## 7. Chart - Gender Distribution

**Visualization:** Pie chart or Bar chart

```sql
SELECT gender, COUNT(*) AS members
FROM gym_members_wide
WHERE {{gender}}
  AND {{abonoment_type}}
  AND {{personal_training}}
  AND {{uses_sauna}}
  AND {{attend_group_lesson}}
  AND {{drink_abo}}
GROUP BY gender
ORDER BY members DESC;
```

## 8. Chart - Age Groups

**Visualization:** Bar chart

```sql
SELECT CASE
         WHEN age < 18 THEN '< 18'
         WHEN age < 25 THEN '18-24'
         WHEN age < 35 THEN '25-34'
         WHEN age < 45 THEN '35-44'
         ELSE '45+'
       END AS age_group,
       COUNT(*) AS members
FROM gym_members_wide
WHERE {{gender}}
  AND {{abonoment_type}}
  AND {{personal_training}}
  AND {{uses_sauna}}
  AND {{attend_group_lesson}}
  AND {{drink_abo}}
GROUP BY age_group
ORDER BY MIN(age);
```

## 9. Chart - Personal Training Usage

**Visualization:** Pie chart or Bar chart

```sql
SELECT personal_training, COUNT(*) AS members
FROM gym_members_wide
WHERE {{gender}}
  AND {{abonoment_type}}
  AND {{personal_training}}
  AND {{uses_sauna}}
  AND {{attend_group_lesson}}
  AND {{drink_abo}}
GROUP BY personal_training;
```

## 10. Chart - Sauna Usage

**Visualization:** Pie chart or Bar chart

```sql
SELECT uses_sauna, COUNT(*) AS members
FROM gym_members_wide
WHERE {{gender}}
  AND {{abonoment_type}}
  AND {{personal_training}}
  AND {{uses_sauna}}
  AND {{attend_group_lesson}}
  AND {{drink_abo}}
GROUP BY uses_sauna;
```

## 11. Chart - Group Lesson Attendance

**Visualization:** Pie chart or Bar chart

```sql
SELECT attend_group_lesson, COUNT(*) AS members
FROM gym_members_wide
WHERE {{gender}}
  AND {{abonoment_type}}
  AND {{personal_training}}
  AND {{uses_sauna}}
  AND {{attend_group_lesson}}
  AND {{drink_abo}}
GROUP BY attend_group_lesson;
```

## 12. Chart - Drink Package Adoption

**Visualization:** Pie chart or Bar chart

```sql
SELECT drink_abo, COUNT(*) AS members
FROM gym_members_wide
WHERE {{gender}}
  AND {{abonoment_type}}
  AND {{personal_training}}
  AND {{uses_sauna}}
  AND {{attend_group_lesson}}
  AND {{drink_abo}}
GROUP BY drink_abo;
```

## 13. Chart - Visit Frequency Distribution

**Visualization:** Bar chart

```sql
SELECT visit_per_week, COUNT(*) AS members
FROM gym_members_wide
WHERE {{gender}}
  AND {{abonoment_type}}
  AND {{personal_training}}
  AND {{uses_sauna}}
  AND {{attend_group_lesson}}
  AND {{drink_abo}}
GROUP BY visit_per_week
ORDER BY visit_per_week;
```

## 14. Chart - Session Duration Distribution

**Visualization:** Bar chart

```sql
SELECT CASE
         WHEN avg_time_in_gym < 45 THEN '< 45'
         WHEN avg_time_in_gym < 60 THEN '45-59'
         WHEN avg_time_in_gym < 90 THEN '60-89'
         WHEN avg_time_in_gym < 120 THEN '90-119'
         WHEN avg_time_in_gym < 150 THEN '120-149'
         ELSE '150+'
       END AS duration_bucket,
       COUNT(*) AS members
FROM gym_members_wide
WHERE {{gender}}
  AND {{abonoment_type}}
  AND {{personal_training}}
  AND {{uses_sauna}}
  AND {{attend_group_lesson}}
  AND {{drink_abo}}
GROUP BY duration_bucket
ORDER BY MIN(avg_time_in_gym);
```

## 15. Chart - Weekly Activity

**Visualization:** Bar chart

```sql
SELECT d.day, COUNT(*) AS members
FROM gym_members_wide
CROSS JOIN LATERAL (
  VALUES
    ('Mon', 1, gym_members_wide.visit_mon),
    ('Tue', 2, gym_members_wide.visit_tue),
    ('Wed', 3, gym_members_wide.visit_wed),
    ('Thu', 4, gym_members_wide.visit_thu),
    ('Fri', 5, gym_members_wide.visit_fri),
    ('Sat', 6, gym_members_wide.visit_sat),
    ('Sun', 7, gym_members_wide.visit_sun)
) AS d(day, day_order, selected)
WHERE d.selected
  AND {{gender}}
  AND {{abonoment_type}}
  AND {{personal_training}}
  AND {{uses_sauna}}
  AND {{attend_group_lesson}}
  AND {{drink_abo}}
GROUP BY d.day, d.day_order
ORDER BY d.day_order;
```

## 16. Chart - Hourly Check-in and Check-out Trend

**Visualization:** Line chart

```sql
WITH filtered_members AS (
  SELECT *
  FROM gym_members_wide
  WHERE {{gender}}
    AND {{abonoment_type}}
    AND {{personal_training}}
    AND {{uses_sauna}}
    AND {{attend_group_lesson}}
    AND {{drink_abo}}
),
events AS (
  SELECT EXTRACT(HOUR FROM avg_time_check_in)::int AS hour,
         'Check-in' AS event
  FROM filtered_members
  UNION ALL
  SELECT EXTRACT(HOUR FROM avg_time_check_out)::int AS hour,
         'Check-out' AS event
  FROM filtered_members
)
SELECT hour, event, COUNT(*) AS members
FROM events
GROUP BY hour, event
ORDER BY hour, event;
```

> The filters are applied inside `filtered_members`, before the check-in and
> check-out events are created.

## 17. Chart - Lesson Popularity

**Visualization:** Bar chart, sorted descending

```sql
SELECT l.lesson, COUNT(*) AS members
FROM gym_members_wide
CROSS JOIN LATERAL (
  VALUES
    ('BodyBalance', gym_members_wide.lesson_bodybalance),
    ('BodyPump', gym_members_wide.lesson_bodypump),
    ('HIT', gym_members_wide.lesson_hit),
    ('Kickboxen', gym_members_wide.lesson_kickboxen),
    ('LesMiles', gym_members_wide.lesson_lesmiles),
    ('Pilates', gym_members_wide.lesson_pilates),
    ('Running', gym_members_wide.lesson_running),
    ('Spinning', gym_members_wide.lesson_spinning),
    ('XCore', gym_members_wide.lesson_xcore),
    ('Yoga', gym_members_wide.lesson_yoga),
    ('Zumba', gym_members_wide.lesson_zumba)
) AS l(lesson, selected)
WHERE l.selected
  AND {{gender}}
  AND {{abonoment_type}}
  AND {{personal_training}}
  AND {{uses_sauna}}
  AND {{attend_group_lesson}}
  AND {{drink_abo}}
GROUP BY l.lesson
ORDER BY members DESC;
```

## 18. Chart - Drink Popularity

**Visualization:** Bar chart, sorted descending

```sql
SELECT d.drink, COUNT(*) AS members
FROM gym_members_wide
CROSS JOIN LATERAL (
  VALUES
    ('berry_boost', gym_members_wide.drink_berry_boost),
    ('black_currant', gym_members_wide.drink_black_currant),
    ('coconut_pineapple', gym_members_wide.drink_coconut_pineapple),
    ('lemon', gym_members_wide.drink_lemon),
    ('orange', gym_members_wide.drink_orange),
    ('passion_fruit', gym_members_wide.drink_passion_fruit)
) AS d(drink, selected)
WHERE d.selected
  AND {{gender}}
  AND {{abonoment_type}}
  AND {{personal_training}}
  AND {{uses_sauna}}
  AND {{attend_group_lesson}}
  AND {{drink_abo}}
GROUP BY d.drink
ORDER BY members DESC;
```

## 19. Chart - Trainer Popularity

**Visualization:** Bar chart, sorted descending

```sql
SELECT name_personal_trainer AS trainer, COUNT(*) AS members
FROM gym_members_wide
WHERE personal_training = TRUE
  AND {{gender}}
  AND {{abonoment_type}}
  AND {{personal_training}}
  AND {{uses_sauna}}
  AND {{attend_group_lesson}}
  AND {{drink_abo}}
GROUP BY name_personal_trainer
ORDER BY members DESC;
```

> This card is already restricted to members with personal training. If the
> dashboard Personal Training filter is set to **False**, this card correctly
> returns no rows.

## 20. Table - Member Detail

**Visualization:** Table

```sql
SELECT id,
       gender,
       age,
       abonoment_type,
       visit_per_week,
       attend_group_lesson,
       drink_abo,
       personal_training,
       name_personal_trainer,
       uses_sauna,
       avg_time_in_gym
FROM gym_members_wide
WHERE {{gender}}
  AND {{abonoment_type}}
  AND {{personal_training}}
  AND {{uses_sauna}}
  AND {{attend_group_lesson}}
  AND {{drink_abo}}
ORDER BY id;
```

---

## Behavior notes

- A dashboard filter only affects the cards where it is mapped. If you do not
  map a filter to a card, that card ignores the filter.
- Use `WHERE {{gender}}`, not `WHERE gender = {{gender}}`. The Field Filter
  inserts the column name, operator, and value handling for you.
- Use **Boolean** dashboard filters for `personal_training`, `uses_sauna`,
  `attend_group_lesson`, and `drink_abo`. A Text or Category filter may produce
  a type mismatch on a boolean column.
- `KPI - Active Personal Trainers` and `Chart - Trainer Popularity` already
  filter to `personal_training = TRUE`. If the Personal Training dashboard
  filter is set to **False**, those cards will return `0` or no rows. That is
  expected.
- `KPI - Group Lessons` now joins `gym_member_lessons` to
  `gym_members_wide` on `gym_members_wide.id = ml.id`. Without the join, the
  card cannot be filtered by member attributes.
- The `Chart - Hourly Check-in and Check-out Trend` query applies the filters
  inside the `filtered_members` CTE, so the check-in/check-out counts are based
  only on the selected members.
- If you use a plain **Text** variable instead, the SQL must be
  `WHERE gender = {{gender}}`, and the dashboard filter must be set to
  **A single value**. Field Filters are the better option for dashboards.

## Troubleshooting

- **“A text variable in this card…”** — the card has no Field Filter
  variable, or the variable is still set to the Text type. Add the `{{...}}`
  tag and change the variable type to Field Filter.
- **“Cannot run the query: missing required parameters: …”** — the variables
  are still type **Text**, or **Always require a value** is on. Change them
  to **Field Filter**, map each field, and turn off **Always require a
  value** if you want the question to run unfiltered.
- **“argument of AND must be type boolean, not type character varying”** — a
  Text variable was used with `[[AND {{gender}}]]` and a value was supplied.
  Metabase substituted only the value, producing `AND 'Female'`. Change the
  variable to **Field Filter** and map it to the field.
- **“column … does not exist”** — the field filter is mapped to the wrong
  table/field, or the SQL aliases the table and the alias setting is missing.
- **“operator does not exist: boolean = character varying”** — a boolean
  column is connected to a Text or Category filter. Change the dashboard
  filter to Boolean.
- **The filter does not appear in the dashboard mapping panel** — save the
  question, then reload the dashboard editor.
- **The filter changes one card but not another** — the other card does not
  have the matching variable mapped. Add the variable to that card and map it.

## Verification

With no dashboard filters selected, the updated queries should return the same
unfiltered results as the original guide:

- Total Members: `1000`
- Membership Type distribution totals: `1000`
- Gender distribution totals: `1000`
- Active Personal Trainers: `4`
- Group Lessons: `11`
- Lesson Popularity rows total: `1003` selections
- Drink Popularity rows total: `719` selections
- Weekly Activity rows total: `2682` member-days

Then test one filter at a time:

- Gender = Female should reduce Total Members to the female count.
- Membership Type = Premium should reduce Total Members to the premium count.
- Each boolean filter should switch between the TRUE and FALSE populations.
- Clearing a filter should restore the unfiltered totals.

## Reference

- Metabase Field Filters:
  <https://www.metabase.com/docs/latest/questions/native-editor/field-filters>
- Metabase dashboard filters:
  <https://www.metabase.com/docs/latest/dashboards/filters>
