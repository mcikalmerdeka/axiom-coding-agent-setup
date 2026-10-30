# Import metrics score that will be evaluated
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    roc_curve,
    average_precision_score,
    precision_recall_curve,
    confusion_matrix
)
from sklearn.calibration import calibration_curve
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from xgboost import XGBClassifier
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

from ._ml_common import (
    CLASSIFICATION_TASK,
    _configure_logging,
    aggregate_fold_metrics,
    collect_fold_results,
    logger,
    tune_models,
)
from ._plotting import finalize_figure

# ╔══════════════════════════════════════════════════════════════════════════════════╗
# ║            Functions for Machine Learning Evaluation                             ║
# ╚══════════════════════════════════════════════════════════════════════════════════╝

# Function for evaluation score calculation and display confusion matrix
def eval_classification(
    model,
    X_test,
    y_test,
    X_train,
    y_train,
    custom_metrics=None,
    plot_confusion_matrix=True,
    plot_roc_curve=True,
    plot_pr_curve=True,
    plot_calibration_curve=True,
    plot_threshold_analysis=True,
    validate_confusion_matrix=False,
    n_splits=5,
    n_repeats=3,
    random_state=42,
    show_plots=True,
    return_figures=False,
    display=True,
) -> dict:
    """
    Comprehensively evaluate a classification model using multiple metrics
    and cross-validation techniques.

    This function provides a robust evaluation of a classification model by:
    1. Performing single-run predictions
    2. Conducting cross-validated performance assessment
    3. Computing multiple performance metrics
    4. Optionally visualizing the cross-validated diagnostics

    All cross-validated diagnostics reuse one set of fold predictions, so the
    model is fitted exactly once per fold.

    Parameters:
    -----------
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

    Example:
    --------
    >>> metrics = eval_classification(
    >>>     model=model,
    >>>     X_test=X_test,
    >>>     y_test=y_test,
    >>>     X_train=X_train,
    >>>     y_train=y_train
    >>> )
    >>> print(metrics)

    Returns:
    --------
    dict
        Comprehensive dictionary of model performance metrics including:
        - Cross-validated metrics
        - Single-run metrics
        - Cross-validated confusion matrix

    Raises:
    -------
    Exception
        If any error occurs during model evaluation
    """
    _configure_logging(display)
    try:
        # Utility function to convert input to numpy array
        def to_numpy(arr):
            """
            Convert pandas DataFrame/Series to numpy array if necessary.

            Parameters:
            -----------
            arr : array-like
                Input array to be converted

            Returns:
            --------
            numpy.ndarray
                Converted numpy array
            """
            if isinstance(arr, (pd.DataFrame, pd.Series)):
                return arr.to_numpy()
            return arr

        # Convert all input data to numpy arrays
        X_test = to_numpy(X_test)
        y_test = to_numpy(y_test)
        X_train = to_numpy(X_train)
        y_train = to_numpy(y_train)

        if not hasattr(model, "predict_proba"):
            raise ValueError(
                "eval_classification requires a model with predict_proba "
                "(needed for ROC AUC and probability-based diagnostics)."
            )

        classes = np.unique(np.concatenate([np.asarray(y_train), np.asarray(y_test)]))
        if len(classes) > 2:
            raise ValueError(
                "eval_classification currently supports binary classification "
                f"only; found {len(classes)} classes."
            )

        # Initialize metrics dictionary to store all evaluation results
        metrics = {}

        # Perform single-run predictions on test and train datasets
        y_pred_test = model.predict(X_test)
        y_pred_train = model.predict(X_train)

        # Get probability predictions for metrics like ROC AUC
        y_pred_proba_test = model.predict_proba(X_test)
        y_pred_proba_train = model.predict_proba(X_train)

        # Setup cross-validation strategy
        cv = RepeatedStratifiedKFold(
            n_splits=n_splits,
            n_repeats=n_repeats,
            random_state=random_state,
        )

        # One fit per fold, reused by every metric and diagnostic plot.
        fold_results = collect_fold_results(model, X_train, y_train, cv)

        if validate_confusion_matrix:
            # Average confusion matrix across the cached fold predictions.
            conf_matrix_list = [
                confusion_matrix(result.y_true, result.y_pred)
                for result in fold_results
            ]
            mean_conf_matrix = np.rint(np.mean(conf_matrix_list, axis=0)).astype(int)
            metrics["cv_confusion_matrix"] = mean_conf_matrix
        else:
            normal_conf_matrix = confusion_matrix(y_test, y_pred_test)
            metrics["confusion_matrix"] = normal_conf_matrix

        # Define standard metric functions explicitly (avoid fragile globals lookup)
        metric_funcs = {
            "accuracy": accuracy_score,
            "precision": lambda y_true, y_pred: precision_score(
                y_true, y_pred, zero_division=0
            ),
            "recall": lambda y_true, y_pred: recall_score(
                y_true, y_pred, zero_division=0
            ),
            "f1": lambda y_true, y_pred: f1_score(
                y_true, y_pred, zero_division=0
            ),
        }

        # Store cross-validated metrics from the same fold results.
        metrics["cv"] = aggregate_fold_metrics(
            fold_results,
            metric_funcs,
            probability_metrics={"roc_auc": roc_auc_score},
        )

        # Store single-run metrics from the supplied fitted model.
        for metric, metric_func in metric_funcs.items():
            metrics[metric] = {
                "test": metric_func(y_test, y_pred_test),
                "train": metric_func(y_train, y_pred_train),
            }
        metrics["roc_auc"] = {
            "test": roc_auc_score(y_test, y_pred_proba_test[:, 1]),
            "train": roc_auc_score(y_train, y_pred_proba_train[:, 1]),
        }

        # Add custom metrics if provided
        if custom_metrics:
            for metric_name, metric_func in custom_metrics.items():
                metrics[metric_name] = {
                    "test": metric_func(y_test, y_pred_test),
                    "train": metric_func(y_train, y_pred_train),
                }

        # Log results
        logger.info("Performance Metrics for %s:", model.__class__.__name__)
        logger.info("\nCross-Validated Metrics (mean ± std):")
        for metric in metrics["cv"]:
            logger.info("\n%s:", metric.upper())
            logger.info(
                "  Test:  %.2f ± %.2f",
                metrics["cv"][metric]["test_mean"] * 100,
                metrics["cv"][metric]["test_std"] * 100,
            )
            logger.info(
                "  Train: %.2f ± %.2f",
                metrics["cv"][metric]["train_mean"] * 100,
                metrics["cv"][metric]["train_std"] * 100,
            )

        logger.info("\nSingle Run Metrics:")
        for metric in [*metric_funcs, "roc_auc"]:
            logger.info("\n%s:", metric.upper())
            logger.info("  Test:  %.2f", metrics[metric]["test"] * 100)
            logger.info("  Train: %.2f", metrics[metric]["train"] * 100)

        figures = {}

        # Plot confusion matrix if requested
        if plot_confusion_matrix:
            if validate_confusion_matrix:
                conf_matrix_values = mean_conf_matrix
                title_prefix = "Cross-Validation"
            else:
                conf_matrix_values = normal_conf_matrix
                title_prefix = "Test Set"

            fig, ax = plt.subplots(figsize=(8, 6))

            # Create annotation labels with TN/FN/FP/TP
            labels = np.array([
                [f"TN\n{conf_matrix_values[0, 0]}", f"FP\n{conf_matrix_values[0, 1]}"],
                [f"FN\n{conf_matrix_values[1, 0]}", f"TP\n{conf_matrix_values[1, 1]}"],
            ])

            sns.heatmap(
                conf_matrix_values,
                ax=ax,
                annot=labels,
                fmt="",
                cmap="Blues",
                xticklabels=["False (0)", "True (1)"],
                yticklabels=["False (0)", "True (1)"],
                annot_kws={"fontsize": 12, "fontweight": "bold"},
            )

            ax.set_xlabel("Predicted Label")
            ax.set_ylabel("Actual Label")
            ax.set_title(
                f"{title_prefix} Confusion Matrix - {model.__class__.__name__}"
            )
            finalize_figure(fig, show=show_plots)
            if return_figures:
                figures["confusion_matrix"] = fig

        # Plot ROC curve if requested (using cached cross-validated predictions)
        if plot_roc_curve:
            fig = _plot_roc_curve(
                fold_results,
                model_name=model.__class__.__name__,
                n_splits=n_splits,
                n_repeats=n_repeats,
                show=show_plots,
            )
            if return_figures and fig is not None:
                figures["roc_curve"] = fig

        # Plot Precision-Recall Curve if requested
        if plot_pr_curve:
            fig = _plot_pr_curve(
                fold_results,
                model_name=model.__class__.__name__,
                n_splits=n_splits,
                n_repeats=n_repeats,
                show=show_plots,
            )
            if return_figures and fig is not None:
                figures["pr_curve"] = fig

        # Plot Calibration Curve if requested
        if plot_calibration_curve:
            fig = _plot_calibration_curve(
                fold_results,
                model_name=model.__class__.__name__,
                n_splits=n_splits,
                n_repeats=n_repeats,
                show=show_plots,
            )
            if return_figures and fig is not None:
                figures["calibration_curve"] = fig

        # Plot Decision Threshold Analysis if requested
        if plot_threshold_analysis:
            fig = _plot_threshold_analysis(
                fold_results,
                model_name=model.__class__.__name__,
                n_splits=n_splits,
                n_repeats=n_repeats,
                show=show_plots,
            )
            if return_figures and fig is not None:
                figures["threshold_analysis"] = fig

        if return_figures:
            metrics["figures"] = figures

        return metrics

    except Exception as e:
        logger.exception("Error during evaluation: %s", e)
        raise


