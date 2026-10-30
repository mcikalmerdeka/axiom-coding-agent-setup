---
name: data-science-utils
description: Reusable Python utilities for tabular data science. Use for data inspection and cleaning, missing-value imputation, outlier filtering, feature scaling and encoding, feature selection, descriptive statistics, EDA plots and self-contained HTML reports, classification and regression evaluation and tuning with scikit-learn, A/B testing, time-series analysis, text preprocessing, and language detection or translation. Trigger when a task involves pandas DataFrames, scikit-learn models, exploratory data analysis, model diagnostics, experiment analysis, forecasting, or NLP preparation in Python.
compatibility: Requires Python 3.14+ and the core packages in requirements.txt. Text and translation helpers need the optional dependencies in requirements-optional.txt.
metadata:
  version: "0.1.0"
  package: "utils"
  source: "Data Science Utils"
  python: ">=3.14"
---

# Data Science Utils

This skill bundles the complete `utils` Python package (import name `utils`) and its dependency manifests. It is self-contained: the target project does not need the original repository, and the bundled code does not import anything from it.

Use it for notebook-friendly tabular analysis and modeling with pandas, scikit-learn, statsmodels, and seaborn.

## When to use this skill

Use this skill when the user wants to:

- Profile a new tabular dataset, check dtypes, missingness, duplicates, cardinality, and data-quality issues.
- Clean data: drop columns, impute missing values, filter outliers, convert binary columns.
- Preprocess features: scale, transform, and encode categorical variables for scikit-learn.
- Select features with correlations, chi-square tests, VIF, or univariate importance.
- Evaluate or tune a binary classifier or a regressor with repeated cross-validation.
- Analyze an A/B test: sample size, normality, variance, t-test, Mann-Whitney, chi-square, z-test.
- Analyze a time series: decomposition, stationarity, lag/rolling/date features, walk-forward CV, forecast metrics.
- Clean text, build word clouds, detect languages, or translate text columns.
- Produce a self-contained HTML EDA report.

Do not use this skill for deep learning, distributed computing, or non-tabular data pipelines. The package is small, in-memory, and pandas-centric.

## Setup

### 1. Locate the skill directory

Set `SKILL_DIR` to the absolute path of the folder that contains this `SKILL.md` (the folder is named `data-science-utils`).

### 2. Install dependencies

```bash
# Core dependencies
uv add -r "<SKILL_DIR>/requirements.txt"

# Text and translation helpers only
uv add -r "<SKILL_DIR>/requirements-optional.txt"

# Everything
uv add -r "<SKILL_DIR>/requirements-all.txt"
```

Run these commands from the target uv project (the directory containing `pyproject.toml`; run `uv init` first if needed). `uv add` records the dependencies in the project. The source project targets Python 3.14+; if the target project uses an older interpreter, verify dependency compatibility before relying on the package.

For NLTK-based text helpers, download the corpora once:

```python
import nltk

for package in ("stopwords", "punkt", "wordnet"):
    nltk.download(package)
```

### 3. Make `utils` importable

Preferred: import in place from the skill without copying anything.

```python
import sys
from pathlib import Path

SKILL_DIR = Path(r"<absolute path to this skill>")
sys.path.insert(0, str(SKILL_DIR / "scripts"))

from utils import check_data_information, feature_scaling
```

Alternative: copy the package into the target project, then use a normal import.

```python
import shutil
from pathlib import Path

SKILL_DIR = Path(r"<absolute path to this skill>")
shutil.copytree(SKILL_DIR / "scripts" / "utils", Path.cwd() / "utils", dirs_exist_ok=True)
```

Or run the helper:

```bash
python "<SKILL_DIR>/scripts/install_into_project.py" /path/to/project --with-requirements
```

### 4. Verify the environment

```bash
python "<SKILL_DIR>/scripts/smoke_test.py"
```

Expected final line: `data-science-utils smoke test passed`.

## Critical import rule

The top-level package keeps backwards-compatible aliases from the regression module. As a result, these unsuffixed names are **regression** helpers:

