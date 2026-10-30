
# Import metrics score that will be evaluated
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    root_mean_squared_error,
    mean_absolute_percentage_error,
    r2_score,
)
from sklearn.model_selection import cross_validate, RepeatedKFold
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.neighbors import KNeighborsRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from xgboost import XGBRegressor
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

from ._ml_common import (
    REGRESSION_TASK,
    _configure_logging,
    logger,
    tune_models,
)
from ._plotting import finalize_figure

# ╔══════════════════════════════════════════════════════════════════════════════════╗
# ║            Functions for Machine Learning Evaluation                             ║
# ╚══════════════════════════════════════════════════════════════════════════════════╝

# Function for evaluation score calculation
def eval_regression(
    model,
    X_test,
    y_test,
    X_train,
    y_train,
    custom_metrics=None,
    plot_predicted_vs_actual=True,
    plot_residuals=True,
    plot_residuals_dist=True,
    n_splits=5,
    n_repeats=3,
    random_state=42,
    show_plots=True,
    display=True
) -> dict:
    """
    Comprehensively evaluate a regression model using multiple metrics 
    and cross-validation techniques.

    This function provides a robust evaluation of a regression model by:
    1. Performing single-run predictions
    2. Conducting cross-validated performance assessment
    3. Computing multiple performance metrics (MAE, MSE, RMSE, MAPE, R2)

    Parameters:
    -----------
    model : sklearn estimator
        The regression model to be evaluated
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
    plot_predicted_vs_actual : bool, optional (default=True)
        Whether to plot predicted vs actual values scatter plot with 45° reference line.
        Shows systematic bias, outliers, and overall fit quality.
    plot_residuals : bool, optional (default=True)
        Whether to plot residuals vs predicted values. Checks for:
        - Homoscedasticity (constant variance)
        - Non-linear patterns
        - Outliers and influential points
    plot_residuals_dist : bool, optional (default=True)
        Whether to plot residuals distribution histogram with KDE and normal curve overlay.
        Checks normality assumption of residuals.
    n_splits : int, optional (default=5)
        Number of splits for cross-validation
    n_repeats : int, optional (default=3)
        Number of times to repeat cross-validation
    random_state : int, optional (default=42)
        Seed for reproducibility of cross-validation splits
    show_plots : bool, optional (default=True)
        Whether to call ``plt.show`` after building each figure. Set False to
        keep figures open without blocking (notebooks, tests, batch jobs).
    display : bool, optional (default=True)
        Whether to log the metric summary at INFO level. False suppresses the
        summary without affecting returned metrics or figures.

    Example:
    --------
    >>> metrics = eval_regression(
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

        # Initialize metrics dictionary to store all evaluation results
        metrics = {}

        # Perform single-run predictions on test and train datasets
        y_pred_test = model.predict(X_test)
        y_pred_train = model.predict(X_train)
        
        # Setup cross-validation strategy
        cv = RepeatedKFold(
            n_splits=n_splits,
            n_repeats=n_repeats,
            random_state=random_state
        )

        # Define standard metrics to evaluate
        # Note: sklearn cross_validate uses negative error scores so they can be maximized
        scoring = {
            'mae': 'neg_mean_absolute_error',
            'mse': 'neg_mean_squared_error',
            'mape': 'neg_mean_absolute_percentage_error',
            'r2': 'r2'
        }

        # Define metric functions explicitly
        metric_funcs = {
            'mae': mean_absolute_error,
            'mse': mean_squared_error,
            'mape': mean_absolute_percentage_error,
            'r2': r2_score,
        }

        # Perform cross-validation with multiple metrics
        cv_scores = cross_validate(
            model,
            X_train,
            y_train,
            cv=cv,
            scoring=scoring,
            return_train_score=True,
            n_jobs=-1  # Use all available CPU cores
        )

        # Store cross-validated metrics
        metrics['cv'] = {}

        # Process each metric from cross-validation
        for metric in scoring.keys():
            test_scores = cv_scores[f'test_{metric}']
            train_scores = cv_scores[f'train_{metric}']
            
            # Convert negative scores back to positive for error metrics
            if metric in ['mae', 'mse', 'mape']:
                test_scores = -test_scores
                train_scores = -train_scores

            # Store mean and standard deviation of cross-validated scores
            metrics['cv'][metric] = {
                'test_mean': test_scores.mean(),
                'test_std': test_scores.std(),
                'train_mean': train_scores.mean(),
                'train_std': train_scores.std()
            }
            
            # Store single-run metrics
            metrics[metric] = {
                'test': metric_funcs[metric](y_test, y_pred_test),
                'train': metric_funcs[metric](y_train, y_pred_train)
            }

        # Calculate RMSE from CV MSE scores (scikit-learn 1.4+ has native root_mean_squared_error)
        # CV RMSE
        mse_test_scores = -cv_scores['test_mse']
        mse_train_scores = -cv_scores['train_mse']
        rmse_test_scores = np.sqrt(mse_test_scores)
        rmse_train_scores = np.sqrt(mse_train_scores)
        
        metrics['cv']['rmse'] = {
            'test_mean': rmse_test_scores.mean(),
            'test_std': rmse_test_scores.std(),
            'train_mean': rmse_train_scores.mean(),
            'train_std': rmse_train_scores.std()
        }
        
        # Single run RMSE using sklearn's native implementation
        metrics['rmse'] = {
            'test': root_mean_squared_error(y_test, y_pred_test),
            'train': root_mean_squared_error(y_train, y_pred_train)
        }

        # Add custom metrics if provided
        if custom_metrics:
            for metric_name, metric_func in custom_metrics.items():
                metrics[metric_name] = {
                    'test': metric_func(y_test, y_pred_test),
                    'train': metric_func(y_train, y_pred_train)
                }

        # Log results
        logger.info("Performance Metrics for %s:", model.__class__.__name__)
        logger.info("\nCross-Validated Metrics (mean ± std):")
        # Order metrics for display
        display_metrics = ['mae', 'mse', 'rmse', 'mape', 'r2']
        for metric in display_metrics:
            logger.info("\n%s:", metric.upper())
            if metric == 'mape':
                logger.info(
                    "  Test:  %.2f%% ± %.2f%%",
                    metrics['cv'][metric]['test_mean'] * 100,
                    metrics['cv'][metric]['test_std'] * 100,
                )
                logger.info(
                    "  Train: %.2f%% ± %.2f%%",
                    metrics['cv'][metric]['train_mean'] * 100,
                    metrics['cv'][metric]['train_std'] * 100,
                )
            else:
                logger.info(
                    "  Test:  %.4f ± %.4f",
                    metrics['cv'][metric]['test_mean'],
                    metrics['cv'][metric]['test_std'],
                )
                logger.info(
                    "  Train: %.4f ± %.4f",
                    metrics['cv'][metric]['train_mean'],
                    metrics['cv'][metric]['train_std'],
                )

        logger.info("\nSingle Run Metrics:")
        for metric in display_metrics:
            logger.info("\n%s:", metric.upper())
            if metric == 'mape':
                logger.info("  Test:  %.2f%%", metrics[metric]['test'] * 100)
                logger.info("  Train: %.2f%%", metrics[metric]['train'] * 100)
            else:
                logger.info("  Test:  %.4f", metrics[metric]['test'])
                logger.info("  Train: %.4f", metrics[metric]['train'])

        # Plot 1: Predicted vs Actual
        if plot_predicted_vs_actual:
            fig, axes = plt.subplots(1, 2, figsize=(14, 6))
            
            # Training set
            ax1 = axes[0]
            ax1.scatter(y_train, y_pred_train, alpha=0.5, edgecolors='none')
            min_val = min(y_train.min(), y_pred_train.min())
            max_val = max(y_train.max(), y_pred_train.max())
            ax1.plot([min_val, max_val], [min_val, max_val], 'r--', lw=2, label='Perfect Prediction')
            ax1.set_xlabel('Actual Values')
            ax1.set_ylabel('Predicted Values')
            ax1.set_title(f'Predicted vs Actual - Training Set\n{model.__class__.__name__}')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Add R² annotation
            r2_train = metrics['r2']['train']
            ax1.text(0.05, 0.95, f'R² = {r2_train:.4f}', transform=ax1.transAxes,
                    verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
            
            # Test set
            ax2 = axes[1]
            ax2.scatter(y_test, y_pred_test, alpha=0.5, edgecolors='none')
            min_val = min(y_test.min(), y_pred_test.min())
            max_val = max(y_test.max(), y_pred_test.max())
            ax2.plot([min_val, max_val], [min_val, max_val], 'r--', lw=2, label='Perfect Prediction')
            ax2.set_xlabel('Actual Values')
            ax2.set_ylabel('Predicted Values')
            ax2.set_title(f'Predicted vs Actual - Test Set\n{model.__class__.__name__}')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            # Add R² annotation
            r2_test = metrics['r2']['test']
            ax2.text(0.05, 0.95, f'R² = {r2_test:.4f}', transform=ax2.transAxes,
                    verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
            
            finalize_figure(fig, show=show_plots)

        # Plot 2: Residuals vs Predicted
        if plot_residuals:
            fig, axes = plt.subplots(1, 2, figsize=(14, 6))
            
            # Calculate residuals
            residuals_train = y_train - y_pred_train
            residuals_test = y_test - y_pred_test
            
            # Training set
            ax1 = axes[0]
            ax1.scatter(y_pred_train, residuals_train, alpha=0.5, edgecolors='none')
            ax1.axhline(y=0, color='r', linestyle='--', lw=2)
            ax1.set_xlabel('Predicted Values')
            ax1.set_ylabel('Residuals (Actual - Predicted)')
            ax1.set_title(f'Residuals vs Predicted - Training Set\n{model.__class__.__name__}')
            ax1.grid(True, alpha=0.3)
            
            # Test set
            ax2 = axes[1]
            ax2.scatter(y_pred_test, residuals_test, alpha=0.5, edgecolors='none')
            ax2.axhline(y=0, color='r', linestyle='--', lw=2)
            ax2.set_xlabel('Predicted Values')
            ax2.set_ylabel('Residuals (Actual - Predicted)')
            ax2.set_title(f'Residuals vs Predicted - Test Set\n{model.__class__.__name__}')
            ax2.grid(True, alpha=0.3)
            
            finalize_figure(fig, show=show_plots)

        # Plot 3: Residuals Distribution
        if plot_residuals_dist:
            fig, axes = plt.subplots(1, 2, figsize=(14, 6))
            
            # Training set
            ax1 = axes[0]
            residuals_train = y_train - y_pred_train
            ax1.hist(residuals_train, bins=30, density=True, alpha=0.7, color='blue', edgecolor='black')
            
            # Add KDE
            from scipy.stats import gaussian_kde, norm
            kde = gaussian_kde(residuals_train)
            x_range = np.linspace(residuals_train.min(), residuals_train.max(), 100)
            ax1.plot(x_range, kde(x_range), 'b-', lw=2, label='KDE')
            
            # Add normal distribution overlay
            mu, sigma = norm.fit(residuals_train)
            ax1.plot(x_range, norm.pdf(x_range, mu, sigma), 'r--', lw=2, label='Normal Fit')
            
            ax1.axvline(x=0, color='green', linestyle='-', lw=2, label='Zero')
            ax1.set_xlabel('Residuals')
            ax1.set_ylabel('Density')
            ax1.set_title(f'Residuals Distribution - Training Set\n{model.__class__.__name__}')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Test set
            ax2 = axes[1]
            residuals_test = y_test - y_pred_test
            ax2.hist(residuals_test, bins=30, density=True, alpha=0.7, color='blue', edgecolor='black')
            
            # Add KDE
            kde = gaussian_kde(residuals_test)
            x_range = np.linspace(residuals_test.min(), residuals_test.max(), 100)
            ax2.plot(x_range, kde(x_range), 'b-', lw=2, label='KDE')
            
            # Add normal distribution overlay
            mu, sigma = norm.fit(residuals_test)
            ax2.plot(x_range, norm.pdf(x_range, mu, sigma), 'r--', lw=2, label='Normal Fit')
            
            ax2.axvline(x=0, color='green', linestyle='-', lw=2, label='Zero')
            ax2.set_xlabel('Residuals')
            ax2.set_ylabel('Density')
            ax2.set_title(f'Residuals Distribution - Test Set\n{model.__class__.__name__}')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            finalize_figure(fig, show=show_plots)

        return metrics

    except Exception as e:
        logger.exception("Error during evaluation: %s", e)
        raise

# Function to compare cross-validated metrics from multiple models
def compare_cv_metrics(
    metrics_dict: dict, *, as_numeric: bool = False
) -> pd.DataFrame:
    """
    Compare cross-validated metrics from multiple models in a single table.
    
    This function extracts only the cross-validation metrics (not single-run metrics)
    from multiple model evaluations and presents them in a comparison DataFrame.
    
    Parameters:
    -----------
    metrics_dict : dict
        Dictionary with model names as keys and metrics dictionaries as values.
        Format: {'model_name': metrics_dict_from_eval_regression}
    as_numeric : bool, optional (default=False)
        Return raw float means instead of the formatted strings.
        
    Returns:
    --------
    pd.DataFrame
        DataFrame with models as rows and CV metrics as columns
        
    Example:
    --------
    >>> metrics_rf = eval_regression(model=rf, X_train=X_train, y_train=y_train, 
    ...                              X_test=X_test, y_test=y_test)
    >>> metrics_xgb = eval_regression(model=xgb, X_train=X_train, y_train=y_train,
    ...                               X_test=X_test, y_test=y_test)
    >>> comparison = compare_cv_metrics({
    ...     'Random Forest': metrics_rf,
    ...     'XGBoost': metrics_xgb
    ... })
    >>> display(comparison)
    """
    # Define metrics to extract from CV results
    cv_metrics = ['mae', 'mse', 'rmse', 'mape', 'r2']
    
    # Prepare data for DataFrame
    data = []
    
    for model_name, metrics in metrics_dict.items():
        row = {'Model': model_name}
        
        # Extract CV metrics (test set only)
        for metric in cv_metrics:
            if 'cv' in metrics and metric in metrics['cv']:
                mean_val = metrics['cv'][metric]['test_mean']
                std_val = metrics['cv'][metric]['test_std']
                
                if as_numeric:
                    row[f'{metric.upper()}'] = float(mean_val)
                elif metric == 'mape':
                    row[f'{metric.upper()}'] = f"{mean_val*100:.2f}% ± {std_val*100:.2f}%"
                else:
                    row[f'{metric.upper()}'] = f"{mean_val:.4f} ± {std_val:.4f}"
            else:
                row[f'{metric.upper()}'] = np.nan if as_numeric else 'N/A'
        
        data.append(row)
    
    # Create DataFrame
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
    scoring='neg_mean_squared_error',
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
        task=REGRESSION_TASK,
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


# Define supported models for regression
SUPPORTED_MODELS = ['linearregression', 'ridge', 'lasso', 'elasticnet', 'knn', 'decisiontree', 'randomforest', 'gb', 'xgboost']

# Function for getting model pipeline
def get_model_pipeline(model_name: str, random_state: int = 42) -> Pipeline:
    """
    Create a pipeline for a specific regression model.
    
    Parameters:
    -----------
    model_name : str
        Name of the model. Supported: 'linearregression', 'ridge', 'lasso', 'elasticnet',
        'knn', 'decisiontree', 'randomforest', 'gb', 'xgboost'
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
        'linearregression': Pipeline([
            ('lr', LinearRegression())
        ]),
        'ridge': Pipeline([
            ('ridge', Ridge(random_state=random_state))
        ]),
        'lasso': Pipeline([
            ('lasso', Lasso(random_state=random_state))
        ]),
        'elasticnet': Pipeline([
            ('en', ElasticNet(random_state=random_state))
        ]),
        'knn': Pipeline([
            ('knn', KNeighborsRegressor())
        ]),
        'decisiontree': Pipeline([
            ('dt', DecisionTreeRegressor(random_state=random_state))
        ]),
        'randomforest': Pipeline([
            ('rf', RandomForestRegressor(random_state=random_state))
        ]),
        'gb': Pipeline([
            ('gb', GradientBoostingRegressor(random_state=random_state))
        ]),
        'xgboost': Pipeline([
            ('xgb', XGBRegressor(random_state=random_state))
        ])
    }
    
    model_key = model_name.lower()
    if model_key not in pipelines:
        raise ValueError(f"Model '{model_name}' not supported. Choose from: {SUPPORTED_MODELS}")
    
    return pipelines[model_key]