def _plot_roc_curve(
    fold_results,
    *,
    model_name: str,
    n_splits: int,
    n_repeats: int,
    show: bool = True,
):
    """Build a cross-validated ROC curve from cached fold predictions."""
    from sklearn.metrics import auc

    tpr_list = []
    auc_list = []
    mean_fpr = np.linspace(0, 1, 100)

    for result in fold_results:
        y_proba = result.y_proba[:, 1]
        fpr, tpr, _ = roc_curve(result.y_true, y_proba)
        roc_auc = auc(fpr, tpr)

        interp_tpr = np.interp(mean_fpr, fpr, tpr)
        interp_tpr[0] = 0.0
        tpr_list.append(interp_tpr)
        auc_list.append(roc_auc)

    mean_tpr = np.mean(tpr_list, axis=0)
    mean_tpr[-1] = 1.0
    mean_auc = np.mean(auc_list)
    std_auc = np.std(auc_list)
    std_tpr = np.std(tpr_list, axis=0)
    tpr_upper = np.minimum(mean_tpr + std_tpr, 1)
    tpr_lower = np.maximum(mean_tpr - std_tpr, 0)

    fig, ax = plt.subplots(figsize=(10, 8))
    ax.plot(
        mean_fpr,
        mean_tpr,
        color="darkorange",
        linewidth=2.5,
        label=f"Mean ROC (CV AUC = {mean_auc:.3f} ± {std_auc:.3f})",
        zorder=3,
    )
    ax.fill_between(
        mean_fpr,
        tpr_lower,
        tpr_upper,
        color="darkorange",
        alpha=0.2,
        label="±1 std. dev.",
    )
    ax.plot(
        [0, 1],
        [0, 1],
        linestyle="--",
        color="gray",
        alpha=0.8,
        label="Chance level (AUC = 0.500)",
    )
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel("False Positive Rate (1 - Specificity)", fontsize=12)
    ax.set_ylabel("True Positive Rate (Sensitivity)", fontsize=12)
    ax.set_title(
        f"Cross-Validated ROC Curve - {model_name}\n"
        f"({n_splits}-fold × {n_repeats} repeats)",
        fontsize=14,
    )
    ax.legend(loc="lower right", fontsize=10)
    ax.grid(True, alpha=0.3)
    return finalize_figure(fig, show=show)


