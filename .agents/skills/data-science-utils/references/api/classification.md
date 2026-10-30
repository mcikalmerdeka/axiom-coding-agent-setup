# Classification API

Source: `scripts/utils/classification_evals_and_tuning.py`

> Auto-generated from the bundled source. Re-run
> `python scripts/dev/generate_references.py` after changing the package.


Binary classification evaluation, model comparison, and hyperparameter tuning.

## Quick index

| Name | Summary |
| --- | --- |
| `eval_classification` | Comprehensively evaluate a classification model using multiple metrics and cross-validation techniques |
| `compare_cv_metrics` | Compare cross-validated metrics from multiple classification models in a single table |
| `tune_pipelines` | Perform hyperparameter tuning with grid/random search and optional curves |
| `get_model_pipeline` | Create a pipeline for a specific model |
| `get_hyperparameters` | Get hyperparameter grid for a specific model |
| `tune_single_model` | Tune a single model using grid or random search |
| `tune_all_models` | Tune multiple classification models using grid or random search |

### `eval_classification`

```python
def eval_classification(model, X_test, y_test, X_train, y_train, custom_metrics=None, plot_confusion_matrix=True, plot_roc_curve=True, plot_pr_curve=True, plot_calibration_curve=True, plot_threshold_analysis=True, validate_confusion_matrix=False, n_splits=5, n_repeats=3, random_state=42, show_plots=True, return_figures=False, display=True) -> dict
```

Comprehensively evaluate a classification model using multiple metrics
and cross-validation techniques.

This function provides a robust evaluation of a classification model by:
1. Performing single-run predictions
2. Conducting cross-validated performance assessment
3. Computing multiple performance metrics
4. Optionally visualizing the cross-validated diagnostics

All cross-validated diagnostics reuse one set of fold predictions, so the
model is fitted exactly once per fold.

**Parameters**
model : sklearn estimator
    The classification model to be evaluated
X_test : array-like
    Test feature dataset
y_test : array-like
    Test target labels
X_train : array-like
    Training feature dataset
y_train : array-like
    Training target labels
custom_metrics : dict, optional (default=None)
    Additional custom metric functions to evaluate
    Format: {'metric_name': metric_function}
plot_confusion_matrix : bool, optional (default=True)
    Whether to display the confusion matrix
plot_roc_curve : bool, optional (default=True)
    Whether to display the cross-validated ROC curve with mean AUC
plot_pr_curve : bool, optional (default=True)
    Whether to display the cross-validated Precision-Recall curve with Average Precision
plot_calibration_curve : bool, optional (default=True)
    Whether to display the cross-validated Calibration curve (reliability diagram)
plot_threshold_analysis : bool, optional (default=True)
    Whether to display the Decision Threshold Analysis curve
validate_confusion_matrix : bool, optional (default=False)
    Whether to use the normal confusion matrix or validated confusion matrix
n_splits : int, optional (default=5)
    Number of splits for cross-validation
n_repeats : int, optional (default=3)
    Number of times to repeat cross-validation
random_state : int, optional (default=42)
    Seed for reproducibility of cross-validation splits
show_plots : bool, optional (default=True)
    Whether to call ``plt.show`` after building each figure. Set False to
    keep figures open without blocking (notebooks, tests, batch jobs).
return_figures : bool, optional (default=False)
    Whether to add a ``figures`` entry to the returned dictionary. The
    default result schema is unchanged when this is False.
display : bool, optional (default=True)
    Whether to log the metric summary at INFO level. False suppresses the
    summary without affecting returned metrics or figures.

**Example**
>>> metrics = eval_classification(
>>>     model=model,
>>>     X_test=X_test,
>>>     y_test=y_test,
>>>     X_train=X_train,
>>>     y_train=y_train
>>> )
>>> print(metrics)

**Returns**
dict
    Comprehensive dictionary of model performance metrics including:
    - Cross-validated metrics
    - Single-run metrics
    - Cross-validated confusion matrix

**Raises**
Exception
    If any error occurs during model evaluation

### `compare_cv_metrics`

```python
def compare_cv_metrics(metrics_dict: dict, *, as_numeric: bool=False) -> pd.DataFrame
```

Compare cross-validated metrics from multiple classification models in a single table.

This function extracts only the cross-validation metrics (not single-run metrics)
from multiple model evaluations and presents them in a comparison DataFrame.

**Parameters**
metrics_dict : dict
    Dictionary with model names as keys and metrics dictionaries as values.
    Format: {'model_name': metrics_dict_from_eval_classification}
as_numeric : bool, optional (default=False)
    Return raw float means instead of the formatted percentage strings.

**Returns**
pd.DataFrame
    DataFrame with models as rows and CV metrics as columns

**Example**
>>> metrics_rf = eval_classification(model=rf, X_train=X_train, y_train=y_train, 
...                                  X_test=X_test, y_test=y_test)
>>> metrics_xgb = eval_classification(model=xgb, X_train=X_train, y_train=y_train,
...                                   X_test=X_test, y_test=y_test)
>>> comparison = compare_cv_metrics({
...     'Random Forest': metrics_rf,
...     'XGBoost': metrics_xgb
... })
>>> display(comparison)

