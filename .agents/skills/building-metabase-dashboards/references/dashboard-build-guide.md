# Dashboard Build Guide

Practical order for building the Gym Membership dashboard in Metabase.

## Short answer: build Questions first

A Metabase dashboard does not contain SQL directly. It displays **cards**, and
each card is backed by a **Question** (a saved query).

Use this order:

1. Create a reusable **Model** from the wide table.
2. Create and save **Questions** in your collection.
3. Create the **Dashboard** and add those saved questions.
4. Add dashboard **filters** and map them to the cards.
5. Format, test, and publish.

You can create a question from inside a dashboard, but saving questions in the
collection first makes them easier to reuse, edit, and debug.

## Step 1: Use the wide table as the dashboard base

For this dashboard, use `gym_members_wide` as the primary table. It has one row
per member and contains:

- Demographics: `gender`, `age`, `abonoment_type`
- Usage: `visit_per_week`, check-in/out times, session duration
- Flags: `attend_group_lesson`, `drink_abo`, `personal_training`, `uses_sauna`
- One-hot preferences: `visit_*`, `lesson_*`, `drink_*`
- Counts: `n_fav_lessons`, `n_fav_drinks`

This keeps every card on one table, so dashboard filters are much easier to
map. The star-schema tables remain available for separate analyses.

### Create the Model

1. Open your collection.
2. Click **+ New -> Model**.
3. Choose the `gym` database and the `gym_members_wide` table.
4. Name it **Gym Members - Wide**.
5. Add a short description and save it in your collection.

Use this model as the source for the member-level questions below.

## Step 2: Create the Questions

For each card:

1. Click **+ New -> Question**.
2. Choose **Gym Members - Wide** (or use **Native query** for the SQL below).
3. Configure the question.
4. Choose the visualization.
5. Click **Save**, name it, and save it in your collection.

Use a consistent naming convention:

```text
KPI - Total Members
Chart - Membership Type
Chart - Weekly Activity
Table - Member Detail
```

## Step 3: Recommended build order

Build the dashboard in sections. Start with the KPI row, then demographics,
then usage, then the detail table.

|   # | Question name                         | Visualization | Source      |
| --: | ------------------------------------- | ------------- | ----------- |
|   1 | KPI - Total Members                   | Number        | Wide table  |
|   2 | KPI - Active Personal Trainers        | Number        | Wide table  |
|   3 | KPI - Group Lessons                   | Number        | Lesson list |
|   4 | KPI - Average Visits per Week         | Number        | Wide table  |
|   5 | KPI - Average Session Duration        | Number        | Wide table  |
|   6 | Chart - Membership Type               | Pie or bar    | Wide table  |
|   7 | Chart - Gender Distribution           | Pie or bar    | Wide table  |
|   8 | Chart - Age Groups                    | Bar           | Wide table  |
|   9 | Chart - Personal Training Usage       | Pie or bar    | Wide table  |
|  10 | Chart - Sauna Usage                   | Pie or bar    | Wide table  |
|  11 | Chart - Group Lesson Attendance       | Pie or bar    | Wide table  |
|  12 | Chart - Drink Package Adoption        | Pie or bar    | Wide table  |
|  13 | Chart - Visit Frequency Distribution  | Bar           | Wide table  |
|  14 | Chart - Session Duration Distribution | Bar           | Wide table  |
|  15 | Chart - Weekly Activity               | Bar           | Wide table  |
|  16 | Chart - Hourly Check-in and Check-out | Line          | Wide table  |
|  17 | Chart - Lesson Popularity             | Bar           | Wide table  |
|  18 | Chart - Drink Popularity              | Bar           | Wide table  |
|  19 | Chart - Trainer Popularity            | Bar           | Wide table  |
|  20 | Table - Member Detail                 | Table         | Wide table  |

## Question descriptions

Use these in the optional **Description** field when saving each question.

