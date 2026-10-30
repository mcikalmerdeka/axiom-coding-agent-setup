import base64
import contextlib
import io
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from .preprocessing import check_data_information
from .statistics import (
    describe_categorical_combined,
    describe_numerical_combined,
    identify_distribution_types,
)
from .feature_selection import calculate_correlation_tabular

# ╔══════════════════════════════════════════════════════════════════════════════════╗
# ║                       Functions for Automated EDA Reports                        ║
# ╚══════════════════════════════════════════════════════════════════════════════════╝


def _human_readable_bytes(num_bytes: float) -> str:
    """Convert a byte count to a human-readable string."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.2f} PB"


def _get_column_types(df: pd.DataFrame) -> Dict[str, List[str]]:
    """Classify DataFrame columns by broad type categories."""
    return {
        "numeric": df.select_dtypes(include=["number"]).columns.tolist(),
        "categorical": df.select_dtypes(include=["object", "category", "string"]).columns.tolist(),
        "datetime": df.select_dtypes(include=["datetime64"]).columns.tolist(),
        "boolean": df.select_dtypes(include=["bool"]).columns.tolist(),
        "other": [
            col
            for col in df.columns
            if col
            not in (
                df.select_dtypes(include=["number"]).columns.tolist()
                + df.select_dtypes(include=["object", "category", "string"]).columns.tolist()
                + df.select_dtypes(include=["datetime64"]).columns.tolist()
                + df.select_dtypes(include=["bool"]).columns.tolist()
            )
        ],
    }


def _fig_to_base64(fig: plt.Figure, fmt: str = "png", dpi: int = 100) -> str:
    """Convert a matplotlib figure to a base64-encoded PNG string for HTML embedding."""
    buf = io.BytesIO()
    fig.savefig(buf, format=fmt, bbox_inches="tight", dpi=dpi)
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return encoded


def _plot_missing_values(df: pd.DataFrame, figsize: Tuple[int, int] = (10, 6)) -> Optional[str]:
    """Create a missing-value bar plot and return it as a base64 image."""
    missing = df.isna().sum()
    missing = missing[missing > 0].sort_values(ascending=False)
    if missing.empty:
        return None

    fig, ax = plt.subplots(figsize=figsize)
    pct = 100 * missing / len(df)
    bars = ax.bar(range(len(missing)), pct.values, color="steelblue", alpha=0.8)
    ax.set_xticks(range(len(missing)))
    ax.set_xticklabels(missing.index, rotation=45, ha="right")
    ax.set_ylabel("Missing (%)")
    ax.set_title("Missing Values by Column")
    ax.grid(True, axis="y", alpha=0.3)

    for bar, value in zip(bars, pct.values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{value:.1f}%",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    fig.tight_layout()
    return _fig_to_base64(fig)


def _plot_correlation_heatmap(
    df: pd.DataFrame,
    cols: List[str],
    method: str = "pearson",
    figsize: Tuple[int, int] = (10, 8),
) -> Optional[str]:
    """Create a correlation heatmap and return it as a base64 image."""
    numeric_df = df[cols].select_dtypes(include=["number"])
    if numeric_df.shape[1] < 2:
        return None

    corr = numeric_df.corr(method=method)
    mask = np.triu(np.ones_like(corr, dtype=bool))

    fig, ax = plt.subplots(figsize=figsize)
    sns.heatmap(
        corr,
        mask=mask,
        annot=True,
        fmt=".2f",
        cmap="coolwarm",
        vmin=-1,
        vmax=1,
        ax=ax,
    )
    ax.set_title(f"{method.capitalize()} Correlation Heatmap")
    fig.tight_layout()
    return _fig_to_base64(fig)


def _plot_distributions(
    df: pd.DataFrame,
    cols: List[str],
    ncols: int = 3,
    figsize: Tuple[int, int] = (15, 10),
) -> Optional[str]:
    """Create histogram/KDE plots for numerical columns and return as base64 image."""
    numeric_cols = df[cols].select_dtypes(include=["number"]).columns.tolist()
    if not numeric_cols:
        return None

    n = len(numeric_cols)
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=figsize, squeeze=False)
    axes = axes.flatten()

    for idx, col in enumerate(numeric_cols):
        ax = axes[idx]
        sns.histplot(df[col].dropna(), kde=True, ax=ax, color="steelblue", alpha=0.7)
        ax.set_title(f"Distribution of {col}")
        ax.set_xlabel(col)
        ax.set_ylabel("Count")

    for idx in range(n, len(axes)):
        fig.delaxes(axes[idx])

    fig.tight_layout()
    return _fig_to_base64(fig)


def _plot_categorical_counts(
    df: pd.DataFrame,
    cols: List[str],
    n_top: int = 10,
    ncols: int = 2,
    figsize: Tuple[int, int] = (14, 10),
) -> Optional[str]:
    """Create count plots for the top N categories and return as base64 image."""
    cat_cols = df[cols].select_dtypes(include=["object", "category", "string"]).columns.tolist()
    if not cat_cols:
        return None

    n = len(cat_cols)
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=figsize, squeeze=False)
    axes = axes.flatten()

    for idx, col in enumerate(cat_cols):
        ax = axes[idx]
        order = df[col].value_counts().head(n_top).index
        sns.countplot(data=df, x=col, order=order, ax=ax, hue=col, palette="viridis", legend=False)
        ax.set_title(f"Top {n_top} Categories of {col}")
        ax.set_xlabel(col)
        ax.set_ylabel("Count")
        ax.tick_params(axis="x", rotation=45)

    for idx in range(n, len(axes)):
        fig.delaxes(axes[idx])

    fig.tight_layout()
    return _fig_to_base64(fig)


def _plot_target(
    df: pd.DataFrame,
    target: str,
    figsize: Tuple[int, int] = (12, 5),
) -> Optional[str]:
    """Create a target distribution plot and return as base64 image."""
    if target not in df.columns:
        return None

    fig, axes = plt.subplots(1, 2, figsize=figsize)

    if pd.api.types.is_numeric_dtype(df[target]) and df[target].nunique() > 10:
        sns.histplot(df[target].dropna(), kde=True, ax=axes[0], color="steelblue")
        axes[0].set_title(f"Distribution of Target: {target}")
        axes[0].set_xlabel(target)
    else:
        vc = df[target].value_counts().reset_index()
        vc.columns = [target, "count"]
        sns.barplot(data=vc, x=target, y="count", ax=axes[0], hue=target, palette="viridis", legend=False)
        axes[0].set_title(f"Target Distribution: {target}")
        axes[0].set_xlabel(target)
        axes[0].set_ylabel("Count")
        axes[0].tick_params(axis="x", rotation=45)

    # Target composition table
    axes[1].axis("off")
    if pd.api.types.is_numeric_dtype(df[target]) and df[target].nunique() > 10:
        summary = df[target].describe().to_frame().reset_index()
        summary.columns = ["Statistic", "Value"]
    else:
        summary = (
            df[target]
            .value_counts(normalize=True)
            .mul(100)
            .round(2)
            .to_frame()
            .reset_index()
        )
        summary.columns = [target, "Percentage (%)"]

    table = axes[1].table(
        cellText=summary.values,
        colLabels=summary.columns,
        loc="center",
        cellLoc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 2)
    axes[1].set_title("Target Summary")

    fig.tight_layout()
    return _fig_to_base64(fig)


def _get_high_correlations(
    df: pd.DataFrame,
    cols: List[str],
    method: str,
    threshold: float,
) -> pd.DataFrame:
    """Return feature pairs whose absolute correlation meets or exceeds the threshold."""
    corr = df[cols].corr(method=method)
    pairs = []
    for i in range(len(corr.columns)):
        for j in range(i + 1, len(corr.columns)):
            raw_value = corr.iloc[i, j]
            abs_value = abs(raw_value)
            if abs_value >= threshold:
                pairs.append({
                    "Feature A": corr.columns[i],
                    "Feature B": corr.columns[j],
                    "Correlation": round(raw_value, 4),
                    "Abs Correlation": round(abs_value, 4),
                })
    if not pairs:
        return pd.DataFrame(columns=["Feature A", "Feature B", "Correlation", "Abs Correlation"])
    return pd.DataFrame(pairs).sort_values("Abs Correlation", ascending=False)


def _df_to_html(df: pd.DataFrame, max_rows: int = 100) -> str:
    """Convert a DataFrame to a compact HTML table."""
    display_df = df.head(max_rows)
    return display_df.to_html(index=False, classes="table table-striped", border=0)


def generate_eda_report(
    df: pd.DataFrame,
    target: Optional[str] = None,
    output_path: Optional[Union[str, Path]] = None,
    title: Optional[str] = None,
    n_top_categories: int = 10,
    corr_method: str = "pearson",
    corr_threshold: float = 0.8,
    verbose: bool = True,
) -> str:
    """
    Generate an automated Exploratory Data Analysis (EDA) report as HTML.

    The report combines data quality checks, statistical summaries,
    correlation analysis, and visualizations. It is designed for quick
    inspection of tabular datasets in notebooks or as a standalone HTML file.

    Parameters
    ----------
    df : pd.DataFrame
        The dataset to analyze.
    target : Optional[str], default=None
        Name of the target column. If provided, target-specific analysis is included.
    output_path : Optional[Union[str, Path]], default=None
        File path to save the report. If None, the report string is returned.
    title : Optional[str], default=None
        Report title. Defaults to "EDA Report".
    n_top_categories : int, default=10
        Number of top categories to display for categorical features.
    corr_method : str, default='pearson'
        Correlation method: 'pearson', 'spearman', or 'kendall'.
    corr_threshold : float, default=0.8
        Threshold above which feature-feature correlations are flagged as high.
    verbose : bool, default=True
        Whether to print progress messages.

    Returns
    -------
    str
        The generated report as an HTML string.

    Examples
    --------
    >>> from utils import generate_eda_report
    >>> report = generate_eda_report(df, target="target")
    >>> generate_eda_report(df, output_path="eda_report.html")
    """
    if df.empty:
        raise ValueError("Input DataFrame is empty.")

    if target is not None and target not in df.columns:
        raise ValueError(f"Target column '{target}' not found in DataFrame.")

    if title is None:
        title = "EDA Report"
    safe_title = escape(title)

    report_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    column_types = _get_column_types(df)
    numeric_features = [col for col in column_types["numeric"] if col != target]
    categorical_features = [col for col in column_types["categorical"] if col != target]

    # Image placeholders
    missing_img: Optional[str] = None
    num_dist_img: Optional[str] = None
    cat_count_img: Optional[str] = None
    corr_img: Optional[str] = None
    target_img: Optional[str] = None

    # ── 1. Dataset Overview ───────────────────────────────────────────────────────
    overview = {
        "Rows": f"{len(df):,}",
        "Columns": f"{len(df.columns):,}",
        "Memory Usage": _human_readable_bytes(df.memory_usage(deep=True).sum()),
        "Duplicate Rows": f"{df.duplicated().sum():,}",
        "Numeric Columns": len(column_types["numeric"]),
        "Categorical Columns": len(column_types["categorical"]),
        "Datetime Columns": len(column_types["datetime"]),
        "Boolean Columns": len(column_types["boolean"]),
        "Other Columns": len(column_types["other"]),
    }

    # ── 2. Data Quality ───────────────────────────────────────────────────────────
    if verbose:
        print("[1/6] Generating data quality summary...")
    data_info = check_data_information(df, df.columns.tolist())
    missing_img = _plot_missing_values(df)

    # ── 3. Numerical Summary ──────────────────────────────────────────────────────
    num_summary_html = ""
    if numeric_features:
        if verbose:
            print("[2/6] Summarizing numerical features...")
        with contextlib.redirect_stdout(io.StringIO()):
            num_summary = describe_numerical_combined(df, numeric_features)
        num_summary_html = _df_to_html(num_summary)
        num_dist_img = _plot_distributions(df, numeric_features)

    # ── 4. Categorical Summary ────────────────────────────────────────────────────
    cat_summary_html = ""
    if categorical_features:
        if verbose:
            print("[3/6] Summarizing categorical features...")
        with contextlib.redirect_stdout(io.StringIO()):
            cat_summary = describe_categorical_combined(df, categorical_features)
        cat_summary_html = _df_to_html(cat_summary)
        cat_count_img = _plot_categorical_counts(
            df, categorical_features, n_top=n_top_categories
        )

    # ── 5. Distribution Types ─────────────────────────────────────────────────────
    dist_html = ""
    if numeric_features:
        if verbose:
            print("[4/6] Identifying distribution types...")
        with contextlib.redirect_stdout(io.StringIO()):
            dist_df = identify_distribution_types(df, numeric_features)
        dist_html = _df_to_html(dist_df)

    # ── 6. Correlation Analysis ───────────────────────────────────────────────────
    corr_target_html = ""
    corr_high_html = ""

    if numeric_features and target and target in column_types["numeric"]:
        with contextlib.redirect_stdout(io.StringIO()):
            feature_target_corr = calculate_correlation_tabular(
                df[numeric_features + [target]],
                target_col=target,
                method=corr_method,
                corr_type="feature_target",
            )
        if not feature_target_corr.empty:
            corr_target_html = _df_to_html(feature_target_corr)

    if len(numeric_features) >= 2:
        if verbose:
            print("[5/6] Computing correlations...")
        corr_img = _plot_correlation_heatmap(df, numeric_features, method=corr_method)

        high_corr = _get_high_correlations(
            df, numeric_features, method=corr_method, threshold=corr_threshold
        )
        if not high_corr.empty:
            corr_high_html = _df_to_html(high_corr)

    # ── 7. Target Analysis ────────────────────────────────────────────────────────
    if target:
        if verbose:
            print("[6/6] Analyzing target variable...")
        target_img = _plot_target(df, target)

    # ── 8. Build HTML Report ──────────────────────────────────────────────────────
    if verbose:
        print("Building report...")

    def img_tag(src: Optional[str], alt: str) -> str:
        if not src:
            return f"<p class='no-data'>No {alt} available.</p>"
        return f'<img src="data:image/png;base64,{src}" alt="{alt}" style="max-width:100%;" />'

    overview_rows = "".join(
        f"<tr><td><strong>{k}</strong></td><td>{v}</td></tr>" for k, v in overview.items()
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{safe_title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
            color: #333;
            background: #fafafa;
        }}
        h1, h2, h3 {{ color: #2c3e50; }}
        h1 {{ border-bottom: 3px solid #3498db; padding-bottom: 0.5rem; }}
        h2 {{ border-bottom: 2px solid #bdc3c7; padding-bottom: 0.3rem; margin-top: 2rem; }}
        .meta {{ color: #7f8c8d; font-size: 0.9rem; margin-bottom: 2rem; }}
        .section {{ background: #fff; padding: 1.5rem; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 1.5rem; }}
        table {{ border-collapse: collapse; width: 100%; font-size: 0.9rem; margin-top: 1rem; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background: #3498db; color: #fff; position: sticky; top: 0; }}
        tr:nth-child(even) {{ background: #f9f9f9; }}
        .overview-table {{ width: auto; min-width: 300px; }}
        .overview-table td {{ border: none; padding: 6px 12px; }}
        img {{ border-radius: 4px; margin-top: 1rem; }}
        .no-data {{ color: #7f8c8d; font-style: italic; }}
        .table-wrap {{ overflow-x: auto; }}
    </style>
</head>
<body>
    <h1>{safe_title}</h1>
    <p class="meta">Generated on {report_date}</p>

    <div class="section">
        <h2>1. Dataset Overview</h2>
        <table class="overview-table">
            {overview_rows}
        </table>
    </div>

    <div class="section">
        <h2>2. Data Quality</h2>
        <h3>Column Information</h3>
        <div class="table-wrap">{_df_to_html(data_info)}</div>
        <h3>Missing Values</h3>
        {img_tag(missing_img, "missing values plot")}
    </div>

    <div class="section">
        <h2>3. Numerical Summary</h2>
        {f'<div class="table-wrap">{num_summary_html}</div>' if num_summary_html else '<p class="no-data">No numerical columns found.</p>'}
        <h3>Distributions</h3>
        {img_tag(num_dist_img, "numerical distributions")}
    </div>

    <div class="section">
        <h2>4. Categorical Summary</h2>
        {f'<div class="table-wrap">{cat_summary_html}</div>' if cat_summary_html else '<p class="no-data">No categorical columns found.</p>'}
        <h3>Top Categories</h3>
        {img_tag(cat_count_img, "categorical counts")}
    </div>

    <div class="section">
        <h2>5. Distribution Types</h2>
        {f'<div class="table-wrap">{dist_html}</div>' if dist_html else '<p class="no-data">No numerical columns available for distribution analysis.</p>'}
    </div>

    <div class="section">
        <h2>6. Correlation Analysis</h2>
        {img_tag(corr_img, "correlation heatmap")}
        <h3>Feature-Target Correlations</h3>
        {f'<div class="table-wrap">{corr_target_html}</div>' if corr_target_html else '<p class="no-data">No target column provided or no numeric features.</p>'}
        <h3>Highly Correlated Feature Pairs (≥ {corr_threshold})</h3>
        {f'<div class="table-wrap">{corr_high_html}</div>' if corr_high_html else f'<p class="no-data">No feature pairs exceed the {corr_threshold} threshold.</p>'}
    </div>

    {f'''
    <div class="section">
        <h2>7. Target Analysis: {target}</h2>
        {img_tag(target_img, "target distribution")}
    </div>
    ''' if target else ''}

    <footer style="margin-top: 3rem; color: #7f8c8d; font-size: 0.85rem; text-align: center;">
        Generated by data-science-utils
    </footer>
</body>
</html>
"""

    # ── 9. Save or Return ─────────────────────────────────────────────────────────
    if output_path is not None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html, encoding="utf-8")
        if verbose:
            print(f"Report saved to: {output_path}")

    return html