`get_model_pipeline`, `get_hyperparameters`, `tune_pipelines`, `tune_single_model`, `tune_all_models`, `compare_cv_metrics`

For classification, import the classification module explicitly or use the `_classification` suffix:

```python
# Classification-specific helpers
from utils.classification_evals_and_tuning import (
    eval_classification,
    get_model_pipeline,
    get_hyperparameters,
    tune_single_model,
    compare_cv_metrics,
)

# Regression-specific helpers
from utils.regression_evals_and_tuning import (
    eval_regression,
    get_model_pipeline,
    get_hyperparameters,
    tune_single_model,
    compare_cv_metrics,
)
```

`eval_classification` and `eval_regression` are unambiguous at the top level.

## Module map

| Module | Use it for | Reference |
| --- | --- | --- |
| `preprocessing` | Profiling, dropping columns, imputation, outliers, scaling, encoding | [preprocessing.md](references/api/preprocessing.md) |
| `feature_selection` | Correlations, categorical association, VIF, univariate importance | [feature-selection.md](references/api/feature-selection.md) |
| `statistics` | Numerical, categorical, and date summaries; distribution typing | [statistics.md](references/api/statistics.md) |
| `visualization` | Distribution, count, relationship, and correlation plots | [visualization.md](references/api/visualization.md) |
| `classification_evals_and_tuning` | Binary classification diagnostics and tuning | [classification.md](references/api/classification.md) |
| `regression_evals_and_tuning` | Regression diagnostics and tuning | [regression.md](references/api/regression.md) |
| `ab_testing` | Sample sizing, assumption checks, hypothesis tests | [ab-testing.md](references/api/ab-testing.md) |
| `time_series` | Decomposition, stationarity, features, CV, forecast metrics | [time-series.md](references/api/time-series.md) |
| `text_preprocessing` | Text cleaning, tokenization, word clouds, frequency analysis | [text.md](references/api/text.md) |
| `translation_utils` | Language detection and batched translation | [translation.md](references/api/translation.md) |
| `eda_report` | Self-contained HTML EDA report | [eda-report.md](references/api/eda-report.md) |

The complete public API is indexed in [references/api-index.md](references/api-index.md). `_ml_common.py` and `_plotting.py` are internal implementation details.

## Workflow recipes

### A. First-pass EDA and data quality

```python
import pandas as pd

from utils import (
    check_data_information,
    describe_categorical_combined,
    describe_numerical_combined,
    generate_eda_report,
    identify_distribution_types,
    plot_correlation_heatmap,
    plot_dynamic_boxplots_violinplots,
    plot_dynamic_countplot,
    plot_dynamic_hisplots_kdeplots,
)

df = pd.read_csv("data.csv")

# Dtypes, nulls, duplicates, unique values, zero/negative counts, empty strings,
# numeric-in-object counts, and cardinality.
info = check_data_information(df, df.columns.tolist())

num_cols = df.select_dtypes(include="number").columns.tolist()
cat_cols = df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()

describe_numerical_combined(df, num_cols)
describe_categorical_combined(df, cat_cols)
identify_distribution_types(df, num_cols)

plot_dynamic_hisplots_kdeplots(df, num_cols, ncols=3, figsize=(15, 10))
plot_dynamic_boxplots_violinplots(df, num_cols, ncols=3, figsize=(15, 10))
plot_dynamic_countplot(df, cat_cols, ncols=3, figsize=(15, 10))

numeric_without_target = [c for c in num_cols if c != "target"]
plot_correlation_heatmap(df, numeric_without_target, corr_method="spearman")

generate_eda_report(
    df,
    target="target",
    output_path="eda_report.html",
    corr_method="spearman",
)
```

Interpret `check_data_information` before cleaning: high null percentages suggest imputation or dropping; a cardinality ratio near 1.0 often identifies an ID column; constant columns carry no information; empty strings are hidden nulls; "numeric in object" indicates a type-conversion candidate.

### B. Cleaning and preprocessing without leakage

