"""Shared cross-validation collection and aggregation helpers for ML utilities."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Callable, Mapping, Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.base import clone
from sklearn.metrics import get_scorer
from sklearn.model_selection import (
    GridSearchCV,
    RandomizedSearchCV,
    RepeatedKFold,
    RepeatedStratifiedKFold,
    learning_curve,
    validation_curve,
)
from tqdm import tqdm

from ._plotting import finalize_figure

logger = logging.getLogger("utils.ml")


def _configure_logging(display: bool) -> None:
    """Route ML diagnostics to INFO when display is on; suppress them otherwise."""
    if display:
        logger.setLevel(logging.INFO)
        if not logger.handlers and not logging.getLogger().handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(message)s"))
            logger.addHandler(handler)
    else:
        logger.setLevel(logging.WARNING)


@dataclass
class FoldResult:
    """Predictions collected from a single cross-validation fold."""

    y_true: np.ndarray
    y_pred: np.ndarray
    y_proba: np.ndarray | None
    y_train_true: np.ndarray
    y_train_pred: np.ndarray
    train_index: np.ndarray
    val_index: np.ndarray
    y_train_proba: np.ndarray | None = None


def _to_numpy(values):
    if isinstance(values, (pd.DataFrame, pd.Series)):
        return values.to_numpy()
    if sparse.issparse(values):
        return values
    return np.asarray(values)


def _positive_class_proba(y_proba: np.ndarray) -> np.ndarray:
    """Return the positive-class probability vector for binary predictions."""
    y_proba = np.asarray(y_proba)
    if y_proba.ndim == 2:
        return y_proba[:, 1]
    return y_proba


def collect_fold_results(
    estimator,
    X,
    y,
    cv,
    *,
    predict_proba: bool = True,
) -> list[FoldResult]:
    """Fit one clone per fold and collect train/validation predictions.

    Fitting happens exactly once per fold, so callers can reuse the same
    predictions for metrics and every downstream diagnostic plot.
    """
    X = _to_numpy(X)
    y = _to_numpy(y)
    results: list[FoldResult] = []

    for train_index, val_index in cv.split(X, y):
        model = clone(estimator)
        model.fit(X[train_index], y[train_index])

        y_pred = model.predict(X[val_index])
        y_train_pred = model.predict(X[train_index])

        y_proba = None
        y_train_proba = None
        if predict_proba:
            if not hasattr(model, "predict_proba"):
                raise ValueError(
                    "predict_proba=True requires an estimator with predict_proba."
                )
            y_proba = model.predict_proba(X[val_index])
            y_train_proba = model.predict_proba(X[train_index])

        results.append(
            FoldResult(
                y_true=y[val_index],
                y_pred=y_pred,
                y_proba=y_proba,
                y_train_true=y[train_index],
                y_train_pred=y_train_pred,
                train_index=train_index,
                val_index=val_index,
                y_train_proba=y_train_proba,
            )
        )

    return results


def _summarize(test_scores: Sequence[float], train_scores: Sequence[float]) -> dict:
    test_scores = np.asarray(test_scores, dtype=float)
    train_scores = np.asarray(train_scores, dtype=float)
    return {
        "test_mean": float(np.mean(test_scores)),
        "test_std": float(np.std(test_scores)),
        "train_mean": float(np.mean(train_scores)),
        "train_std": float(np.std(train_scores)),
    }


def aggregate_fold_metrics(
    results: Sequence[FoldResult],
    metric_funcs: Mapping[str, Callable],
    *,
    probability_metrics: Mapping[str, Callable] | None = None,
) -> dict[str, dict[str, float]]:
    """Aggregate per-fold metrics into the public mean/std schema.

    ``metric_funcs`` receive ``(y_true, y_pred)``; ``probability_metrics``
    receive ``(y_true, y_proba)`` where ``y_proba`` is the positive-class
    probability vector.
    """
    metrics: dict[str, dict[str, float]] = {}

    for name, metric_func in metric_funcs.items():
        test_scores = [
            metric_func(result.y_true, result.y_pred) for result in results
        ]
        train_scores = [
            metric_func(result.y_train_true, result.y_train_pred)
            for result in results
        ]
        metrics[name] = _summarize(test_scores, train_scores)

    for name, metric_func in (probability_metrics or {}).items():
        test_scores = []
        train_scores = []
        for result in results:
            if result.y_proba is None or result.y_train_proba is None:
                raise ValueError(
                    f"Metric '{name}' needs probabilities; collect folds with "
                    "predict_proba=True and an estimator that supports it."
                )
            test_scores.append(
                metric_func(result.y_true, _positive_class_proba(result.y_proba))
            )
            train_scores.append(
                metric_func(
                    result.y_train_true,
                    _positive_class_proba(result.y_train_proba),
                )
            )
        metrics[name] = _summarize(test_scores, train_scores)

    return metrics


@dataclass(frozen=True)
class TaskConfig:
    """Task-specific cross-validation and default scoring configuration."""

    name: str
    cv_factory: Callable[[int, int, int], object]
    default_scoring: str


def _classification_cv(n_splits: int, n_repeats: int, random_state: int):
    return RepeatedStratifiedKFold(
        n_splits=n_splits, n_repeats=n_repeats, random_state=random_state
    )


def _regression_cv(n_splits: int, n_repeats: int, random_state: int):
    return RepeatedKFold(
        n_splits=n_splits, n_repeats=n_repeats, random_state=random_state
    )


CLASSIFICATION_TASK = TaskConfig(
    name="classification",
    cv_factory=_classification_cv,
    default_scoring="accuracy",
)
REGRESSION_TASK = TaskConfig(
    name="regression",
    cv_factory=_regression_cv,
    default_scoring="neg_mean_squared_error",
)


def _draw_learning_curves(
    estimator,
    X_train,
    y_train,
    *,
    scoring: str,
    name: str,
    cv,
    show: bool = True,
):
    """Plot learning curves using only the training data and its CV."""
    train_sizes = np.linspace(0.1, 1.0, 10)

    train_sizes_abs, train_scores, test_scores = learning_curve(
        estimator=estimator,
        X=X_train,
        y=y_train,
        train_sizes=train_sizes,
        cv=cv,
        scoring=scoring,
        n_jobs=1,
        return_times=False,
    )

    train_scores_mean = np.mean(train_scores, axis=1)
    train_scores_std = np.std(train_scores, axis=1)
    test_scores_mean = np.mean(test_scores, axis=1)
    test_scores_std = np.std(test_scores, axis=1)

    fig, ax = plt.subplots(figsize=(12, 8))

    ax.plot(
        train_sizes_abs,
        train_scores_mean,
        "o-",
        color="blue",
        label="Training Score",
        linewidth=2.5,
        markersize=8,
    )
    ax.fill_between(
        train_sizes_abs,
        train_scores_mean - train_scores_std,
        train_scores_mean + train_scores_std,
        alpha=0.2,
        color="blue",
    )

    ax.plot(
        train_sizes_abs,
        test_scores_mean,
        "o-",
        color="darkorange",
        label="Validation Score",
        linewidth=2.5,
        markersize=8,
    )
    ax.fill_between(
        train_sizes_abs,
        test_scores_mean - test_scores_std,
        test_scores_mean + test_scores_std,
        alpha=0.2,
        color="darkorange",
    )

    display_gap = train_scores_mean[-1] - test_scores_mean[-1]

    textstr = f"Final Gap: {display_gap:.3f}\n"
    if display_gap < 0.01:
        textstr += "Status: Well-fitted ✓"
    elif display_gap < 0.05:
        textstr += "Status: Slight overfitting"
    else:
        textstr += "Status: High variance (overfitting)"

    if not scoring.startswith("neg_"):
        if test_scores_mean[-1] - test_scores_mean[0] > 0.05:
            textstr += "\nMore data may help"
    else:
        if test_scores_mean[0] - test_scores_mean[-1] > 0.05:
            textstr += "\nMore data may help"

    ax.text(
        0.02,
        0.98,
        textstr,
        transform=ax.transAxes,
        fontsize=11,
        verticalalignment="top",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
    )

    ax.set_xlabel("Training Set Size", fontsize=12)
    ax.set_ylabel(f"{scoring.upper().replace('NEG_', '')} Score", fontsize=12)
    ax.set_title(
        f"Learning Curves - {name}\n(Best Model After Hyperparameter Tuning)",
        fontsize=14,
    )
    ax.legend(loc="best", fontsize=11)
    ax.grid(True, alpha=0.3)

    return finalize_figure(fig, show=show)


def _draw_validation_curves(
    estimator,
    X_train,
    y_train,
    *,
    param_name: str,
    param_values,
    scoring: str,
    cv,
    show: bool = True,
):
    """Plot one validation curve using only the training data and its CV."""
    train_scores, test_scores = validation_curve(
        estimator=estimator,
        X=X_train,
        y=y_train,
        param_name=param_name,
        param_range=param_values,
        cv=cv,
        scoring=scoring,
        n_jobs=1,
    )

    train_scores_mean = np.mean(train_scores, axis=1)
    test_scores_mean = np.mean(test_scores, axis=1)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(param_values, train_scores_mean, "o-", label="Train", linewidth=2)
    ax.plot(param_values, test_scores_mean, "o-", label="Validation", linewidth=2)

    best_idx = int(np.argmax(test_scores_mean))
    best_value = param_values[best_idx]
    best_score = test_scores_mean[best_idx]
    numeric_value = isinstance(best_value, (int, float, np.number))

    if numeric_value:
        ax.axvline(x=best_value, color="r", linestyle="--", alpha=0.5)
    ax.annotate(
        f"Best: {best_value}\nScore: {best_score:.3f}",
        xy=(best_value if numeric_value else best_idx, best_score),
        xytext=(10, -30),
        textcoords="offset points",
        bbox=dict(boxstyle="round,pad=0.5", fc="yellow", alpha=0.7),
        arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0"),
    )

    ax.set_title(f"Validation Curve: {estimator.__class__.__name__} | {param_name}")
    ax.set_xlabel(param_name)
    ax.set_ylabel(scoring.upper().replace("NEG_", ""))
    ax.legend()
    ax.grid(True, alpha=0.3)

    return finalize_figure(fig, show=show)


def plot_learning_curves(
    estimator,
    X_train,
    y_train,
    *,
    scoring: str,
    name: str,
    cv,
    show: bool = True,
):
    """Public learning-curve builder; returns the figure."""
    return _draw_learning_curves(
        estimator,
        X_train,
        y_train,
        scoring=scoring,
        name=name,
        cv=cv,
        show=show,
    )


def plot_validation_curves(
    estimator,
    X_train,
    y_train,
    *,
    param_name: str,
    param_values,
    scoring: str,
    cv,
    show: bool = True,
):
    """Public validation-curve builder; returns the figure."""
    return _draw_validation_curves(
        estimator,
        X_train,
        y_train,
        param_name=param_name,
        param_values=param_values,
        scoring=scoring,
        cv=cv,
        show=show,
    )


def tune_models(
    pipelines: Mapping[str, object],
    param_grid: Mapping[str, Mapping[str, Sequence]],
    X_train,
    y_train,
    X_test,
    y_test,
    *,
    task: TaskConfig,
    scoring: str | None = None,
    search_method: str = "grid",
    n_iter: int = 50,
    n_splits: int = 5,
    n_repeats: int = 3,
    random_state: int = 42,
    display: bool = True,
    plot_validation_curves: bool = False,
    plot_learning_curves: bool = True,
    progress_bar: bool = False,
    show: bool = True,
    n_jobs: int = -1,
) -> tuple[dict, list[float]]:
    """Shared grid/random-search tuning for classification and regression.

    The task config supplies the CV splitter and default scorer. Holdout
    scores are always computed through ``get_scorer`` so the public scoring
    string is honored exactly. Learning curves are generated whenever
    requested, independently of ``display``.
    """
    _configure_logging(display)
    scoring = scoring or task.default_scoring
    fitted_models: dict[str, object] = {}
    fit_times: list[float] = []

    pipe_iter = (
        tqdm(pipelines.items(), desc="Processing Pipelines", position=0, leave=True)
        if progress_bar
        else pipelines.items()
    )

    for name, pipeline in pipe_iter:
        try:
            cv = task.cv_factory(n_splits, n_repeats, random_state)

            if plot_validation_curves:
                param_iter = (
                    tqdm(
                        param_grid[name].items(),
                        desc=f"Validation Curves for {name}",
                        position=1,
                        leave=True,
                    )
                    if progress_bar
                    else param_grid[name].items()
                )
                for param_name, param_values in param_iter:
                    if not isinstance(param_values, (list, np.ndarray)):
                        continue
                    if len(param_values) < 2:
                        continue
                    _draw_validation_curves(
                        pipeline,
                        X_train,
                        y_train,
                        param_name=param_name,
                        param_values=param_values,
                        scoring=scoring,
                        cv=cv,
                        show=show,
                    )

            if search_method == "random":
                search = RandomizedSearchCV(
                    estimator=pipeline,
                    param_distributions=param_grid[name],
                    n_iter=n_iter,
                    scoring=scoring,
                    cv=cv,
                    verbose=2 if display else 0,
                    n_jobs=n_jobs,
                    random_state=random_state,
                    return_train_score=True,
                    error_score="raise",
                )
            else:
                search = GridSearchCV(
                    estimator=pipeline,
                    param_grid=param_grid[name],
                    scoring=scoring,
                    cv=cv,
                    verbose=2 if display else 0,
                    n_jobs=n_jobs,
                    return_train_score=True,
                    error_score="raise",
                )

            start_time = time.time()
            search.fit(X_train, y_train)
            fit_time = time.time() - start_time
            fit_times.append(round(fit_time, 2))

            search.test_score_ = float(
                get_scorer(scoring)(search.best_estimator_, X_test, y_test)
            )
            fitted_models[name] = search

            if display:
                logger.info("\n%s", "=" * 50)
                logger.info(
                    "Results for %s (%s Search)", name, search_method.upper()
                )
                logger.info("%s", "=" * 50)
                logger.info("Fit Time: %.2fs", fit_time)
                logger.info("Best CV %s: %.4f", scoring, search.best_score_)
                logger.info("\nBest Parameters:")
                for param, value in search.best_params_.items():
                    logger.info("  %s: %s", param, value)
                logger.info("\nTest %s: %.4f", scoring, search.test_score_)

            if plot_learning_curves:
                if display:
                    logger.info("\nGenerating learning curves for %s...", name)
                _draw_learning_curves(
                    search.best_estimator_,
                    X_train,
                    y_train,
                    scoring=scoring,
                    name=name,
                    cv=cv,
                    show=show,
                )

        except Exception as e:
            logger.exception("Error during %s pipeline tuning: %s", name, e)
            raise

    return fitted_models, fit_times