| Question                              | Description                                                                                                                                 |
| ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| KPI - Total Members                   | Count of unique gym members in the analysis-ready dataset. Use this as the denominator for member-level percentages.                        |
| KPI - Active Personal Trainers        | Count of distinct personal trainers assigned to at least one member with personal training enabled.                                         |
| KPI - Group Lessons                   | Count of distinct group lessons selected by members in this dataset.                                                                        |
| KPI - Average Visits per Week         | Average number of planned gym visits per member per week, based on the visit_per_week field.                                                |
| KPI - Average Session Duration        | Average time spent in the gym per visit, in minutes, based on the avg_time_in_gym field.                                                    |
| Chart - Membership Type               | Number of members by membership plan: Standard or Premium.                                                                                  |
| Chart - Gender Distribution           | Number of members by gender.                                                                                                                |
| Chart - Age Groups                    | Member count by age band: under 18, 18-24, 25-34, 35-44, and 45 and above.                                                                  |
| Chart - Personal Training Usage       | Number of members who use a personal trainer versus those who do not.                                                                       |
| Chart - Sauna Usage                   | Number of members who use the sauna versus those who do not.                                                                                |
| Chart - Group Lesson Attendance       | Number of members who attend group lessons versus those who do not.                                                                         |
| Chart - Drink Package Adoption        | Number of members with a drink package versus those without one.                                                                            |
| Chart - Visit Frequency Distribution  | Number of members for each planned weekly visit count, from one to five visits per week.                                                    |
| Chart - Session Duration Distribution | Member count by average session length bucket, measured in minutes.                                                                         |
| Chart - Weekly Activity               | Number of members who typically visit on each day of the week. A member can be counted on more than one day.                                |
| Chart - Hourly Check-in and Check-out | Distribution of average check-in and check-out times by hour of day. Counts represent members, not individual visits.                       |
| Chart - Lesson Popularity             | Number of members who selected each group lesson as a favourite. Members can select up to three lessons, so totals exceed the member count. |
| Chart - Drink Popularity              | Number of members who selected each drink as a favourite. Members can select up to two drinks, so totals exceed the member count.           |
| Chart - Trainer Popularity            | Number of members assigned to each personal trainer, among members who use personal training.                                               |
| Table - Member Detail                 | One row per member with key demographic, membership, usage, and preference fields for drill-down and verification.                          |

## Step 4: Verified SQL for each card

Use **Native query** for the cards below. The SQL has been tested against the
running `gym` database.

> If you plan to use the dashboard filters in Step 6, use the field-filtered
> versions in [dashboard-sql-with-filters.md](dashboard-sql-with-filters.md).
> The SQL below has no variables and cannot be mapped to dashboard filters
> as-is.

### 1. Total Members

```sql
SELECT COUNT(*) AS total_members
FROM gym_members_wide;
```

Visualization: **Number**.

### 2. Active Personal Trainers

```sql
SELECT COUNT(DISTINCT name_personal_trainer) AS personal_trainers
FROM gym_members_wide
WHERE personal_training = TRUE;
```

Visualization: **Number**.

### 3. Group Lessons

```sql
SELECT COUNT(DISTINCT lesson) AS group_lessons
FROM gym_member_lessons;
```

Visualization: **Number**.

### 4. Average Visits per Week

```sql
SELECT ROUND(AVG(visit_per_week), 1) AS avg_visits_per_week
FROM gym_members_wide;
```

Visualization: **Number**.

### 5. Average Session Duration

```sql
SELECT ROUND(AVG(avg_time_in_gym)) AS avg_minutes_in_gym
FROM gym_members_wide;
```

Visualization: **Number**.

### 6. Membership Type Distribution

```sql
SELECT abonoment_type, COUNT(*) AS members
FROM gym_members_wide
GROUP BY abonoment_type
ORDER BY members DESC;
```

Visualization: **Pie chart** or **Bar chart**.

- Category: `abonoment_type`
- Measure: `members`

### 7. Gender Distribution

```sql
SELECT gender, COUNT(*) AS members
FROM gym_members_wide
GROUP BY gender
ORDER BY members DESC;
```

