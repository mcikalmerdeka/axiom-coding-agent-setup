# Time series API

Source: `scripts/utils/time_series.py`

> Auto-generated from the bundled source. Re-run
> `python scripts/dev/generate_references.py` after changing the package.


Decomposition, stationarity, feature engineering, splitting, diagnostics, and forecast metrics.

## Quick index

| Name | Summary |
| --- | --- |
| `decompose_series` | Decompose a time series into trend, seasonal, and residual components |
| `adf_test` | Perform the Augmented Dickey-Fuller test for stationarity |
| `kpss_test` | Perform the Kwiatkowski-Phillips-Schmidt-Shin (KPSS) test for stationarity |
| `check_stationarity` | Run both ADF and KPSS stationarity tests and return a summary DataFrame |
| `make_stationary` | Attempt to make a time series stationary using differencing |
| `create_lag_features` | Create lagged versions of specified columns |
| `create_rolling_features` | Create rolling-window statistics for specified columns |
| `create_date_features` | Extract common date/time features from a datetime column |
| `split_time_series` | Split a time-ordered DataFrame into train and test sets without shuffling |
| `time_series_cv_splits` | Generate walk-forward cross-validation splits for time series |
| `evaluate_forecast` | Compute common time-series forecast accuracy metrics |
| `plot_acf_pacf` | Plot the Autocorrelation Function (ACF) and Partial Autocorrelation Function (PACF) |
| `detect_outliers_iqr` | Detect outliers in a time series using the IQR method |
| `interpolate_series` | Interpolate missing values in a time series |
| `resample_series` | Resample a time series to a different frequency |
| `get_acf_pacf_values` | Compute ACF and PACF values with confidence intervals |

### `decompose_series`

```python
def decompose_series(series: pd.Series, model: str='additive', period: Optional[int]=None, plot: bool=True, figsize: Tuple[int, int]=(14, 10)) -> Dict[str, Any]
```

Decompose a time series into trend, seasonal, and residual components.

Parameters
----------
series : pd.Series
    The time series to decompose.
model : str, default='additive'
    Type of seasonal component: 'additive' or 'multiplicative'.
period : Optional[int], default=None
    Seasonal period. If None, inferred from the index frequency or defaults
    to a sensible value.
plot : bool, default=True
    Whether to display the decomposition plot.
figsize : Tuple[int, int], default=(14, 10)
    Figure size for the plot.

Returns
-------
Dict[str, Any]
    Dictionary containing:
    - 'observed': original series
    - 'trend': trend component
    - 'seasonal': seasonal component
    - 'residual': residual component
    - 'model': model used
    - 'period': period used

Examples
--------
>>> result = decompose_series(df['sales'], model='additive', period=12)
>>> trend = result['trend']

### `adf_test`

```python
def adf_test(series: pd.Series, alpha: float=0.05) -> Dict[str, Any]
```

Perform the Augmented Dickey-Fuller test for stationarity.

Parameters
----------
series : pd.Series
    The time series to test.
alpha : float, default=0.05
    Significance level.

Returns
-------
Dict[str, Any]
    Dictionary with test statistic, p-value, critical values, used lag,
    number of observations, and interpretation.

Examples
--------
>>> result = adf_test(df['sales'])
>>> print(result['is_stationary'])

### `kpss_test`

```python
def kpss_test(series: pd.Series, alpha: float=0.05, regression: str='c') -> Dict[str, Any]
```

Perform the Kwiatkowski-Phillips-Schmidt-Shin (KPSS) test for stationarity.

The null hypothesis of the KPSS test is that the series is stationary.

Parameters
----------
series : pd.Series
    The time series to test.
alpha : float, default=0.05
    Significance level.
regression : str, default='c'
    'c' for constant, 'ct' for constant and trend.

Returns
-------
Dict[str, Any]
    Dictionary with test statistic, p-value, critical values, lags used,
    and interpretation.

Examples
--------
>>> result = kpss_test(df['sales'])
>>> print(result['is_stationary'])

### `check_stationarity`

```python
def check_stationarity(series: pd.Series, alpha: float=0.05) -> pd.DataFrame
```

Run both ADF and KPSS stationarity tests and return a summary DataFrame.

Parameters
----------
series : pd.Series
    The time series to test.
alpha : float, default=0.05
    Significance level.

