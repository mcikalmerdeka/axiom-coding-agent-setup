import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.power import TTestIndPower, GofChisquarePower
from statsmodels.stats.proportion import confint_proportions_2indep, proportions_ztest
from typing import List, Dict, Union, Optional, Tuple, Any

# ╔══════════════════════════════════════════════════════════════════════════════════╗
# ║                       Functions for A/B Testing                                  ║
# ╚══════════════════════════════════════════════════════════════════════════════════╝


def _validate_alpha_power(alpha: float, power: Optional[float] = None) -> None:
    """Validate significance and power levels shared by the A/B helpers."""
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1.")
    if power is not None and not 0 < power < 1:
        raise ValueError("power must be between 0 and 1.")


def _validate_proportion_counts(
    conversions: float, total: float, label: str
) -> None:
    """Reject impossible conversion counts before handing them to statsmodels."""
    if total <= 0:
        raise ValueError(f"{label} total must be positive.")
    if conversions < 0 or conversions > total:
        raise ValueError(
            f"{label} conversions must be between 0 and the group total "
            f"({total}); got {conversions}."
        )


def _mean_difference_ci(
    group_a: Union[pd.Series, np.ndarray],
    group_b: Union[pd.Series, np.ndarray],
    alpha: float,
    equal_var: bool,
) -> Tuple[float, float]:
    """Confidence interval for mean(group_b) - mean(group_a)."""
    values_a = np.asarray(group_a, dtype=float)
    values_b = np.asarray(group_b, dtype=float)
    values_a = values_a[~np.isnan(values_a)]
    values_b = values_b[~np.isnan(values_b)]

    n_a = len(values_a)
    n_b = len(values_b)
    if n_a < 2 or n_b < 2:
        return np.nan, np.nan

    mean_diff = float(np.mean(values_b) - np.mean(values_a))
    var_a = float(np.var(values_a, ddof=1))
    var_b = float(np.var(values_b, ddof=1))

    if equal_var:
        degrees_of_freedom = n_a + n_b - 2
        pooled_var = (
            (n_a - 1) * var_a + (n_b - 1) * var_b
        ) / degrees_of_freedom
        standard_error = np.sqrt(pooled_var * (1 / n_a + 1 / n_b))
    else:
        se_a = var_a / n_a
        se_b = var_b / n_b
        standard_error = np.sqrt(se_a + se_b)
        denominator = (se_a ** 2) / (n_a - 1) + (se_b ** 2) / (n_b - 1)
        if denominator > 0:
            degrees_of_freedom = (se_a + se_b) ** 2 / denominator
        else:
            degrees_of_freedom = n_a + n_b - 2

    if not np.isfinite(standard_error):
        return np.nan, np.nan
    if standard_error == 0:
        return mean_diff, mean_diff

    critical_value = stats.t.ppf(1 - alpha / 2, degrees_of_freedom)
    margin = critical_value * standard_error
    return float(mean_diff - margin), float(mean_diff + margin)


## Calculate sample size
def calculate_sample_size(baseline_rate: float, minimum_detectable_effect: float, power: float = 0.8, alpha: float = 0.05, metric_type: str = 'proportion', std_dev: Optional[float] = None) -> int:
    """
    Calculate the required sample size per variation for an A/B test.
    
    Parameters:
    -----------
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
        
    Returns:
    --------
    int
        The required sample size per group.
        
    Examples:
    ---------
    >>> # For a conversion rate moving from 10% to 12% (absolute diff 0.02)
    >>> n = calculate_sample_size(0.10, 0.02, metric_type='proportion')
    
    >>> # For a continuous metric with a raw difference of 5 and std dev of 10
    >>> n = calculate_sample_size(100, 5, metric_type='continuous', std_dev=10)
    """
    _validate_alpha_power(alpha, power)

    if minimum_detectable_effect <= 0:
        raise ValueError("minimum_detectable_effect must be positive.")

    if metric_type == 'proportion':
        if not 0 < baseline_rate < 1:
            raise ValueError(
                "baseline_rate must be between 0 and 1 for proportion metrics."
            )
        if baseline_rate + minimum_detectable_effect >= 1:
            raise ValueError(
                "baseline_rate + minimum_detectable_effect must be less than 1."
            )

        # Using statsmodels for proportion power analysis.
        from statsmodels.stats.power import NormalIndPower
        import statsmodels.stats.proportion as proportion
        
        p1 = baseline_rate
        p2 = baseline_rate + minimum_detectable_effect
        
        # Calculate effect size (Cohen's h)
        effect_size = proportion.proportion_effectsize(p1, p2)
        
        analysis = NormalIndPower()
        sample_size = analysis.solve_power(effect_size=effect_size, alpha=alpha, power=power, ratio=1.0)
        
    elif metric_type == 'continuous':
        if std_dev is not None:
            if std_dev <= 0:
                raise ValueError("std_dev must be positive.")
            effect_size = minimum_detectable_effect / std_dev
        else:
            # Backwards-compatible interpretation: MDE is Cohen's d.
            effect_size = minimum_detectable_effect

        analysis = TTestIndPower()
        sample_size = analysis.solve_power(effect_size=effect_size, alpha=alpha, power=power, ratio=1.0)
        
    else:
        raise ValueError("metric_type must be 'proportion' or 'continuous'")
        
    return int(np.ceil(sample_size))