Visualization: **Pie chart** or **Bar chart**.

### 8. Age Groups

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
GROUP BY age_group
ORDER BY MIN(age);
```

Visualization: **Bar chart**.

### 9. Personal Training Usage

```sql
SELECT personal_training, COUNT(*) AS members
FROM gym_members_wide
GROUP BY personal_training;
```

Visualization: **Pie chart** or **Bar chart**.

### 10. Sauna Usage

```sql
SELECT uses_sauna, COUNT(*) AS members
FROM gym_members_wide
GROUP BY uses_sauna;
```

Visualization: **Pie chart** or **Bar chart**.

### 11. Group Lesson Attendance

```sql
SELECT attend_group_lesson, COUNT(*) AS members
FROM gym_members_wide
GROUP BY attend_group_lesson;
```

Visualization: **Pie chart** or **Bar chart**.

### 12. Drink Package Adoption

```sql
SELECT drink_abo, COUNT(*) AS members
FROM gym_members_wide
GROUP BY drink_abo;
```

Visualization: **Pie chart** or **Bar chart**.

### 13. Visit Frequency Distribution

```sql
SELECT visit_per_week, COUNT(*) AS members
FROM gym_members_wide
GROUP BY visit_per_week
ORDER BY visit_per_week;
```

Visualization: **Bar chart**.

### 14. Session Duration Distribution

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
GROUP BY duration_bucket
ORDER BY MIN(avg_time_in_gym);
```

Visualization: **Bar chart**.

### 15. Weekly Activity

```
SELECT d.day, COUNT(*) AS members
FROM gym_members_wide w
CROSS JOIN LATERAL (
  VALUES
    ('Mon', 1, w.visit_mon),
    ('Tue', 2, w.visit_tue),
    ('Wed', 3, w.visit_wed),
    ('Thu', 4, w.visit_thu),
    ('Fri', 5, w.visit_fri),
    ('Sat', 6, w.visit_sat),
    ('Sun', 7, w.visit_sun)
) AS d(day, day_order, selected)
WHERE d.selected
GROUP BY d.day, d.day_order
ORDER BY d.day_order;
```

Visualization: **Bar chart**.

### 16. Hourly Check-in and Check-out Trend

```sql
WITH events AS (
  SELECT EXTRACT(HOUR FROM avg_time_check_in)::int AS hour,
         'Check-in' AS event
  FROM gym_members_wide
  UNION ALL
  SELECT EXTRACT(HOUR FROM avg_time_check_out)::int AS hour,
         'Check-out' AS event
  FROM gym_members_wide
)
SELECT hour, event, COUNT(*) AS members
FROM events
GROUP BY hour, event
ORDER BY hour, event;
```

Visualization: **Line chart**.

- X-axis: `hour`
- Y-axis: `members`
- Series breakout: `event`

### 17. Lesson Popularity

```sql
SELECT l.lesson, COUNT(*) AS members
FROM gym_members_wide w
CROSS JOIN LATERAL (
  VALUES
    ('BodyBalance', w.lesson_bodybalance),
    ('BodyPump', w.lesson_bodypump),
    ('HIT', w.lesson_hit),
    ('Kickboxen', w.lesson_kickboxen),
    ('LesMiles', w.lesson_lesmiles),
    ('Pilates', w.lesson_pilates),
    ('Running', w.lesson_running),
    ('Spinning', w.lesson_spinning),
    ('XCore', w.lesson_xcore),
    ('Yoga', w.lesson_yoga),
    ('Zumba', w.lesson_zumba)
) AS l(lesson, selected)
WHERE l.selected
GROUP BY l.lesson
ORDER BY members DESC;
```

Visualization: **Bar chart**, sorted descending.

### 18. Drink Popularity