```python
from sklearn.model_selection import train_test_split

from utils import (
    change_binary_dtype,
    drop_columns,
    feature_encoding,
    feature_scaling,
    filter_outliers,
    handle_missing_values,
)

# 1. Drop identifiers, constants, and leakage columns.
df = drop_columns(df, ["id", "constant_column"])

# 2. Fix binary representation before encoding.
df["is_active"] = change_binary_dtype(df, "is_active", target_type="numerical")

# 3. Split BEFORE fitting any data-dependent transformation.
train, test = train_test_split(
    df, test_size=0.2, random_state=42, stratify=df["target"]
)

# 4. Impute. KNN returns a reusable fitted imputer.
train, imputer = handle_missing_values(
    train, ["income"], strategy="knn", n_neighbors=5
)
test, _ = handle_missing_values(
    test, ["income"], strategy="knn", imputer=imputer
)

# For median/mean/mode the returned imputer is None: the function fits the
# statistic on the frame you pass. Either apply the train statistic to test
# manually, or use sklearn.impute.SimpleImputer for a reusable transformer.

# 5. Detect outliers on training data; filter only if the task justifies it.
outlier_summary = filter_outliers(
    train, ["income"], method="iqr", threshold=1.5, detect_only=True, verbose=False
)
train = filter_outliers(train, ["income"], method="iqr", threshold=1.5)

# 6. Scale with a fitted scaler.
train, scaler = feature_scaling(
    train, columns=["age", "income"], method="robust"
)
test, _ = feature_scaling(
    test, columns=["age", "income"], scaler=scaler
)

# 7. Encode with fitted encoders.
train, encoders = feature_encoding(
    train,
    ordinal_columns=["grade"],
    nominal_columns=["city"],
    binary_columns=["channel"],
    frequency_columns=["route"],
    ordinal_categories={"grade": ["low", "medium", "high"]},
    target=train["target"],
)
test, _ = feature_encoding(
    test,
    ordinal_columns=["grade"],
    nominal_columns=["city"],
    binary_columns=["channel"],
    frequency_columns=["route"],
    ordinal_categories={"grade": ["low", "medium", "high"]},
    encoders=encoders,
)
```

`feature_encoding` uses cross-fitting for mean encoding. Pass `target` when fitting mean-encoded columns on train, and pass `encoders` on validation/test. `drop_first=True` is the default for one-hot columns.

### C. Feature selection

```python
from utils import (
    analyze_categorical_relationships,
    calculate_correlation_tabular,
    calculate_feature_importance,
    calculate_vif,
)

num_features = [c for c in num_cols if c != "target"]

# Feature-feature and feature-target correlations (also prints tables).
feature_corr, target_corr = calculate_correlation_tabular(
    df, target_col="target", method="spearman", corr_type="both"
)

# Chi-square + Cramer's V for categorical features.
cat_assoc = analyze_categorical_relationships(
    df, features=["city", "channel"], target="target"
)

# VIF on numeric features plus the target (the target is excluded internally).
vif = calculate_vif(df[num_features + ["target"]], target_col="target")

# Univariate importance.
importance = calculate_feature_importance(
    df[num_features], df["target"], task="classification", method="mutual_info", k="all"
)
```

Use `method="anova"` or `"chi2"` for classification and `"f_regression"` or `"mutual_info"` for regression. `chi2` requires non-negative features.

### D. Binary classification evaluation and tuning

```python
import pandas as pd
from sklearn.model_selection import train_test_split

from utils.classification_evals_and_tuning import (
    compare_cv_metrics,
    eval_classification,
    get_model_pipeline,
    tune_single_model,
)

X = df.drop(columns=["target"])
y = df["target"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

model = get_model_pipeline("randomforest", random_state=42)
model.fit(X_train, y_train)

metrics = eval_classification(
    model=model,
    X_test=X_test,
    y_test=y_test,
    X_train=X_train,
    y_train=y_train,
    show_plots=False,      # do not call plt.show
    display=False,         # suppress the metric log
    return_figures=True,   # add metrics["figures"]
)

comparison = compare_cv_metrics({"random_forest": metrics}, as_numeric=True)

search, seconds = tune_single_model(
    "randomforest",
    X_train,
    y_train,
    X_test,
    y_test,
    scoring="accuracy",
    search_method="random",
    n_iter=20,
    n_splits=3,
    n_repeats=1,
    display=False,
    plot_learning_curves=False,
    show=False,
)
best_model = search.best_estimator_
```

