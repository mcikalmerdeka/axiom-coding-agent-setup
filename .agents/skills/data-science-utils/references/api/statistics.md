# Statistics API

Source: `scripts/utils/statistics.py`

> Auto-generated from the bundled source. Re-run
> `python scripts/dev/generate_references.py` after changing the package.


Descriptive statistics for numerical, categorical, and date columns plus distribution typing.

## Quick index

| Name | Summary |
| --- | --- |
| `describe_numerical_combined` | Generate descriptive statistics for numerical columns in a dataframe, both overall and optionally grouped by a categorical variable |
| `describe_categorical_combined` | Generate descriptive statistics for categorical columns in a dataframe, both overall and optionally grouped by a categorical variable |
| `describe_date_columns` | Comprehensive analysis of date columns including various temporal features |
| `identify_distribution_types` | Identifies and categorizes the distribution type of each numerical column based on skewness and kurtosis |

### `describe_numerical_combined`

```python
def describe_numerical_combined(data: pd.DataFrame, col_series: List[str], hue: Optional[str]=None) -> pd.DataFrame
```

Generate descriptive statistics for numerical columns in a dataframe,
both overall and optionally grouped by a categorical variable.

Parameters:
data (pd.DataFrame): The dataframe containing the numerical columns
col_series (List[str]): The list of numerical columns to describe
hue (Optional[str], optional): The name of the categorical column to group by

Returns:
pd.DataFrame: A dataframe containing descriptive statistics, with hue classes if specified

**Examples**
>>> # Overall statistics only
>>> stats = describe_numerical_combined(df, ['age', 'salary', 'experience'])

>>> # Statistics grouped by a categorical variable
>>> stats = describe_numerical_combined(df, ['age', 'salary'], hue='department')

### `describe_categorical_combined`

```python
def describe_categorical_combined(data: pd.DataFrame, col_series: List[str], hue: Optional[str]=None) -> pd.DataFrame
```

Generate descriptive statistics for categorical columns in a dataframe,
both overall and optionally grouped by a categorical variable.

Parameters:
data (pd.DataFrame): The dataframe containing the categorical columns
col_series (List[str]): The list of categorical columns to describe
hue (Optional[str], optional): The name of the categorical column to group by

Returns:
pd.DataFrame: A dataframe containing descriptive statistics, with hue classes if specified

**Examples**
>>> # Overall statistics only
>>> stats = describe_categorical_combined(df, ['gender', 'department', 'job_title'])

>>> # Statistics grouped by a categorical variable
>>> stats = describe_categorical_combined(df, ['gender', 'job_title'], hue='department')

### `describe_date_columns`

```python
def describe_date_columns(df: pd.DataFrame, date_columns: List[str]) -> pd.DataFrame
```

Comprehensive analysis of date columns including various temporal features

Parameters:
df (pd.DataFrame): DataFrame containing date columns
date_columns (List[str]): List of column names containing dates

Returns:
pd.DataFrame: dates_summary statistics and temporal features for each date column

**Examples**
>>> # Analyze single date column
>>> date_stats = describe_date_columns(df, ['purchase_date'])

>>> # Analyze multiple date columns
>>> date_stats = describe_date_columns(df, ['start_date', 'end_date', 'modified_date'])

### `identify_distribution_types`

```python
def identify_distribution_types(df: pd.DataFrame, col_series: List[str], uniform_cols: Optional[List[str]]=None, multimodal_cols: Optional[List[str]]=None) -> pd.DataFrame
```

Identifies and categorizes the distribution type of each numerical column
based on skewness and kurtosis.

Skewness thresholds:
    |skew| < 0.2  → Normal / Symmetric
    0.2 ≤ |skew| < 0.5  → Slightly skewed
    0.5 ≤ |skew| < 1.0  → Moderately skewed
    |skew| ≥ 1.0  → Highly skewed

Kurtosis (excess, Fisher definition):
    < -0.5  → Platykurtic (light-tailed / flat)
    -0.5 to 0.5  → Mesokurtic (normal-like)
    > 0.5  → Leptokurtic (heavy-tailed / peaked)

Parameters
----------
df : pd.DataFrame
    Input DataFrame.
col_series : List[str]
    Column names to analyze.
uniform_cols : List[str], optional
    Columns to manually override as Uniform Distribution.
multimodal_cols : List[str], optional
    Columns to manually override as Multi-modal Distribution.

Returns
-------
pd.DataFrame
    Columns: Column Name, Mean, Median, Mode, Skewness, Kurtosis,
             Skewness Type, Kurtosis Type.

Examples
--------
>>> result = identify_distribution_types(df, df.select_dtypes('number').columns.tolist())
>>> result = identify_distribution_types(df, num_cols, uniform_cols=['Age'], multimodal_cols=['Income'])