```sql
SELECT d.drink, COUNT(*) AS members
FROM gym_members_wide w
CROSS JOIN LATERAL (
  VALUES
    ('berry_boost', w.drink_berry_boost),
    ('black_currant', w.drink_black_currant),
    ('coconut_pineapple', w.drink_coconut_pineapple),
    ('lemon', w.drink_lemon),
    ('orange', w.drink_orange),
    ('passion_fruit', w.drink_passion_fruit)
) AS d(drink, selected)
WHERE d.selected
GROUP BY d.drink
ORDER BY members DESC;
```

Visualization: **Bar chart**, sorted descending.

### 19. Trainer Popularity

```sql
SELECT name_personal_trainer AS trainer, COUNT(*) AS members
FROM gym_members_wide
WHERE personal_training = TRUE
GROUP BY name_personal_trainer
ORDER BY members DESC;
```

Visualization: **Bar chart**, sorted descending.

### 20. Member Detail

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
ORDER BY id;
```

Visualization: **Table**.

## Step 5: Create the Dashboard

1. Open your collection.
2. Click **+ New -> Dashboard**.
3. Name it **Gym Membership Operational Dashboard**.
4. Click the pencil/edit icon.
5. Click **Add a card -> Saved questions**.
6. Add the questions in the order above.

Suggested layout:

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

## Step 6: Add dashboard filters

Start with these filters:

| Filter                  | Type             | Column                |
| ----------------------- | ---------------- | --------------------- |
| Gender                  | Text or Category | `gender`              |
| Membership Type         | Text or Category | `abonoment_type`      |
| Personal Training       | Boolean          | `personal_training`   |
| Sauna Usage             | Boolean          | `uses_sauna`          |
| Group Lesson Attendance | Boolean          | `attend_group_lesson` |
| Drink Package           | Boolean          | `drink_abo`           |

To add a filter:

1. Edit the dashboard.
2. Click **Add a filter**.
3. Choose the filter type.
4. For each card, map the filter to the matching column or variable.
5. Save the dashboard.

If you are keeping the questions as **Native SQL**, the queries in Step 4 do
not contain variables, so Metabase has nothing to map the filters to. Use the
field-filtered versions in
[dashboard-sql-with-filters.md](dashboard-sql-with-filters.md) instead.

### Important filter behavior

A filter only affects cards where it is mapped. For cards built with the query
builder on `gym_members_wide`, Metabase knows the columns and mapping is
straightforward.

For native SQL cards, every card needs a **Field Filter** variable for each
filter you want to apply. A raw SQL column cannot be mapped directly. If a
filter does not map to a native card, you have two options:

- Leave that card unfiltered.
- Add the Field Filter variable to the SQL and map it in the question settings.

Do not force a filter mapping that changes the meaning of a card. Test each
filter after mapping.

## Step 7: Format and test

### Formatting

- KPI cards: one row, equal width, no unnecessary decimals.
- Pie charts: show legend and percentage labels.
- Bar charts: sort descending for popularity; keep source order for days and
  visit frequency.
- Line chart: use a distinct color for check-ins and check-outs.
- Tables: hide unnecessary columns, set a sensible row limit, and enable
  downloads if useful.
- Add a short description to each card explaining what it measures.

### QA checklist

- [ ] Total members equals 1,000.
- [ ] Membership type totals equal 1,000.
- [ ] Gender totals equal 1,000.
- [ ] Lesson popularity rows sum to 1,003 selections.
- [ ] Drink popularity rows sum to 719 selections.
- [ ] Weekly activity rows sum to 2,682 member-days.
- [ ] Every filter changes the intended cards and can be cleared.
- [ ] No card shows an error or an empty result unexpectedly.
- [ ] Dashboard is saved in the project collection.

## When to use the star schema instead

Use `gym_members_clean` and the three bridge tables when you need:

- A strictly normalized relational model.
- Separate analyses of days, lessons, or drinks without one-hot columns.
- A dashboard where popularity cards are filtered by member attributes and you
  are comfortable using joins or SQL field filters.

The wide table is the recommended starting point for this dashboard because it
keeps filters and questions simple. You can always add star-schema cards later.