`eval_classification` requires a model with `predict_proba` and currently supports **binary** classification only. Its result contains `metrics["cv"]` keyed by `accuracy`, `precision`, `recall`, `f1`, and `roc_auc`, each with `test_mean`, `test_std`, `train_mean`, and `train_std`, plus single-run metrics and `confusion_matrix`.

Supported classification model keys: `logisticregression`, `knn`, `decisiontree`, `randomforest`, `gb`, `xgboost`.

### E. Regression evaluation and tuning

```python
from utils.regression_evals_and_tuning import (
    compare_cv_metrics,
    eval_regression,
    get_model_pipeline,
    tune_single_model,
)

model = get_model_pipeline("randomforest", random_state=42)
model.fit(X_train, y_train)

metrics = eval_regression(
    model=model,
    X_test=X_test,
    y_test=y_test,
    X_train=X_train,
    y_train=y_train,
    show_plots=False,
    display=False,
)

comparison = compare_cv_metrics({"random_forest": metrics}, as_numeric=True)

search, seconds = tune_single_model(
    "randomforest",
    X_train,
    y_train,
    X_test,
    y_test,
    scoring="neg_mean_squared_error",
    search_method="random",
    n_iter=20,
    n_splits=3,
    n_repeats=1,
    display=False,
    plot_learning_curves=False,
    show=False,
)
```

`eval_regression` reports `mae`, `mse`, `rmse`, `mape`, and `r2`. Supported regression model keys: `linearregression`, `ridge`, `lasso`, `elasticnet`, `knn`, `decisiontree`, `randomforest`, `gb`, `xgboost`.

`get_model_pipeline` wraps only the estimator. Apply imputation, scaling, and encoding yourself before fitting, or build a full scikit-learn `Pipeline` with preprocessing steps and pass it to `tune_pipelines`.

### F. A/B testing

```python
from utils import analyze_ab_test_results, calculate_sample_size

# Sample size per variant for a conversion metric.
n_per_group = calculate_sample_size(
    baseline_rate=0.10,
    minimum_detectable_effect=0.02,  # absolute difference: 10% -> 12%
    power=0.8,
    alpha=0.05,
    metric_type="proportion",
)

# Continuous metric: raw difference of 5 with standard deviation 10.
n_continuous = calculate_sample_size(
    100, 5, metric_type="continuous", std_dev=10
)

result = analyze_ab_test_results(
    experiment_df,
    metric_col="converted",
    group_col="group",
    metric_type="binary",       # or "continuous"
    control_label="A",
    treatment_label="B",
    alpha=0.05,
)
print(result["p_value"], result["absolute_lift"], result["relative_lift"])
print(result["ci_lower"], result["ci_upper"])
```

`analyze_ab_test_results` checks assumptions and selects an appropriate test automatically. Use the individual helpers (`check_normality`, `check_variance_homogeneity`, `perform_t_test`, `perform_mann_whitney_u_test`, `perform_chi_squared_test`, `perform_z_test_proportions`) when the user wants explicit control.

### G. Time series

```python
import pandas as pd

from utils import (
    check_stationarity,
    create_date_features,
    create_lag_features,
    create_rolling_features,
    decompose_series,
    evaluate_forecast,
    make_stationary,
    plot_acf_pacf,
    split_time_series,
    time_series_cv_splits,
)

series = df.set_index("date")["sales"].sort_index().asfreq("D").interpolate()

decomposition = decompose_series(series, model="additive", period=7)
stationarity = check_stationarity(series)
stationary_series = make_stationary(series, seasonal_period=7)["transformed"]

features = create_date_features(df, "date")
features = create_lag_features(features, ["sales"], lags=[1, 7, 14])
features = create_rolling_features(features, ["sales"], windows=[7, 30])
features = features.dropna()  # lag/rolling windows create leading NaNs

train, test = split_time_series(features, test_size=0.2)

for fold_train, fold_test in time_series_cv_splits(features, n_splits=5, test_size=0.2):
    ...  # fit on fold_train, predict fold_test

metrics = evaluate_forecast(y_true, y_pred)
plot_acf_pacf(series, lags=40)
```

