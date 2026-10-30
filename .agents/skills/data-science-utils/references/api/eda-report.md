# EDA report API

Source: `scripts/utils/eda_report.py`

> Auto-generated from the bundled source. Re-run
> `python scripts/dev/generate_references.py` after changing the package.


Self-contained HTML exploratory data analysis reports.

## Quick index

| Name | Summary |
| --- | --- |
| `generate_eda_report` | Generate an automated Exploratory Data Analysis (EDA) report as HTML |

### `generate_eda_report`

```python
def generate_eda_report(df: pd.DataFrame, target: Optional[str]=None, output_path: Optional[Union[str, Path]]=None, title: Optional[str]=None, n_top_categories: int=10, corr_method: str='pearson', corr_threshold: float=0.8, verbose: bool=True) -> str
```

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
