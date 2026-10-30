# A/B testing API

Source: `scripts/utils/ab_testing.py`

> Auto-generated from the bundled source. Re-run
> `python scripts/dev/generate_references.py` after changing the package.


Sample sizing, assumption checks, hypothesis tests, and end-to-end experiment analysis.

## Quick index

| Name | Summary |
| --- | --- |
| `calculate_sample_size` | Calculate the required sample size per variation for an A/B test |
| `check_normality` | Perform Shapiro-Wilk test to check for normality |
| `check_variance_homogeneity` | Perform Levene's test to check for equal variances |
| `perform_t_test` | Perform independent t-test for continuous metrics |
| `perform_mann_whitney_u_test` | Perform Mann-Whitney U test for continuous metrics (non-parametric) |
| `perform_chi_squared_test` | Perform Chi-squared test for conversion rates |
| `perform_z_test_proportions` | Perform Z-test for two proportions |
| `analyze_ab_test_results` | Analyze A/B test results from a DataFrame, automatically selecting appropriate tests |

### `calculate_sample_size`

```python
def calculate_sample_size(baseline_rate: float, minimum_detectable_effect: float, power: float=0.8, alpha: float=0.05, metric_type: str='proportion', std_dev: Optional[float]=None) -> int
```

Calculate the required sample size per variation for an A/B test.

**Parameters**
baseline_rate : float
    The current conversion rate or mean value (e.g., 0.10 for 10%).
minimum_detectable_effect : float
    The minimum change you want to detect.
    For proportions, this is the absolute difference (e.g., 0.10 -> 0.12
    means MDE is 0.02). For continuous metrics, this is Cohen's d unless
    ``std_dev`` is provided, in which case it is the raw mean difference.
power : float, default=0.8
    The probability of rejecting the null hypothesis when it is false (1 - beta).
alpha : float, default=0.05
    The significance level (probability of Type I error).
metric_type : str, default='proportion'
    Type of metric: 'proportion' (for conversion rates) or 'continuous' (for means like revenue).
std_dev : Optional[float], default=None
    Standard deviation of the continuous metric. When provided, the
    effect size is ``minimum_detectable_effect / std_dev``.

**Returns**
int
    The required sample size per group.

**Examples**
>>> # For a conversion rate moving from 10% to 12% (absolute diff 0.02)
>>> n = calculate_sample_size(0.10, 0.02, metric_type='proportion')

>>> # For a continuous metric with a raw difference of 5 and std dev of 10
>>> n = calculate_sample_size(100, 5, metric_type='continuous', std_dev=10)

### `check_normality`

```python
def check_normality(data: Union[pd.Series, np.ndarray, List[float]], alpha: float=0.05) -> Dict[str, Any]
```

Perform Shapiro-Wilk test to check for normality.

**Parameters**
data : array-like
    The data to test.
alpha : float, default=0.05
    Significance level for the normality decision.

**Returns**
Dict[str, Any]
    Dictionary containing statistic, p-value, and interpretation.

### `check_variance_homogeneity`

```python
def check_variance_homogeneity(group_a: Union[pd.Series, np.ndarray], group_b: Union[pd.Series, np.ndarray], alpha: float=0.05) -> Dict[str, Any]
```

Perform Levene's test to check for equal variances.

**Parameters**
group_a : array-like
    Data for group A.
group_b : array-like
    Data for group B.
alpha : float, default=0.05
    Significance level for the equal-variance decision.

**Returns**
Dict[str, Any]
    Dictionary containing statistic, p-value, and interpretation.

### `perform_t_test`

```python
def perform_t_test(group_a: Union[pd.Series, np.ndarray], group_b: Union[pd.Series, np.ndarray], equal_var: bool=True, alpha: float=0.05) -> Dict[str, Any]
```

Perform independent t-test for continuous metrics.

**Parameters**
group_a : array-like
    Data for control group.
group_b : array-like
    Data for treatment group.
equal_var : bool, default=True
    If True, perform standard t-test. If False, perform Welch's t-test.
alpha : float, default=0.05
    Significance level for the decision.

**Returns**
Dict[str, Any]
    Test results including statistic, p-value, and decision.

### `perform_mann_whitney_u_test`

```python
def perform_mann_whitney_u_test(group_a: Union[pd.Series, np.ndarray], group_b: Union[pd.Series, np.ndarray], alpha: float=0.05) -> Dict[str, Any]
```

Perform Mann-Whitney U test for continuous metrics (non-parametric).

**Parameters**
group_a : array-like
    Data for control group.
group_b : array-like
    Data for treatment group.
alpha : float, default=0.05
    Significance level for the decision.

**Returns**
Dict[str, Any]
    Test results including statistic, p-value, and decision.

### `perform_chi_squared_test`

```python
def perform_chi_squared_test(group_a_conversions: int, group_a_total: int, group_b_conversions: int, group_b_total: int, alpha: float=0.05) -> Dict[str, Any]
```

Perform Chi-squared test for conversion rates.

**Parameters**
group_a_conversions : int
    Number of conversions in group A.
group_a_total : int
    Total sample size of group A.
group_b_conversions : int
    Number of conversions in group B.
group_b_total : int
    Total sample size of group B.
alpha : float, default=0.05
    Significance level for the decision.

**Returns**
Dict[str, Any]
    Test results including statistic, p-value, and decision.

### `perform_z_test_proportions`

```python
def perform_z_test_proportions(group_a_conversions: int, group_a_total: int, group_b_conversions: int, group_b_total: int, alpha: float=0.05) -> Dict[str, Any]
```

Perform Z-test for two proportions.

**Parameters**
group_a_conversions : int
    Number of conversions in group A.
group_a_total : int
    Total sample size of group A.
group_b_conversions : int
    Number of conversions in group B.
group_b_total : int
    Total sample size of group B.
alpha : float, default=0.05
    Significance level for the decision.

**Returns**
Dict[str, Any]
    Test results including statistic, p-value, and decision.

### `analyze_ab_test_results`

```python
def analyze_ab_test_results(data: pd.DataFrame, metric_col: str, group_col: str, metric_type: str='continuous', control_label: str='A', treatment_label: str='B', alpha: float=0.05) -> Dict[str, Any]
```

Analyze A/B test results from a DataFrame, automatically selecting appropriate tests.

**Parameters**
data : pd.DataFrame
    The dataframe containing the experiment data.
metric_col : str
    The column name of the metric to analyze.
group_col : str
    The column name indicating the group (e.g., 'group').
metric_type : str, default='continuous'
    'continuous' (e.g., revenue, time) or 'binary' (e.g., conversion 0/1).
control_label : str, default='A'
    Value in group_col representing the control group.
treatment_label : str, default='B'
    Value in group_col representing the treatment group.
alpha : float, default=0.05
    Significance level used by the selected tests.

**Returns**
Dict[str, Any]
    Comprehensive analysis results. Includes ``absolute_lift``,
    ``relative_lift``, ``ci_lower``, and ``ci_upper`` for the
    treatment-minus-control effect.