`split_time_series` and `time_series_cv_splits` assume the frame is already sorted by time. `evaluate_forecast` returns `MAE`, `MSE`, `RMSE`, `MAPE`, `sMAPE`, and `MPE`; `MAPE` is `NaN` when any actual value is zero.

### H. Text preprocessing and translation

```python
from utils import (
    TextPreprocessor,
    TextVisualizer,
    detect_language_rows,
    extract_ngrams,
    get_text_stats,
    quick_clean,
    run_translation_pipeline,
    translate_dataframe,
)

preprocessor = TextPreprocessor(language="english", custom_stopwords={"foo"})
clean_df = preprocessor.preprocess_dataframe(
    df, columns=["title", "description"], options={"remove_stopwords": False}
)

# Faster vectorized variant for larger frames.
clean_df = preprocessor.preprocess_dataframe_vectorized(
    df, columns=["title", "description"]
)

df["clean_text"] = quick_clean(df["text"])
stats = get_text_stats(df, ["clean_text"])
bigrams = extract_ngrams("machine learning is fun", n=2)

visualizer = TextVisualizer()
visualizer.create_wordclouds(df, text_columns=["clean_text"])
visualizer.analyze_word_frequencies(df, text_columns=["clean_text"], top_n=20)

# Language detection: target_langs=None means "all non-English".
target_rows, other_rows = detect_language_rows(
    df, columns=["text"], target_langs=None, use_parallel=True
)

# Translate selected columns.
translated_df = translate_dataframe(
    df, columns=["text"], src="auto", dest="en", batch_size=50
)

# Detect, translate, and recombine in one call.
final_df = run_translation_pipeline(
    df, columns=["text"], target_langs=["es", "fr"], dest="en"
)
```

Text helpers need the optional `text` dependencies; translation needs `deep-translator` and `langid`. Translation calls an external service, so respect rate limits and avoid sending sensitive data. `correct_spelling` is deliberately slow.

### I. Self-contained HTML EDA report

```python
from utils import generate_eda_report

html = generate_eda_report(
    df,
    target="target",
    output_path="eda_report.html",
    title="Customer Churn EDA",
    n_top_categories=10,
    corr_method="spearman",
    corr_threshold=0.8,
    verbose=True,
)
```

The report includes data quality, summaries, correlations, distributions, categorical counts, and optional target analysis. Images are embedded as base64, so the file is self-contained and can be large.

## Return-value contract

| Function | Returns |
| --- | --- |
| `check_data_information` | `pd.DataFrame` profile |
| `drop_columns` | New `pd.DataFrame` |
| `change_binary_dtype` | `pd.Series` (assign it back) |
| `handle_missing_values` | `(df, imputer_or_None)` |
| `filter_outliers` | summary DataFrame, filtered DataFrame, or `(df, mask)` |
| `feature_scaling` | `(df, scaler_or_dict_of_scalers)` |
| `feature_encoding` | `(df, encoders_dict)` |
| `calculate_*`, `describe_*`, `identify_*` | `pd.DataFrame` or tuple of DataFrames |
| plotting helpers | `None` (they display); `TextVisualizer` methods return a `Figure` |
| `eval_classification` / `eval_regression` | metrics `dict` |
| `compare_cv_metrics` | comparison `pd.DataFrame` |
| `tune_pipelines` | `(dict_of_search_objects, fit_times)` |
| `tune_single_model` | `(search_object, fit_time)` |
| `tune_all_models` | `(dict_of_search_objects, fit_times)` |
| `generate_eda_report` | HTML `str` |