# Function for getting hyperparameters
def get_hyperparameters(model_name: str, search_method: str = 'grid') -> dict:
    """
    Get hyperparameter grid for a specific regression model.
    
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
        'linearregression': {
            'lr__fit_intercept': [True, False]
        },
        'ridge': {
            'ridge__alpha': [0.001, 0.01, 0.1, 1.0, 10.0, 100.0],
            'ridge__fit_intercept': [True, False],
            'ridge__solver': ['auto', 'svd', 'cholesky', 'lsqr']
        },
        'lasso': {
            'lasso__alpha': [0.001, 0.01, 0.1, 1.0, 10.0],
            'lasso__fit_intercept': [True, False],
            'lasso__max_iter': [1000, 5000]
        },
        'elasticnet': {
            'en__alpha': [0.001, 0.01, 0.1, 1.0, 10.0],
            'en__l1_ratio': [0.1, 0.3, 0.5, 0.7, 0.9],
            'en__fit_intercept': [True, False],
            'en__max_iter': [1000, 5000]
        },
        'knn': {
            'knn__n_neighbors': [3, 5, 7, 11, 15, 21],
            'knn__weights': ['uniform', 'distance'],
            'knn__p': [1, 2],
            'knn__algorithm': ['auto'],
            'knn__leaf_size': [20, 30]
        },
        'decisiontree': {
            'dt__criterion': ['squared_error', 'friedman_mse', 'absolute_error'],
            'dt__max_depth': [3, 5, 7, 10, 15, 20],
            'dt__min_samples_split': [2, 5, 10, 20],
            'dt__min_samples_leaf': [1, 2, 5, 10],
            'dt__max_features': ['sqrt', 'log2']
        },
        'randomforest': {
            'rf__n_estimators': [50, 100, 200],
            'rf__criterion': ['squared_error', 'friedman_mse'],
            'rf__max_depth': [10, 15, 20, 30],
            'rf__min_samples_split': [2, 5],
            'rf__max_features': ['sqrt', 'log2'],
            'rf__min_samples_leaf': [1, 2]
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
        'linearregression': {
            'lr__fit_intercept': [True, False]
        },
        'ridge': {
            'ridge__alpha': [float(x) for x in np.logspace(-4, 3, 50)],
            'ridge__fit_intercept': [True, False],
            'ridge__solver': ['auto', 'svd', 'cholesky', 'lsqr', 'sparse_cg', 'sag', 'saga']
        },
        'lasso': {
            'lasso__alpha': [float(x) for x in np.logspace(-4, 2, 50)],
            'lasso__fit_intercept': [True, False],
            'lasso__max_iter': [1000, 5000, 10000]
        },
        'elasticnet': {
            'en__alpha': [float(x) for x in np.logspace(-4, 2, 50)],
            'en__l1_ratio': [float(x) for x in np.linspace(0.1, 0.9, 9)],
            'en__fit_intercept': [True, False],
            'en__max_iter': [1000, 5000, 10000]
        },
        'knn': {
            'knn__n_neighbors': list(range(1, 31)),
            'knn__weights': ['uniform', 'distance'],
            'knn__p': [1, 2],
            'knn__algorithm': ['auto', 'ball_tree', 'kd_tree', 'brute'],
            'knn__leaf_size': list(range(10, 50, 5))
        },
        'decisiontree': {
            'dt__criterion': ['squared_error', 'friedman_mse', 'absolute_error'],
            'dt__max_depth': list(range(1, 25)),
            'dt__min_samples_split': list(range(2, 50)),
            'dt__min_samples_leaf': list(range(1, 30)),
            'dt__max_features': ['sqrt', 'log2']
        },
        'randomforest': {
            'rf__n_estimators': [25, 50, 75, 100, 150, 200, 300],
            'rf__criterion': ['squared_error', 'friedman_mse', 'absolute_error'],
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
    scoring='neg_mean_squared_error',
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
    Tune a single regression model using grid or random search.
    
    Parameters:
    -----------
    model_name : str
        Name of the model to tune. Supported: 'linearregression', 'ridge', 'lasso',
        'elasticnet', 'knn', 'decisiontree', 'randomforest', 'gb', 'xgboost'
    X_train, y_train : array-like
        Training data
    X_test, y_test : array-like
        Test data
    scoring : str, optional (default='neg_mean_squared_error')
        Metric to optimize. Common options:
        - 'neg_mean_squared_error' (MSE, negated for maximization)
        - 'neg_mean_absolute_error' (MAE, negated for maximization)
        - 'r2' (R-squared, higher is better)
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
    scoring='neg_mean_squared_error',
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
    Tune multiple regression models using grid or random search.
    
    Parameters:
    -----------
    X_train, y_train : array-like
        Training data
    X_test, y_test : array-like
        Test data
    models : list, optional (default=None)
        List of model names to tune. If None, tunes all supported models:
        ['linearregression', 'ridge', 'lasso', 'elasticnet', 'knn', 
         'decisiontree', 'randomforest', 'gb', 'xgboost']
    scoring : str, optional (default='neg_mean_squared_error')
        Metric to optimize. Common options:
        - 'neg_mean_squared_error' (MSE, negated for maximization)
        - 'neg_mean_absolute_error' (MAE, negated for maximization)
        - 'r2' (R-squared, higher is better)
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