### `tune_pipelines`

```python
def tune_pipelines(pipedict: dict, param_grid: dict, X_train, y_train, X_test, y_test, scoring='accuracy', search_method='grid', n_iter=50, n_splits=5, n_repeats=3, random_state=42, display=True, n_jobs=-1, plot_validation_curves=False, plot_learning_curves=True, progress_bar=False, show=True) -> tuple
```

Perform hyperparameter tuning with grid/random search and optional curves.

This adapter delegates to the shared ML tuning layer. See
``utils._ml_common.tune_models`` for the full parameter documentation.

**Returns**
tuple
    (dictionary of fitted search objects, list of fitting times)

### `get_model_pipeline`

```python
def get_model_pipeline(model_name: str, random_state: int=42) -> Pipeline
```

Create a pipeline for a specific model.

**Parameters**
model_name : str
    Name of the model. Supported: 'logisticregression', 'knn', 'decisiontree',
    'randomforest', 'gb', 'xgboost'
random_state : int, optional (default=42)
    Random seed for reproducibility

**Returns**
Pipeline
    Scikit-learn pipeline with the specified model

**Raises**
ValueError
    If model_name is not supported

### `get_hyperparameters`

```python
def get_hyperparameters(model_name: str, search_method: str='grid') -> dict
```

Get hyperparameter grid for a specific model.

**Parameters**
model_name : str
    Name of the model to get hyperparameters for
search_method : str, optional (default='grid')
    'grid' returns smaller grids suitable for exhaustive search,
    'random' returns larger distributions for random sampling

**Returns**
dict
    Dictionary of hyperparameters for search

**Raises**
ValueError
    If model_name is not supported

### `tune_single_model`

```python
def tune_single_model(model_name: str, X_train, y_train, X_test, y_test, scoring='accuracy', search_method='grid', n_iter=50, n_splits=5, n_repeats=3, random_state=42, display=True, plot_validation_curves=False, plot_learning_curves=True, progress_bar=False, show=True) -> tuple
```

Tune a single model using grid or random search.

**Parameters**
model_name : str
    Name of the model to tune. Supported: 'logisticregression', 'knn', 
    'decisiontree', 'randomforest', 'gb', 'xgboost'
X_train, y_train : array-like
    Training data
X_test, y_test : array-like
    Test data
scoring : str, optional (default='accuracy')
    Metric to optimize
search_method : str, optional (default='grid')
    'grid' for GridSearchCV, 'random' for RandomizedSearchCV
n_iter : int, optional (default=50)
    Number of iterations for random search
n_splits : int, optional (default=5)
    Number of CV splits
n_repeats : int, optional (default=3)
    Number of CV repeats
random_state : int, optional (default=42)
    Random seed
display : bool, optional (default=True)
    Whether to print results
plot_validation_curves : bool, optional (default=False)
    Whether to plot validation curves
plot_learning_curves : bool, optional (default=True)
    Whether to plot learning curves after tuning
progress_bar : bool, optional (default=False)
    Whether to show progress bar

**Returns**
tuple
    (fitted search object, fitting time in seconds)

**Example**
>>> model, time = tune_single_model(
>>>     'randomforest', X_train, y_train, X_test, y_test,
>>>     search_method='random', n_iter=30
>>> )
>>> print(model.best_params_)

### `tune_all_models`

```python
def tune_all_models(X_train, y_train, X_test, y_test, models: list=None, scoring='accuracy', search_method='grid', n_iter=50, n_splits=5, n_repeats=3, random_state=42, display=True, plot_learning_curves=True, progress_bar=True, show=True) -> tuple
```

Tune multiple classification models using grid or random search.

**Parameters**
X_train, y_train : array-like
    Training data
X_test, y_test : array-like
    Test data
models : list, optional (default=None)
    List of model names to tune. If None, tunes all supported models:
    ['logisticregression', 'knn', 'decisiontree', 'randomforest', 'gb', 'xgboost']
scoring : str, optional (default='accuracy')
    Metric to optimize
search_method : str, optional (default='grid')
    'grid' for GridSearchCV, 'random' for RandomizedSearchCV
n_iter : int, optional (default=50)
    Number of iterations for random search
n_splits : int, optional (default=5)
    Number of CV splits
n_repeats : int, optional (default=3)
    Number of CV repeats
random_state : int, optional (default=42)
    Random seed
display : bool, optional (default=True)
    Whether to print results
plot_learning_curves : bool, optional (default=True)
    Whether to plot learning curves for each model after tuning
progress_bar : bool, optional (default=True)
    Whether to show progress bar

**Returns**
tuple
    (dictionary of fitted search objects, list of fitting times)

**Example**
>>> # Tune only specific models
>>> fitted, times = tune_all_models(
>>>     X_train, y_train, X_test, y_test,
>>>     models=['randomforest', 'xgboost'],
>>>     search_method='random', n_iter=30
>>> )
