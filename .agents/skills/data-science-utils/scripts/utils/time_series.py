import warnings
from typing import Any, Dict, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import acf, adfuller, kpss, pacf

# ╔══════════════════════════════════════════════════════════════════════════════════╗
# ║                       Functions for Time Series Analysis                         ║
# ╚══════════════════════════════════════════════════════════════════════════════════╝

_ALLOWED_RESAMPLE_AGGREGATIONS = frozenset(
    {"mean", "sum", "min", "max", "median", "first", "last", "count", "std", "var"}
)


def _validate_series(series: pd.Series) -> pd.Series:
    """Validate that input is a non-empty pandas Series."""
    if not isinstance(series, pd.Series):
        raise TypeError("Input must be a pandas Series.")
    if series.empty:
        raise ValueError("Input series is empty.")
    if series.isna().all():
        raise ValueError("Input series contains only missing values.")
    return series


def _infer_period(series: pd.Series) -> int:
    """Infer a reasonable seasonal period from a datetime index if possible."""
    if isinstance(series.index, pd.DatetimeIndex):
        freq = pd.infer_freq(series.index)
        if freq:
            # Accept both legacy uppercase aliases and modern lowercase
            # aliases (e.g. 'h', 'ME', 'QE-DEC'), including count prefixes.
            # Keep the raw case for month aliases: 'MS' is month-start while
            # 'ms' is milliseconds, and 'min' is minutes.
            normalized = freq.lstrip("0123456789")
            upper = normalized.upper()
            if upper.startswith("W"):
                return 52
            if upper.startswith("Q") or upper.startswith("BQ"):
                return 4
            if normalized in {"M", "ME", "MS", "BM", "BME", "BMS", "CBM", "CBMS"}:
                return 12
            if upper in ("H", "BH"):
                return 24
            if upper in ("D", "B"):
                return 7
    return min(len(series) // 2, 12)


def decompose_series(
    series: pd.Series,
    model: str = "additive",
    period: Optional[int] = None,
    plot: bool = True,
    figsize: Tuple[int, int] = (14, 10),
) -> Dict[str, Any]:
    """
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
    """
    series = _validate_series(series)

    if model not in {"additive", "multiplicative"}:
        raise ValueError("model must be 'additive' or 'multiplicative'.")

    if period is None:
        period = _infer_period(series)
    if period < 2:
        raise ValueError(
            "period must be at least 2 for seasonal decomposition; "
            f"got {period}."
        )

    # Ensure strictly positive values for multiplicative decomposition
    if model == "multiplicative" and (series <= 0).any():
        raise ValueError("Multiplicative decomposition requires strictly positive values.")

    result = seasonal_decompose(series, model=model, period=period, extrapolate_trend="freq")

    if plot:
        fig = result.plot()
        fig.set_size_inches(figsize)
        plt.suptitle(f"Seasonal Decomposition ({model.capitalize()}, period={period})", y=1.02)
        plt.tight_layout()
        plt.show()

    return {
        "observed": result.observed,
        "trend": result.trend,
        "seasonal": result.seasonal,
        "residual": result.resid,
        "model": model,
        "period": period,
    }


def adf_test(series: pd.Series, alpha: float = 0.05) -> Dict[str, Any]:
    """
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
    """
    series = _validate_series(series).dropna()

    statistic, p_value, usedlag, nobs, critical_values, icbest = adfuller(series)

    return {
        "test": "Augmented Dickey-Fuller",
        "statistic": statistic,
        "p_value": p_value,
        "used_lag": usedlag,
        "n_observations": nobs,
        "critical_values": critical_values,
        "icbest": icbest,
        "alpha": alpha,
        "is_stationary": p_value < alpha,
        "interpretation": (
            "Stationary" if p_value < alpha else "Non-stationary"
        ),
    }


def kpss_test(
    series: pd.Series,
    alpha: float = 0.05,
    regression: str = "c",
) -> Dict[str, Any]:
    """
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
    """
    series = _validate_series(series).dropna()

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        statistic, p_value, lags, critical_values = kpss(
            series, regression=regression, nlags="auto"
        )

    return {
        "test": "KPSS",
        "statistic": statistic,
        "p_value": p_value,
        "lags": lags,
        "critical_values": critical_values,
        "alpha": alpha,
        "is_stationary": p_value >= alpha,
        "interpretation": (
            "Stationary" if p_value >= alpha else "Non-stationary"
        ),
    }


def check_stationarity(
    series: pd.Series,
    alpha: float = 0.05,
) -> pd.DataFrame:
    """
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
    """
    adf = adf_test(series, alpha=alpha)
    kpss_result = kpss_test(series, alpha=alpha)

    return pd.DataFrame({
        "Test": [adf["test"], kpss_result["test"]],
        "Statistic": [adf["statistic"], kpss_result["statistic"]],
        "P-Value": [adf["p_value"], kpss_result["p_value"]],
        "Stationary": [adf["is_stationary"], kpss_result["is_stationary"]],
        "Interpretation": [adf["interpretation"], kpss_result["interpretation"]],
    })


def make_stationary(
    series: pd.Series,
    max_diff: int = 2,
    alpha: float = 0.05,
    seasonal_period: Optional[int] = None,
) -> Dict[str, Any]:
    """
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
    """
    series = _validate_series(series).dropna()
    transformed = series.copy()
    n_diffs = 0
    seasonal_diffs = 0

    # Ordinary differencing
    while n_diffs < max_diff:
        adf = adf_test(transformed, alpha=alpha)
        if adf["is_stationary"]:
            break
        transformed = transformed.diff().dropna()
        n_diffs += 1

    # Seasonal differencing
    if seasonal_period is not None and not adf_test(transformed, alpha=alpha)["is_stationary"]:
        transformed = transformed.diff(seasonal_period).dropna()
        seasonal_diffs = 1

    final_adf = adf_test(transformed, alpha=alpha)

    return {
        "transformed": transformed,
        "n_diffs": n_diffs,
        "seasonal_diffs": seasonal_diffs,
        "adf_result": final_adf,
        "is_stationary": final_adf["is_stationary"],
    }


def create_lag_features(
    df: pd.DataFrame,
    columns: List[str],
    lags: List[int] = [1, 2, 3],
    drop_original: bool = False,
) -> pd.DataFrame:
    """
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
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame.")

    result = df.copy() if not drop_original else pd.DataFrame(index=df.index)

    for col in columns:
        if col not in df.columns:
            raise ValueError(f"Column '{col}' not found in DataFrame.")
        for lag in lags:
            result[f"{col}_lag_{lag}"] = df[col].shift(lag)

    return result


def create_rolling_features(
    df: pd.DataFrame,
    columns: List[str],
    windows: List[int] = [3, 7, 14],
    aggregations: List[str] = ["mean", "std", "min", "max"],
    drop_original: bool = False,
) -> pd.DataFrame:
    """
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
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame.")

    result = df.copy() if not drop_original else pd.DataFrame(index=df.index)

    for col in columns:
        if col not in df.columns:
            raise ValueError(f"Column '{col}' not found in DataFrame.")
        for window in windows:
            for agg in aggregations:
                if not hasattr(df[col].rolling(window=window), agg):
                    raise ValueError(f"Invalid aggregation: '{agg}'")
                feature_name = f"{col}_roll_{window}_{agg}"
                result[feature_name] = getattr(df[col].rolling(window=window), agg)()

    return result


def create_date_features(
    df: pd.DataFrame,
    datetime_col: str,
    drop_original: bool = False,
) -> pd.DataFrame:
    """
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
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame.")
    if datetime_col not in df.columns:
        raise ValueError(f"Column '{datetime_col}' not found in DataFrame.")

    result = df.copy()
    dt = pd.to_datetime(result[datetime_col])

    result[f"{datetime_col}_year"] = dt.dt.year
    result[f"{datetime_col}_month"] = dt.dt.month
    result[f"{datetime_col}_day"] = dt.dt.day
    result[f"{datetime_col}_dayofweek"] = dt.dt.dayofweek
    result[f"{datetime_col}_dayofyear"] = dt.dt.dayofyear
    result[f"{datetime_col}_quarter"] = dt.dt.quarter
    result[f"{datetime_col}_weekofyear"] = dt.dt.isocalendar().week.astype(np.int64)
    result[f"{datetime_col}_is_weekend"] = (dt.dt.dayofweek >= 5).astype(int)
    result[f"{datetime_col}_hour"] = dt.dt.hour

    if drop_original:
        result = result.drop(columns=[datetime_col])

    return result


def split_time_series(
    df: pd.DataFrame,
    test_size: Union[int, float] = 0.2,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
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
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame.")

    n = len(df)
    if isinstance(test_size, float):
        if not 0.0 < test_size < 1.0:
            raise ValueError("test_size as float must be between 0 and 1.")
        test_len = int(n * test_size)
    else:
        test_len = test_size

    if test_len <= 0 or test_len >= n:
        raise ValueError("test_size results in an invalid split.")

    return df.iloc[:-test_len].copy(), df.iloc[-test_len:].copy()


def time_series_cv_splits(
    df: pd.DataFrame,
    n_splits: int = 5,
    test_size: Union[int, float] = 0.2,
) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
    """
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
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame.")

    n = len(df)
    if isinstance(test_size, float):
        test_len = int(n * test_size)
    else:
        test_len = test_size

    if test_len <= 0 or n_splits <= 0 or test_len * n_splits >= n:
        raise ValueError("Invalid n_splits or test_size for the given DataFrame.")

    splits = []
    for i in range(1, n_splits + 1):
        test_end = n - test_len * (n_splits - i)
        test_start = test_end - test_len
        train_df = df.iloc[:test_start].copy()
        test_df = df.iloc[test_start:test_end].copy()
        splits.append((train_df, test_df))

    return splits


def evaluate_forecast(
    y_true: Union[pd.Series, np.ndarray, List[float]],
    y_pred: Union[pd.Series, np.ndarray, List[float]],
) -> Dict[str, float]:
    """
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
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    if y_true.shape != y_pred.shape:
        raise ValueError("y_true and y_pred must have the same shape.")

    mae = np.mean(np.abs(y_true - y_pred))
    mse = np.mean((y_true - y_pred) ** 2)
    rmse = np.sqrt(mse)

    if np.any(y_true == 0):
        mape = np.nan
    else:
        with np.errstate(divide="ignore", invalid="ignore"):
            mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100

    with np.errstate(divide="ignore", invalid="ignore"):
        smape = np.mean(2 * np.abs(y_true - y_pred) / (np.abs(y_true) + np.abs(y_pred))) * 100
        smape = np.nan_to_num(smape, nan=0.0)

        mpe = np.mean((y_true - y_pred) / y_true) * 100
        mpe = np.nan_to_num(mpe, nan=0.0)

    return {
        "mae": float(mae),
        "mse": float(mse),
        "rmse": float(rmse),
        "mape": float(mape),
        "smape": float(smape),
        "mpe": float(mpe),
    }


def plot_acf_pacf(
    series: pd.Series,
    lags: int = 40,
    figsize: Tuple[int, int] = (14, 5),
    alpha: float = 0.05,
) -> None:
    """
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
    """
    series = _validate_series(series).dropna()

    fig, axes = plt.subplots(1, 2, figsize=figsize)
    plot_acf(series, lags=lags, ax=axes[0], alpha=alpha)
    axes[0].set_title("Autocorrelation Function (ACF)")

    plot_pacf(series, lags=lags, ax=axes[1], alpha=alpha, method="ywm")
    axes[1].set_title("Partial Autocorrelation Function (PACF)")

    plt.tight_layout()
    plt.show()


def detect_outliers_iqr(
    series: pd.Series,
    k: float = 1.5,
) -> pd.Series:
    """
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
    """
    series = _validate_series(series)

    mask = pd.Series(False, index=series.index)
    valid = series.dropna()

    q1 = valid.quantile(0.25)
    q3 = valid.quantile(0.75)
    iqr = q3 - q1

    lower_bound = q1 - k * iqr
    upper_bound = q3 + k * iqr

    mask.loc[valid.index] = (valid < lower_bound) | (valid > upper_bound)
    return mask


def interpolate_series(
    series: pd.Series,
    method: str = "time",
    limit: Optional[int] = None,
) -> pd.Series:
    """
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
    """
    series = _validate_series(series)

    if method == "time" and not isinstance(series.index, pd.DatetimeIndex):
        raise ValueError("method='time' requires a DatetimeIndex.")

    return series.interpolate(method=method, limit=limit)


def resample_series(
    series: pd.Series,
    rule: str,
    aggregation: str = "mean",
) -> pd.Series:
    """
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
    """
    series = _validate_series(series)

    if not isinstance(series.index, pd.DatetimeIndex):
        raise ValueError("Resampling requires a DatetimeIndex.")

    if aggregation not in _ALLOWED_RESAMPLE_AGGREGATIONS:
        allowed = ", ".join(sorted(_ALLOWED_RESAMPLE_AGGREGATIONS))
        raise ValueError(
            f"Invalid aggregation: '{aggregation}'. Supported aggregations: {allowed}."
        )

    resampler = series.resample(rule)
    return getattr(resampler, aggregation)()


def get_acf_pacf_values(
    series: pd.Series,
    lags: int = 40,
    alpha: float = 0.05,
) -> pd.DataFrame:
    """
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
    """
    series = _validate_series(series).dropna()

    acf_values, acf_confint = acf(series, nlags=lags, alpha=alpha)
    pacf_values, pacf_confint = pacf(series, nlags=lags, alpha=alpha, method="ywm")

    return pd.DataFrame({
        "lag": np.arange(len(acf_values)),
        "acf": acf_values,
        "acf_lower": acf_confint[:, 0],
        "acf_upper": acf_confint[:, 1],
        "pacf": pacf_values,
        "pacf_lower": pacf_confint[:, 0],
        "pacf_upper": pacf_confint[:, 1],
    })