def _plot_pr_curve(
    fold_results,
    *,
    model_name: str,
    n_splits: int,
    n_repeats: int,
    show: bool = True,
):
    """Build a cross-validated precision-recall curve from cached predictions."""
    precision_list = []
    ap_list = []
    mean_recall = np.linspace(0, 1, 100)

    for result in fold_results:
        y_proba = result.y_proba[:, 1]
        precision, recall, _ = precision_recall_curve(result.y_true, y_proba)
        avg_precision = average_precision_score(result.y_true, y_proba)

        interp_precision = np.interp(mean_recall, recall[::-1], precision[::-1])
        interp_precision[0] = 1.0
        precision_list.append(interp_precision)
        ap_list.append(avg_precision)

    mean_precision = np.mean(precision_list, axis=0)
    mean_precision[-1] = 0.0
    mean_ap = np.mean(ap_list)
    std_ap = np.std(ap_list)
    std_precision = np.std(precision_list, axis=0)
    precision_upper = np.minimum(mean_precision + std_precision, 1)
    precision_lower = np.maximum(mean_precision - std_precision, 0)

    baseline = np.mean(np.concatenate([result.y_true for result in fold_results]))

    fig, ax = plt.subplots(figsize=(10, 8))
    ax.plot(
        mean_recall,
        mean_precision,
        color="darkblue",
        linewidth=2.5,
        label=f"Mean PR (CV AP = {mean_ap:.3f} ± {std_ap:.3f})",
        zorder=3,
    )
    ax.fill_between(
        mean_recall,
        precision_lower,
        precision_upper,
        color="darkblue",
        alpha=0.2,
        label="±1 std. dev.",
    )
    ax.axhline(
        y=baseline,
        linestyle="--",
        color="gray",
        alpha=0.8,
        label=f"Baseline (AP = {baseline:.3f})",
    )
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel("Recall (Sensitivity)", fontsize=12)
    ax.set_ylabel("Precision (PPV)", fontsize=12)
    ax.set_title(
        f"Cross-Validated Precision-Recall Curve - {model_name}\n"
        f"({n_splits}-fold × {n_repeats} repeats)",
        fontsize=14,
    )
    ax.legend(loc="lower left", fontsize=10)
    ax.grid(True, alpha=0.3)
    return finalize_figure(fig, show=show)