## Check Normality
def check_normality(data: Union[pd.Series, np.ndarray, List[float]], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Perform Shapiro-Wilk test to check for normality.
    
    Parameters:
    -----------
    data : array-like
        The data to test.
    alpha : float, default=0.05
        Significance level for the normality decision.
        
    Returns:
    --------
    Dict[str, Any]
        Dictionary containing statistic, p-value, and interpretation.
    """
    _validate_alpha_power(alpha)

    values = np.asarray(data, dtype=float)
    values = values[~np.isnan(values)]
    if len(values) < 3:
        return {
            'test': 'Shapiro-Wilk',
            'statistic': np.nan,
            'p_value': np.nan,
            'alpha': alpha,
            'is_normal': False
        }

    stat, p_value = stats.shapiro(values)
    return {
        'test': 'Shapiro-Wilk',
        'statistic': stat,
        'p_value': p_value,
        'alpha': alpha,
        'is_normal': p_value > alpha
    }

## Check Variance Homogeneity
def check_variance_homogeneity(group_a: Union[pd.Series, np.ndarray], group_b: Union[pd.Series, np.ndarray], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Perform Levene's test to check for equal variances.
    
    Parameters:
    -----------
    group_a : array-like
        Data for group A.
    group_b : array-like
        Data for group B.
    alpha : float, default=0.05
        Significance level for the equal-variance decision.
        
    Returns:
    --------
    Dict[str, Any]
        Dictionary containing statistic, p-value, and interpretation.
    """
    _validate_alpha_power(alpha)
    stat, p_value = stats.levene(group_a, group_b)
    return {
        'test': 'Levene',
        'statistic': stat,
        'p_value': p_value,
        'alpha': alpha,
        'equal_variance': p_value > alpha
    }

## T-Test (Parametric)
def perform_t_test(group_a: Union[pd.Series, np.ndarray], group_b: Union[pd.Series, np.ndarray], equal_var: bool = True, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Perform independent t-test for continuous metrics.
    
    Parameters:
    -----------
    group_a : array-like
        Data for control group.
    group_b : array-like
        Data for treatment group.
    equal_var : bool, default=True
        If True, perform standard t-test. If False, perform Welch's t-test.
    alpha : float, default=0.05
        Significance level for the decision.
        
    Returns:
    --------
    Dict[str, Any]
        Test results including statistic, p-value, and decision.
    """
    _validate_alpha_power(alpha)
    t_stat, p_val = stats.ttest_ind(group_a, group_b, equal_var=equal_var)
    
    return {
        'test': 'T-Test' if equal_var else "Welch's T-Test",
        'statistic': t_stat,
        'p_value': p_val,
        'alpha': alpha,
        'significant': p_val < alpha,
        'mean_a': np.mean(group_a),
        'mean_b': np.mean(group_b)
    }

## Mann-Whitney U Test (Non-Parametric)
def perform_mann_whitney_u_test(group_a: Union[pd.Series, np.ndarray], group_b: Union[pd.Series, np.ndarray], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Perform Mann-Whitney U test for continuous metrics (non-parametric).
    
    Parameters:
    -----------
    group_a : array-like
        Data for control group.
    group_b : array-like
        Data for treatment group.
    alpha : float, default=0.05
        Significance level for the decision.
        
    Returns:
    --------
    Dict[str, Any]
        Test results including statistic, p-value, and decision.
    """
    _validate_alpha_power(alpha)
    u_stat, p_val = stats.mannwhitneyu(group_a, group_b, alternative='two-sided')
    
    return {
        'test': 'Mann-Whitney U',
        'statistic': u_stat,
        'p_value': p_val,
        'alpha': alpha,
        'significant': p_val < alpha,
        'median_a': np.median(group_a),
        'median_b': np.median(group_b)
    }

## Chi-Squared Test
def perform_chi_squared_test(group_a_conversions: int, group_a_total: int, group_b_conversions: int, group_b_total: int, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Perform Chi-squared test for conversion rates.
    
    Parameters:
    -----------
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
        
    Returns:
    --------
    Dict[str, Any]
        Test results including statistic, p-value, and decision.
    """
    _validate_alpha_power(alpha)
    _validate_proportion_counts(group_a_conversions, group_a_total, "Group A")
    _validate_proportion_counts(group_b_conversions, group_b_total, "Group B")

    # Contingency table
    #           Converted   Not Converted
    # Group A   conv_a      total_a - conv_a
    # Group B   conv_b      total_b - conv_b
    
    obs = np.array([
        [group_a_conversions, group_a_total - group_a_conversions],
        [group_b_conversions, group_b_total - group_b_conversions]
    ])

    # Chi-square is undefined when a row or column margin is zero, which
    # happens when both arms have 0% or both have 100% conversions.
    if (obs.sum(axis=0) == 0).any() or (obs.sum(axis=1) == 0).any():
        chi2 = 0.0
        p_val = 1.0
    else:
        chi2, p_val, dof, ex = stats.chi2_contingency(obs)
    
    rate_a = group_a_conversions / group_a_total
    rate_b = group_b_conversions / group_b_total
    
    return {
        'test': 'Chi-Squared',
        'statistic': chi2,
        'p_value': p_val,
        'alpha': alpha,
        'significant': p_val < alpha,
        'rate_a': rate_a,
        'rate_b': rate_b,
        'lift': (rate_b - rate_a) / rate_a if rate_a > 0 else np.nan
    }

## Z-Test for Proportions
def perform_z_test_proportions(group_a_conversions: int, group_a_total: int, group_b_conversions: int, group_b_total: int, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Perform Z-test for two proportions.
    
    Parameters:
    -----------
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
        
    Returns:
    --------
    Dict[str, Any]
        Test results including statistic, p-value, and decision.
    """
    _validate_alpha_power(alpha)
    _validate_proportion_counts(group_a_conversions, group_a_total, "Group A")
    _validate_proportion_counts(group_b_conversions, group_b_total, "Group B")

    count = np.array([group_a_conversions, group_b_conversions])
    nobs = np.array([group_a_total, group_b_total])
    
    rate_a = group_a_conversions / group_a_total
    rate_b = group_b_conversions / group_b_total

    # With 0% or 100% in both arms the pooled variance is zero and the
    # z-statistic is undefined. Treat the result as non-significant instead
    # of returning NaN with a runtime warning.
    pooled_rate = count.sum() / nobs.sum()
    if pooled_rate == 0.0 or pooled_rate == 1.0:
        stat = np.nan
        p_val = 1.0
    else:
        stat, p_val = proportions_ztest(count, nobs)
    
    return {
        'test': 'Z-Test Proportions',
        'statistic': stat,
        'p_value': p_val,
        'alpha': alpha,
        'significant': p_val < alpha,
        'rate_a': rate_a,
        'rate_b': rate_b
    }

## High-level Analysis
def analyze_ab_test_results(data: pd.DataFrame, metric_col: str, group_col: str, metric_type: str = 'continuous', control_label: str = 'A', treatment_label: str = 'B', alpha: float = 0.05) -> Dict[str, Any]:
    """
    Analyze A/B test results from a DataFrame, automatically selecting appropriate tests.
    
    Parameters:
    -----------
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
        
    Returns:
    --------
    Dict[str, Any]
        Comprehensive analysis results. Includes ``absolute_lift``,
        ``relative_lift``, ``ci_lower``, and ``ci_upper`` for the
        treatment-minus-control effect.
    """
    _validate_alpha_power(alpha)
    if metric_type not in {'continuous', 'binary'}:
        raise ValueError("metric_type must be 'continuous' or 'binary'")

    # Split data
    group_a = data[data[group_col] == control_label][metric_col].dropna()
    group_b = data[data[group_col] == treatment_label][metric_col].dropna()

    if group_a.empty:
        raise ValueError(
            f"Group '{control_label}' is empty (no rows after dropping missing values)."
        )
    if group_b.empty:
        raise ValueError(
            f"Group '{treatment_label}' is empty (no rows after dropping missing values)."
        )
    
    results = {
        'metric': metric_col,
        'sample_size_a': len(group_a),
        'sample_size_b': len(group_b)
    }
    
    if metric_type == 'continuous':
        if len(group_a) < 2 or len(group_b) < 2:
            raise ValueError(
                "Continuous A/B analysis requires at least 2 observations per group."
            )

        # Check normality
        normality_a = check_normality(group_a, alpha=alpha)
        normality_b = check_normality(group_b, alpha=alpha)
        
        results['normality_check'] = {
            'group_a': normality_a,
            'group_b': normality_b
        }
        
        # Check variance homogeneity
        variance_check = check_variance_homogeneity(group_a, group_b, alpha=alpha)
        results['variance_check'] = variance_check
        
        # Decide test
        if normality_a['is_normal'] and normality_b['is_normal']:
            # Parametric
            test_res = perform_t_test(
                group_a,
                group_b,
                equal_var=variance_check['equal_variance'],
                alpha=alpha,
            )
            interval_equal_var = variance_check['equal_variance']
        else:
            # Non-parametric; report a Welch mean-difference interval because
            # the equal-variance assumption was not established.
            test_res = perform_mann_whitney_u_test(group_a, group_b, alpha=alpha)
            interval_equal_var = False
            
        results.update(test_res)

        mean_a = float(np.mean(group_a))
        mean_b = float(np.mean(group_b))
        absolute_lift = mean_b - mean_a
        results['absolute_lift'] = absolute_lift
        results['relative_lift'] = (
            absolute_lift / mean_a if mean_a != 0 else np.nan
        )
        ci_lower, ci_upper = _mean_difference_ci(
            group_a, group_b, alpha=alpha, equal_var=interval_equal_var
        )
        results['ci_lower'] = ci_lower
        results['ci_upper'] = ci_upper
        
    elif metric_type == 'binary':
        # Binary metrics must be explicitly 0/1 (booleans are accepted).
        if not group_a.isin([0, 1]).all():
            invalid = group_a[~group_a.isin([0, 1])].unique().tolist()
            raise ValueError(
                f"Binary metric '{metric_col}' must contain only 0/1 values; "
                f"invalid values in group '{control_label}': {invalid}"
            )
        if not group_b.isin([0, 1]).all():
            invalid = group_b[~group_b.isin([0, 1])].unique().tolist()
            raise ValueError(
                f"Binary metric '{metric_col}' must contain only 0/1 values; "
                f"invalid values in group '{treatment_label}': {invalid}"
            )

        # Conversion counts
        conv_a = int(group_a.sum())
        total_a = len(group_a)
        conv_b = int(group_b.sum())
        total_b = len(group_b)
        
        # Use Chi-Squared by default for binary data analysis
        test_res = perform_chi_squared_test(
            conv_a, total_a, conv_b, total_b, alpha=alpha
        )
        results.update(test_res)
        
        # Also include Z-test for reference
        z_res = perform_z_test_proportions(
            conv_a, total_a, conv_b, total_b, alpha=alpha
        )
        results['z_test_p_value'] = z_res['p_value']

        rate_a = conv_a / total_a
        rate_b = conv_b / total_b
        absolute_lift = rate_b - rate_a
        results['absolute_lift'] = absolute_lift
        results['relative_lift'] = (
            absolute_lift / rate_a if rate_a > 0 else np.nan
        )

        # confint_proportions_2indep returns an interval for p1 - p2; pass the
        # treatment group first to get treatment minus control.
        ci_lower, ci_upper = confint_proportions_2indep(
            conv_b,
            total_b,
            conv_a,
            total_a,
            compare='diff',
            alpha=alpha,
        )
        results['ci_lower'] = float(ci_lower)
        results['ci_upper'] = float(ci_upper)
        
    return results