Returns
-------
pd.DataFrame
    DataFrame with test name, statistic, p-value, and conclusion.

Examples
--------
>>> check_stationarity(df['sales'])

### `make_stationary`

```python
def make_stationary(series: pd.Series, max_diff: int=2, alpha: float=0.05, seasonal_period: Optional[int]=None) -> Dict[str, Any]
```

Attempt to make a time series stationary using differencing.

Tries ordinary differencing first, then seasonal differencing if a period
is provided. Stops as soon as the ADF test indicates stationarity or the
maximum number of differences is reached.

Parameters
----------
series : pd.Series
    The time series to transform.
max_diff : int, default=2
    Maximum number of ordinary differences to apply.
alpha : float, default=0.05
    Significance level for the ADF test.
seasonal_period : Optional[int], default=None
    Seasonal period for seasonal differencing.

Returns
-------
Dict[str, Any]
    Dictionary containing:
    - 'transformed': the transformed series
    - 'n_diffs': number of ordinary differences applied
    - 'seasonal_diffs': number of seasonal differences applied
    - 'adf_result': final ADF test result
    - 'is_stationary': whether the final series is stationary

Examples
--------
>>> result = make_stationary(df['sales'], max_diff=2, seasonal_period=12)
>>> stationary_series = result['transformed']

### `create_lag_features`

```python
def create_lag_features(df: pd.DataFrame, columns: List[str], lags: List[int]=[1, 2, 3], drop_original: bool=False) -> pd.DataFrame
```

Create lagged versions of specified columns.

Parameters
----------
df : pd.DataFrame
    Input DataFrame.
columns : List[str]
    Columns to lag.
lags : List[int], default=[1, 2, 3]
    Lag steps to create.
drop_original : bool, default=False
    If True, drop the original columns and return only lag features.

Returns
-------
pd.DataFrame
    DataFrame with lag features added.

Examples
--------
>>> df_lags = create_lag_features(df, columns=['sales'], lags=[1, 7, 14])

### `create_rolling_features`

```python
def create_rolling_features(df: pd.DataFrame, columns: List[str], windows: List[int]=[3, 7, 14], aggregations: List[str]=['mean', 'std', 'min', 'max'], drop_original: bool=False) -> pd.DataFrame
```

Create rolling-window statistics for specified columns.

Parameters
----------
df : pd.DataFrame
    Input DataFrame.
columns : List[str]
    Columns to process.
windows : List[int], default=[3, 7, 14]
    Window sizes.
aggregations : List[str], default=['mean', 'std', 'min', 'max']
    Aggregation functions to apply. Must be valid pandas rolling methods.
drop_original : bool, default=False
    If True, drop the original columns and return only rolling features.

Returns
-------
pd.DataFrame
    DataFrame with rolling features added.

Examples
--------
>>> df_rolling = create_rolling_features(df, columns=['sales'], windows=[7, 30])

### `create_date_features`

```python
def create_date_features(df: pd.DataFrame, datetime_col: str, drop_original: bool=False) -> pd.DataFrame
```

Extract common date/time features from a datetime column.

Parameters
----------
df : pd.DataFrame
    Input DataFrame.
datetime_col : str
    Name of the datetime column.
drop_original : bool, default=False
    If True, drop the original datetime column.

Returns
-------
pd.DataFrame
    DataFrame with date features added.

Examples
--------
>>> df_dates = create_date_features(df, datetime_col='date')

### `split_time_series`

```python
def split_time_series(df: pd.DataFrame, test_size: Union[int, float]=0.2) -> Tuple[pd.DataFrame, pd.DataFrame]
```

Split a time-ordered DataFrame into train and test sets without shuffling.

Parameters
----------
df : pd.DataFrame
    Input DataFrame, assumed to be sorted by time.
test_size : Union[int, float], default=0.2
    If float, fraction of rows to use for testing. If int, number of rows.

Returns
-------
Tuple[pd.DataFrame, pd.DataFrame]
    (train_df, test_df)

Examples
--------
>>> train, test = split_time_series(df, test_size=0.2)

### `time_series_cv_splits`

```python
def time_series_cv_splits(df: pd.DataFrame, n_splits: int=5, test_size: Union[int, float]=0.2) -> List[Tuple[pd.DataFrame, pd.DataFrame]]
```