def _plot_calibration_curve(
    fold_results,
    *,
    model_name: str,
    n_splits: int,
    n_repeats: int,
    show: bool = True,
):
    """Build a cross-validated calibration curve from cached probabilities."""
    from scipy import interpolate

    prob_true_interp_list = []
    common_prob_bins = np.linspace(0, 1, 11)

    for result in fold_results:
        y_proba = result.y_proba[:, 1]
        prob_true, prob_pred = calibration_curve(
            result.y_true, y_proba, n_bins=10, strategy="uniform"
        )
        if len(prob_pred) >= 2:
            interp_func = interpolate.interp1d(
                prob_pred,
                prob_true,
                kind="linear",
                bounds_error=False,
                fill_value=(prob_true[0], prob_true[-1]),
            )
            prob_true_interp_list.append(interp_func(common_prob_bins))

    if not prob_true_interp_list:
        return None

    prob_true_array = np.array(prob_true_interp_list)
    mean_prob_true = np.mean(prob_true_array, axis=0)
    std_prob_true = np.std(prob_true_array, axis=0)

    fig, ax = plt.subplots(figsize=(10, 8))
    ax.plot([0, 1], [0, 1], "k--", label="Perfectly Calibrated", linewidth=2)
    ax.errorbar(
        common_prob_bins,
        mean_prob_true,
        yerr=std_prob_true,
        fmt="o-",
        color="darkgreen",
        linewidth=2,
        markersize=8,
        capsize=5,
        label="Mean Calibration (±1 std)",
        ecolor="lightgreen",
        alpha=0.8,
    )
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.0])
    ax.set_xlabel("Mean Predicted Probability", fontsize=12)
    ax.set_ylabel("Fraction of Positives (Actual)", fontsize=12)
    ax.set_title(
        f"Cross-Validated Calibration Curve (Reliability Diagram) - {model_name}\n"
        f"({n_splits}-fold × {n_repeats} repeats)",
        fontsize=14,
    )
    ax.legend(loc="upper left", fontsize=10)
    ax.grid(True, alpha=0.3)
    return finalize_figure(fig, show=show)


