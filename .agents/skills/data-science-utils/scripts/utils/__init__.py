# Core preprocessing functions (always available)
from .preprocessing import (
    check_data_information,
    drop_columns,
    change_binary_dtype,
    handle_missing_values,
    filter_outliers,
    feature_scaling,
    feature_encoding
)

# Feature selection functions (always available)
from .feature_selection import (
    calculate_correlation_tabular,
    analyze_categorical_relationships,
    calculate_vif,
    calculate_feature_importance
)
# Statistics functions (always available)
from .statistics import (
    describe_numerical_combined,
    describe_categorical_combined,
    describe_date_columns,
    identify_distribution_types
)

# Visualization functions (always available)
from .visualization import (
    plot_dynamic_hisplots_kdeplots,
    plot_dynamic_boxplots_violinplots,
    plot_dynamic_countplot,
    plot_dynamic_stripplot_swarmplot,
    plot_correlation_heatmap
)

# ML regression functions
from .regression_evals_and_tuning import (
    eval_regression,
    compare_cv_metrics as compare_cv_metrics_regression,
    tune_pipelines as tune_pipelines_regression,
    tune_single_model as tune_single_model_regression,
    tune_all_models as tune_all_models_regression,
    get_model_pipeline as get_model_pipeline_regression,
    get_hyperparameters as get_hyperparameters_regression
)

# Backwards-compatible unsuffixed aliases used by the README and notebooks.
compare_cv_metrics = compare_cv_metrics_regression
tune_pipelines = tune_pipelines_regression
tune_single_model = tune_single_model_regression
tune_all_models = tune_all_models_regression
get_model_pipeline = get_model_pipeline_regression
get_hyperparameters = get_hyperparameters_regression

# ML classification functions
from .classification_evals_and_tuning import (
    eval_classification,
    compare_cv_metrics as compare_cv_metrics_classification,
    tune_pipelines as tune_pipelines_classification,
    tune_single_model as tune_single_model_classification,
    tune_all_models as tune_all_models_classification,
    get_model_pipeline as get_model_pipeline_classification,
    get_hyperparameters as get_hyperparameters_classification
)

# A/B Testing functions
from .ab_testing import (
    calculate_sample_size,
    check_normality,
    check_variance_homogeneity,
    perform_t_test,
    perform_mann_whitney_u_test,
    perform_chi_squared_test,
    perform_z_test_proportions,
    analyze_ab_test_results
)

# Text preprocessing and analysis functions
from .text_preprocessing import (
    TextPreprocessor,
    TextVisualizer,
    quick_clean,
    extract_ngrams,
    get_text_stats
)

# Translation utilities
from .translation_utils import (
    detect_language_rows,
    translate_series,
    translate_dataframe,
    run_translation_pipeline,
    translate_all_text
)

# Automated EDA report generator
from .eda_report import generate_eda_report

# Time series analysis functions
from .time_series import (
    decompose_series,
    adf_test,
    kpss_test,
    check_stationarity,
    make_stationary,
    create_lag_features,
    create_rolling_features,
    create_date_features,
    split_time_series,
    time_series_cv_splits,
    evaluate_forecast,
    plot_acf_pacf,
    detect_outliers_iqr,
    interpolate_series,
    resample_series,
    get_acf_pacf_values,
)

# Define what's exported with `from utils import *`
__all__ = [
    # Preprocessing
    'check_data_information',
    'drop_columns',
    'change_binary_dtype',
    'handle_missing_values',
    'filter_outliers',
    'feature_scaling',
    'feature_encoding',

    # Feature selection
    'calculate_correlation_tabular',
    'analyze_categorical_relationships',
    'calculate_vif',
    'calculate_feature_importance',
    
    # Statistics
    'describe_numerical_combined',
    'describe_categorical_combined',
    'describe_date_columns',
    'identify_distribution_types',
    
    # Visualization
    'plot_dynamic_hisplots_kdeplots',
    'plot_dynamic_boxplots_violinplots',
    'plot_dynamic_countplot',
    'plot_dynamic_stripplot_swarmplot',
    'plot_correlation_heatmap',

    # ML regression
    'eval_regression',
    'compare_cv_metrics',
    'tune_pipelines',
    'tune_single_model',
    'tune_all_models',
    'get_model_pipeline',
    'get_hyperparameters',
    'compare_cv_metrics_regression',
    'tune_pipelines_regression',
    'tune_single_model_regression',
    'tune_all_models_regression',
    'get_model_pipeline_regression',
    'get_hyperparameters_regression',
    
    # ML classification
    'eval_classification',
    'compare_cv_metrics_classification',
    'tune_pipelines_classification',
    'tune_single_model_classification',
    'tune_all_models_classification',
    'get_model_pipeline_classification',
    'get_hyperparameters_classification',

    # A/B Testing
    'calculate_sample_size',
    'check_normality',
    'check_variance_homogeneity',
    'perform_t_test',
    'perform_mann_whitney_u_test',
    'perform_chi_squared_test',
    'perform_z_test_proportions',
    'analyze_ab_test_results',

    # Text preprocessing and analysis
    'TextPreprocessor',
    'TextVisualizer',
    'quick_clean',
    'extract_ngrams',
    'get_text_stats',

    # Translation utilities
    'detect_language_rows',
    'translate_series',
    'translate_dataframe',
    'run_translation_pipeline',
    'translate_all_text',

    # Automated EDA report
    'generate_eda_report',

    # Time series analysis
    'decompose_series',
    'adf_test',
    'kpss_test',
    'check_stationarity',
    'make_stationary',
    'create_lag_features',
    'create_rolling_features',
    'create_date_features',
    'split_time_series',
    'time_series_cv_splits',
    'evaluate_forecast',
    'plot_acf_pacf',
    'detect_outliers_iqr',
    'interpolate_series',
    'resample_series',
    'get_acf_pacf_values',
]