Generate walk-forward cross-validation splits for time series.

Parameters
----------
df : pd.DataFrame
    Input DataFrame, assumed to be sorted by time.
n_splits : int, default=5
    Number of CV splits.
test_size : Union[int, float], default=0.2
    Size of the test fold for each split.

Returns
-------
List[Tuple[pd.DataFrame, pd.DataFrame]]
    List of (train_df, test_df) tuples.

Examples
--------
>>> for train, test in time_series_cv_splits(df, n_splits=5):
...     model.fit(train)
...     model.predict(test)

### `evaluate_forecast`

```python
def evaluate_forecast(y_true: Union[pd.Series, np.ndarray, List[float]], y_pred: Union[pd.Series, np.ndarray, List[float]]) -> Dict[str, float]
```

Compute common time-series forecast accuracy metrics.

Parameters
----------
y_true : array-like
    Actual values.
y_pred : array-like
    Forecasted values.

Returns
-------
Dict[str, float]
    Dictionary with MAE, MSE, RMSE, MAPE, sMAPE, and MPE. MAPE is NaN
    when any actual value is zero, because the percentage error is
    undefined for those observations.

Examples
--------
>>> metrics = evaluate_forecast(y_test, y_pred)
>>> print(metrics['rmse'])

### `plot_acf_pacf`

```python
def plot_acf_pacf(series: pd.Series, lags: int=40, figsize: Tuple[int, int]=(14, 5), alpha: float=0.05) -> None
```

Plot the Autocorrelation Function (ACF) and Partial Autocorrelation Function (PACF).

Parameters
----------
series : pd.Series
    The time series.
lags : int, default=40
    Number of lags to plot.
figsize : Tuple[int, int], default=(14, 5)
    Figure size.
alpha : float, default=0.05
    Significance level for confidence intervals.

Examples
--------
>>> plot_acf_pacf(df['sales'], lags=40)

### `detect_outliers_iqr`

```python
def detect_outliers_iqr(series: pd.Series, k: float=1.5) -> pd.Series
```

Detect outliers in a time series using the IQR method.

Parameters
----------
series : pd.Series
    The time series.
k : float, default=1.5
    IQR multiplier. Larger values are more lenient.

Returns
-------
pd.Series
    Boolean mask where True indicates an outlier.

Examples
--------
>>> outlier_mask = detect_outliers_iqr(df['sales'])
>>> df.loc[outlier_mask]

### `interpolate_series`

```python
def interpolate_series(series: pd.Series, method: str='time', limit: Optional[int]=None) -> pd.Series
```

Interpolate missing values in a time series.

Parameters
----------
series : pd.Series
    The time series with missing values.
method : str, default='time'
    Interpolation method. For time-series indices, 'time' or 'linear' are
    common choices.
limit : Optional[int], default=None
    Maximum number of consecutive NaNs to fill.

Returns
-------
pd.Series
    Series with missing values interpolated.

Examples
--------
>>> filled = interpolate_series(df['sales'], method='time')

### `resample_series`

```python
def resample_series(series: pd.Series, rule: str, aggregation: str='mean') -> pd.Series
```

Resample a time series to a different frequency.

Parameters
----------
series : pd.Series
    The time series, ideally with a DatetimeIndex.
rule : str
    Pandas offset string, e.g. 'D', 'W', 'M', 'Q', 'H'.
aggregation : str, default='mean'
    Aggregation method to apply after resampling. Must be one of
    'mean', 'sum', 'min', 'max', 'median', 'first', 'last', 'count',
    'std', or 'var'.

Returns
-------
pd.Series
    Resampled series.

Examples
--------
>>> monthly = resample_series(df['sales'], rule='M', aggregation='sum')

### `get_acf_pacf_values`

```python
def get_acf_pacf_values(series: pd.Series, lags: int=40, alpha: float=0.05) -> pd.DataFrame
```

Compute ACF and PACF values with confidence intervals.

Parameters
----------
series : pd.Series
    The time series.
lags : int, default=40
    Number of lags.
alpha : float, default=0.05
    Significance level for confidence intervals.

Returns
-------
pd.DataFrame
    DataFrame with lag, acf, pacf, and confidence bounds.

Examples
--------
>>> acf_pacf_df = get_acf_pacf_values(df['sales'])