def _plot_threshold_analysis(
    fold_results,
    *,
    model_name: str,
    n_splits: int,
    n_repeats: int,
    show: bool = True,
):
    """Build threshold curves from cached fold probabilities (no refits)."""
    thresholds = np.linspace(0, 1, 101)
    precision_cv = []
    recall_cv = []
    f1_cv = []

    for threshold in thresholds:
        precision_fold = []
        recall_fold = []
        f1_fold = []

        for result in fold_results:
            y_proba = result.y_proba[:, 1]
            y_true = result.y_true
            y_pred_thresh = (y_proba >= threshold).astype(int)

            if np.sum(y_pred_thresh) == 0:
                precision = 0
            else:
                precision = precision_score(
                    y_true, y_pred_thresh, zero_division=0
                )

            recall = recall_score(y_true, y_pred_thresh, zero_division=0)

            if precision + recall == 0:
                f1 = 0
            else:
                f1 = 2 * (precision * recall) / (precision + recall)

            precision_fold.append(precision)
            recall_fold.append(recall)
            f1_fold.append(f1)

        precision_cv.append(np.mean(precision_fold))
        recall_cv.append(np.mean(recall_fold))
        f1_cv.append(np.mean(f1_fold))

    precision_cv = np.array(precision_cv)
    recall_cv = np.array(recall_cv)
    f1_cv = np.array(f1_cv)

    best_f1_idx = np.argmax(f1_cv)
    best_f1_threshold = thresholds[best_f1_idx]
    best_f1_score = f1_cv[best_f1_idx]

    fig, ax = plt.subplots(figsize=(12, 8))
    ax.plot(
        thresholds, precision_cv, "b-", linewidth=2.5, label="Precision", alpha=0.8
    )
    ax.plot(thresholds, recall_cv, "g-", linewidth=2.5, label="Recall", alpha=0.8)
    ax.plot(thresholds, f1_cv, "r-", linewidth=2.5, label="F1-Score", alpha=0.8)
    ax.axvline(
        x=best_f1_threshold,
        color="purple",
        linestyle="--",
        linewidth=2,
        label=f"Optimal F1 = {best_f1_score:.3f} @ threshold = {best_f1_threshold:.2f}",
    )
    ax.scatter([best_f1_threshold], [best_f1_score], color="purple", s=150, zorder=5)
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel("Classification Threshold", fontsize=12)
    ax.set_ylabel("Score", fontsize=12)
    ax.set_title(
        f"Decision Threshold Analysis - {model_name}\n"
        f"({n_splits}-fold × {n_repeats} repeats)",
        fontsize=14,
    )
    ax.legend(loc="best", fontsize=10)
    ax.grid(True, alpha=0.3)
    return finalize_figure(fig, show=show)


def compare_cv_metrics(
    metrics_dict: dict, *, as_numeric: bool = False
) -> pd.DataFrame:
    """
    Compare cross-validated metrics from multiple classification models in a single table.
    
    This function extracts only the cross-validation metrics (not single-run metrics)
    from multiple model evaluations and presents them in a comparison DataFrame.
    
    Parameters:
    -----------
    metrics_dict : dict
        Dictionary with model names as keys and metrics dictionaries as values.
        Format: {'model_name': metrics_dict_from_eval_classification}
    as_numeric : bool, optional (default=False)
        Return raw float means instead of the formatted percentage strings.
        
    Returns:
    --------
    pd.DataFrame
        DataFrame with models as rows and CV metrics as columns
        
    Example:
    --------
    >>> metrics_rf = eval_classification(model=rf, X_train=X_train, y_train=y_train, 
    ...                                  X_test=X_test, y_test=y_test)
    >>> metrics_xgb = eval_classification(model=xgb, X_train=X_train, y_train=y_train,
    ...                                   X_test=X_test, y_test=y_test)
    >>> comparison = compare_cv_metrics({
    ...     'Random Forest': metrics_rf,
    ...     'XGBoost': metrics_xgb
    ... })
    >>> display(comparison)
    """
    cv_metrics = ['accuracy', 'precision', 'recall', 'f1', 'roc_auc']
    
    data = []
    
    for model_name, metrics in metrics_dict.items():
        row = {'Model': model_name}
        
        for metric in cv_metrics:
            if 'cv' in metrics and metric in metrics['cv']:
                mean_val = metrics['cv'][metric]['test_mean']
                std_val = metrics['cv'][metric]['test_std']
                if as_numeric:
                    row[f'{metric.upper()}'] = float(mean_val)
                else:
                    row[f'{metric.upper()}'] = (
                        f"{mean_val*100:.2f}% ± {std_val*100:.2f}%"
                    )
            else:
                row[f'{metric.upper()}'] = np.nan if as_numeric else 'N/A'
        
        data.append(row)
    
    df = pd.DataFrame(data)
    
    return df