## Leakage-safe sequence

1. Split rows into train and test before fitting any transformation.
2. Fit imputers, scalers, and encoders on train only; reuse the fitted objects on test.
3. Filter or cap outliers using training statistics only.
4. Fit the model on train; evaluate on test with `eval_*`.
5. Use repeated cross-validation on train for stable estimates; do not tune on the test set.
6. Keep `random_state` fixed when comparing models.

## Gotchas and edge cases

- **Regression aliases:** unsuffixed `get_model_pipeline`, `tune_single_model`, and related names are regression helpers. Use `_classification` or module-level imports for classification.
- **Binary only:** `eval_classification` rejects multiclass targets and models without `predict_proba`.
- **Simple imputation:** `handle_missing_values` returns `imputer=None` for `median`, `mean`, `mode`, `ffill`, and `bfill`; it fits on the frame passed. Use `knn` for a reusable imputer, or `sklearn.impute.SimpleImputer` for strict train/test consistency. When reusing a KNN imputer, keep `strategy="knn"`; the default strategy is `"median"` and would ignore the supplied imputer.
- **Log transforms:** `feature_scaling(..., apply_log=True)` raises if any observed value is negative. `power` with `box-cox` requires strictly positive values; use `yeo-johnson` otherwise.
- **Encoding defaults:** `drop_first=True` drops the first one-hot category. Mean encoding requires `target` on train and `encoders` on test. Unknown categories are controlled by `handle_unknown`.
- **Outlier filtering:** `filter_outliers` keeps `NaN` rows and does not mutate the input. `detect_only=True` returns a summary; `return_mask=True` returns `(filtered_df, mask)`.
- **Time-series hygiene:** decomposition and ACF/PACF plots expect a regularly spaced series without missing values; resample or interpolate first. Lag and rolling features create leading `NaN`s, so drop or impute them before fitting.
- **Language detection on Windows/notebooks:** `detect_language_rows` uses process-based parallelism by default. If the process pool misbehaves, set `use_parallel=False`.
- **Plotting in batch jobs:** call `show_plots=False` on `eval_*` and `show=False` on tuning helpers to avoid blocking. Use `display=False` to suppress logs. `return_figures=True` adds figures to classification metrics.
- **Tuning cost:** `tune_all_models` with grid search can be expensive. Prefer `search_method="random"`, a small `n_iter`, `n_splits=3`, `n_repeats=1`, and `n_jobs=-1` for exploration.
- **Model pipelines:** `get_model_pipeline` contains only the estimator, not preprocessing. Build a full scikit-learn `Pipeline` when you need one object for training and inference.
- **Optional dependencies:** `import utils` succeeds without text/translation extras because those imports are lazy, but calls raise an actionable `ImportError`. If the message mentions `pip install`, install the missing package with `uv add <package>` in the target project instead.
- **Python version:** the source package targets Python 3.14+; `xgboost` and other compiled dependencies may lag on very new interpreters.

## References

- [API index](references/api-index.md) — every public function and class.
- [Preprocessing](references/api/preprocessing.md)
- [Feature selection](references/api/feature-selection.md)
- [Statistics](references/api/statistics.md)
- [Visualization](references/api/visualization.md)
- [Classification](references/api/classification.md)
- [Regression](references/api/regression.md)
- [A/B testing](references/api/ab-testing.md)
- [Time series](references/api/time-series.md)
- [Text processing](references/api/text.md)
- [Translation](references/api/translation.md)
- [EDA report](references/api/eda-report.md)

## Verification checklist

Before reporting a result as complete:

- [ ] `python "<SKILL_DIR>/scripts/smoke_test.py"` passes.
- [ ] The target project can import the functions used.
- [ ] Train/test transforms were fit on train and reused on test.
- [ ] `eval_classification` received a binary target and a `predict_proba` model.
- [ ] Plots were suppressed in headless runs, or saved explicitly.
- [ ] Optional dependencies are installed before calling text or translation helpers.