# ╔══════════════════════════════════════════════════════════════════════════════════╗
# ║            Functions for Hyperparameter Tuning                                   ║
# ╚══════════════════════════════════════════════════════════════════════════════════╝

# Function for tuning multiple pipelines
def tune_pipelines(
    pipedict: dict,
    param_grid: dict,
    X_train,
    y_train,
    X_test,
    y_test,
    scoring='accuracy',
    search_method='grid',
    n_iter=50,
    n_splits=5,
    n_repeats=3,
    random_state=42,
    display=True,
    n_jobs=-1,
    plot_validation_curves=False,
    plot_learning_curves=True,
    progress_bar=False,
    show=True
) -> tuple:
    """
    Perform hyperparameter tuning with grid/random search and optional curves.

    This adapter delegates to the shared ML tuning layer. See
    ``utils._ml_common.tune_models`` for the full parameter documentation.

    Returns:
    --------
    tuple
        (dictionary of fitted search objects, list of fitting times)
    """
    return tune_models(
        pipedict,
        param_grid,
        X_train,
        y_train,
        X_test,
        y_test,
        task=CLASSIFICATION_TASK,
        scoring=scoring,
        search_method=search_method,
        n_iter=n_iter,
        n_splits=n_splits,
        n_repeats=n_repeats,
        random_state=random_state,
        display=display,
        n_jobs=n_jobs,
        plot_validation_curves=plot_validation_curves,
        plot_learning_curves=plot_learning_curves,
        progress_bar=progress_bar,
        show=show,
    )


# Define supported models
SUPPORTED_MODELS = ['logisticregression', 'knn', 'decisiontree', 'randomforest', 'gb', 'xgboost']

# Function for getting model pipeline
def get_model_pipeline(model_name: str, random_state: int = 42) -> Pipeline:
    """
    Create a pipeline for a specific model.
    
    Parameters:
    -----------
    model_name : str
        Name of the model. Supported: 'logisticregression', 'knn', 'decisiontree',
        'randomforest', 'gb', 'xgboost'
    random_state : int, optional (default=42)
        Random seed for reproducibility
        
    Returns:
    --------
    Pipeline
        Scikit-learn pipeline with the specified model
        
    Raises:
    -------
    ValueError
        If model_name is not supported
    """
    pipelines = {
        'logisticregression': Pipeline([
            ('lr', LogisticRegression(random_state=random_state))
        ]),
        'knn': Pipeline([
            ('knn', KNeighborsClassifier())
        ]),
        'decisiontree': Pipeline([
            ('dt', DecisionTreeClassifier(random_state=random_state))
        ]),
        'randomforest': Pipeline([
            ('rf', RandomForestClassifier(random_state=random_state))
        ]),
        'gb': Pipeline([
            ('gb', GradientBoostingClassifier(random_state=random_state))
        ]),
        'xgboost': Pipeline([
            ('xgb', XGBClassifier(random_state=random_state))
        ])
    }
    
    model_key = model_name.lower()
    if model_key not in pipelines:
        raise ValueError(f"Model '{model_name}' not supported. Choose from: {SUPPORTED_MODELS}")
    
    return pipelines[model_key]

# Function for getting hyperparameters
def get_hyperparameters(model_name: str, search_method: str = 'grid') -> dict:
    """
    Get hyperparameter grid for a specific model.
    
    Parameters:
    -----------
    model_name : str
        Name of the model to get hyperparameters for
    search_method : str, optional (default='grid')
        'grid' returns smaller grids suitable for exhaustive search,
        'random' returns larger distributions for random sampling
        
    Returns:
    --------
    dict
        Dictionary of hyperparameters for search
        
    Raises:
    -------
    ValueError
        If model_name is not supported
    """
    # Smaller grids for GridSearchCV (exhaustive)
    grid_params = {
        'logisticregression': {
            'lr__C': [0.001, 0.01, 0.1, 0.5, 1.0],
            'lr__penalty': ['l2'],
            'lr__solver': ['lbfgs', 'liblinear'],
            'lr__max_iter': [1000, 5000]
        },
        'knn': {
            'knn__n_neighbors': [3, 5, 7, 11, 15, 21],
            'knn__weights': ['uniform', 'distance'],
            'knn__p': [1, 2],
            'knn__algorithm': ['auto'],
            'knn__leaf_size': [20, 30]
        },
        'decisiontree': {
            'dt__criterion': ['entropy', 'gini'],
            'dt__max_depth': [3, 5, 7, 10, 15, 20],
            'dt__min_samples_split': [2, 5, 10, 20],
            'dt__min_samples_leaf': [1, 2, 5, 10],
            'dt__max_features': ['sqrt']
        },
        'randomforest': {
            'rf__n_estimators': [50, 100, 200],
            'rf__criterion': ['entropy', 'gini'],
            'rf__max_depth': [5, 10, 15, 20],
            'rf__min_samples_split': [2, 5, 10],
            'rf__max_features': ['sqrt', 'log2'],
            'rf__min_samples_leaf': [1, 2, 4]
        },
        'gb': {
            'gb__n_estimators': [50, 100, 200],
            'gb__max_depth': [3, 5, 7],
            'gb__min_samples_split': [2, 5],
            'gb__min_samples_leaf': [1, 2],
            'gb__learning_rate': [0.01, 0.1, 0.2]
        },
        'xgboost': {
            'xgb__learning_rate': [0.01, 0.1, 0.2],
            'xgb__n_estimators': [50, 100, 200],
            'xgb__max_depth': [3, 5, 7, 10],
            'xgb__tree_method': ['hist']
        }
    }
    
    # Larger distributions for RandomizedSearchCV
    random_params = {
        'logisticregression': {
            'lr__C': [float(x) for x in np.logspace(-3, 1, 50)],
            'lr__penalty': ['l2'],
            'lr__solver': ['newton-cg', 'lbfgs', 'newton-cholesky', 'liblinear'],
            'lr__max_iter': [1000, 5000, 10000]
        },
        'knn': {
            'knn__n_neighbors': list(range(1, 31)),
            'knn__weights': ['uniform', 'distance'],
            'knn__p': [1, 2],
            'knn__algorithm': ['auto', 'ball_tree', 'kd_tree', 'brute'],
            'knn__leaf_size': list(range(10, 50, 5))
        },
        'decisiontree': {
            'dt__criterion': ['entropy', 'gini'],
            'dt__max_depth': list(range(1, 25)),
            'dt__min_samples_split': list(range(2, 50)),
            'dt__min_samples_leaf': list(range(1, 30)),
            'dt__max_features': ['sqrt', 'log2', None]
        },
        'randomforest': {
            'rf__n_estimators': [25, 50, 75, 100, 150, 200, 300],
            'rf__criterion': ['entropy', 'gini'],
            'rf__max_depth': list(range(3, 25)),
            'rf__min_samples_split': [2, 5, 7, 10, 15],
            'rf__max_features': ['sqrt', 'log2'],
            'rf__min_samples_leaf': [1, 2, 4, 6, 8]
        },
        'gb': {
            'gb__n_estimators': [25, 50, 100, 150, 200, 300],
            'gb__max_depth': list(range(1, 15)),
            'gb__min_samples_split': [2, 3, 5, 7, 10],
            'gb__min_samples_leaf': [1, 2, 3, 5, 7],
            'gb__learning_rate': [0.001, 0.01, 0.05, 0.1, 0.2, 0.3]
        },
        'xgboost': {
            'xgb__learning_rate': [float(x) for x in np.linspace(0.01, 0.3, 20)],
            'xgb__n_estimators': [25, 50, 75, 100, 150, 200],
            'xgb__max_depth': list(range(3, 15)),
            'xgb__subsample': [0.6, 0.7, 0.8, 0.9, 1.0],
            'xgb__colsample_bytree': [0.6, 0.7, 0.8, 0.9, 1.0],
            'xgb__tree_method': ['hist']
        }
    }
    
    model_key = model_name.lower()
    params = random_params if search_method == 'random' else grid_params
    
    if model_key not in params:
        raise ValueError(f"Model '{model_name}' not supported. Choose from: {SUPPORTED_MODELS}")
    
    return params[model_key]

# Function for tuning a single model
def tune_single_model(
    model_name: str,
    X_train,
    y_train,
    X_test,
    y_test,
    scoring='accuracy',
    search_method='grid',
    n_iter=50,
    n_splits=5,
    n_repeats=3,
    random_state=42,
    display=True,
    plot_validation_curves=False,
    plot_learning_curves=True,
    progress_bar=False,
    show=True
) -> tuple:
    """
    Tune a single model using grid or random search.
    
    Parameters:
    -----------
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
        
    Returns:
    --------
    tuple
        (fitted search object, fitting time in seconds)
        
    Example:
    --------
    >>> model, time = tune_single_model(
    >>>     'randomforest', X_train, y_train, X_test, y_test,
    >>>     search_method='random', n_iter=30
    >>> )
    >>> print(model.best_params_)
    """
    # Get pipeline and hyperparameters for the specified model
    pipeline = get_model_pipeline(model_name, random_state=random_state)
    params = get_hyperparameters(model_name, search_method=search_method)
    
    # Create single-model dictionary
    pipedict = {model_name: pipeline}
    param_grid = {model_name: params}
    
    # Run search
    fitted_models, fit_times = tune_pipelines(
        pipedict=pipedict,
        param_grid=param_grid,
        X_train=X_train,
        y_train=y_train,
        X_test=X_test,
        y_test=y_test,
        scoring=scoring,
        search_method=search_method,
        n_iter=n_iter,
        n_splits=n_splits,
        n_repeats=n_repeats,
        random_state=random_state,
        display=display,
        plot_validation_curves=plot_validation_curves,
        plot_learning_curves=plot_learning_curves,
        progress_bar=progress_bar,
        show=show
    )
    
    return fitted_models[model_name], fit_times[0]

# Function for tuning all models
def tune_all_models(
    X_train,
    y_train,
    X_test,
    y_test,
    models: list = None,
    scoring='accuracy',
    search_method='grid',
    n_iter=50,
    n_splits=5,
    n_repeats=3,
    random_state=42,
    display=True,
    plot_learning_curves=True,
    progress_bar=True,
    show=True
) -> tuple:
    """
    Tune multiple classification models using grid or random search.
    
    Parameters:
    -----------
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
        
    Returns:
    --------
    tuple
        (dictionary of fitted search objects, list of fitting times)
        
    Example:
    --------
    >>> # Tune only specific models
    >>> fitted, times = tune_all_models(
    >>>     X_train, y_train, X_test, y_test,
    >>>     models=['randomforest', 'xgboost'],
    >>>     search_method='random', n_iter=30
    >>> )
    """
    if models is None:
        models = SUPPORTED_MODELS

    # Build pipelines and params for selected models
    all_pipelines = {
        name: get_model_pipeline(name, random_state=random_state)
        for name in models
    }
    all_hyperparameters = {
        name: get_hyperparameters(name, search_method=search_method)
        for name in models
    }

    # Run search
    fitted_models, times = tune_pipelines(
        pipedict=all_pipelines,
        param_grid=all_hyperparameters,
        X_train=X_train,
        y_train=y_train,
        X_test=X_test,
        y_test=y_test,
        scoring=scoring,
        search_method=search_method,
        n_iter=n_iter,
        n_splits=n_splits,
        n_repeats=n_repeats,
        random_state=random_state,
        display=display,
        plot_learning_curves=plot_learning_curves,
        progress_bar=progress_bar,
        show=show
    )

    return fitted_models, times