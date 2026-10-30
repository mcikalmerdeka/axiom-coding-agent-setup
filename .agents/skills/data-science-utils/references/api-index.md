# API index

Every public function and class in the bundled `utils` package, grouped by module.

The internal modules `_ml_common.py` and `_plotting.py` are implementation details and are not part of the public API.


## Preprocessing

Data inspection, cleaning, imputation, outlier handling, scaling, and encoding. See [`api/preprocessing.md`](api/preprocessing.md).

- [`check_data_information`](api/preprocessing.md) — Check basic data information including data types, null values, duplicates, unique values, and various data characteristics like zero/negative values, empty strings, and cardinality
- [`drop_columns`](api/preprocessing.md) — Drop specified columns from a DataFrame
- [`change_binary_dtype`](api/preprocessing.md) — Convert binary columns between numerical (0/1) and categorical (No/Yes) representations
- [`handle_missing_values`](api/preprocessing.md) — Handle missing values using various imputation strategies
- [`filter_outliers`](api/preprocessing.md) — Unified function to detect and/or filter outliers using IQR or Z-score method
- [`feature_scaling`](api/preprocessing.md) — General feature scaling function with flexible options. Supports applying different scaling methods to different columns
- [`feature_encoding`](api/preprocessing.md) — General feature encoding function supporting ordinal, one-hot, mean, label, and frequency encoding

## Feature selection

Correlation analysis, categorical association tests, VIF, and univariate importance. See [`api/feature-selection.md`](api/feature-selection.md).

- [`calculate_correlation_tabular`](api/feature-selection.md) — Calculate and display correlation analysis in tabular form for feature-to-feature, feature-to-target correlations, or both
- [`analyze_categorical_relationships`](api/feature-selection.md) — Analyze relationships between categorical features and target using Chi-Square test and calculate effect sizes using Cramér's V
- [`calculate_vif`](api/feature-selection.md) — Calculate VIF for each feature in the dataset
- [`calculate_feature_importance`](api/feature-selection.md) — Calculate feature importance scores using different statistical methods for classification or regression

## Statistics

Descriptive statistics for numerical, categorical, and date columns plus distribution typing. See [`api/statistics.md`](api/statistics.md).

- [`describe_numerical_combined`](api/statistics.md) — Generate descriptive statistics for numerical columns in a dataframe, both overall and optionally grouped by a categorical variable
- [`describe_categorical_combined`](api/statistics.md) — Generate descriptive statistics for categorical columns in a dataframe, both overall and optionally grouped by a categorical variable
- [`describe_date_columns`](api/statistics.md) — Comprehensive analysis of date columns including various temporal features
- [`identify_distribution_types`](api/statistics.md) — Identifies and categorizes the distribution type of each numerical column based on skewness and kurtosis

## Visualization

Notebook-friendly distribution, count, relationship, and correlation plots. See [`api/visualization.md`](api/visualization.md).

- [`plot_dynamic_hisplots_kdeplots`](api/visualization.md) — Creates a dynamic grid of histogram plots (with KDE) or KDE plots for multiple numerical columns
- [`plot_dynamic_boxplots_violinplots`](api/visualization.md) — Creates a dynamic grid of either boxplots or violin plots for multiple numerical columns
- [`plot_dynamic_countplot`](api/visualization.md) — Plots a dynamic grid of countplot for a list of categorical columns from a DataFrame
- [`plot_dynamic_stripplot_swarmplot`](api/visualization.md) — Create multiple stripplots or swarmplots comparing a categorical column against numerical columns
- [`plot_correlation_heatmap`](api/visualization.md) — Plots a correlation heatmap for the specified columns in a dataframe

## Classification

Binary classification evaluation, model comparison, and hyperparameter tuning. See [`api/classification.md`](api/classification.md).

- [`eval_classification`](api/classification.md) — Comprehensively evaluate a classification model using multiple metrics and cross-validation techniques
- [`compare_cv_metrics`](api/classification.md) — Compare cross-validated metrics from multiple classification models in a single table
- [`tune_pipelines`](api/classification.md) — Perform hyperparameter tuning with grid/random search and optional curves
- [`get_model_pipeline`](api/classification.md) — Create a pipeline for a specific model
- [`get_hyperparameters`](api/classification.md) — Get hyperparameter grid for a specific model
- [`tune_single_model`](api/classification.md) — Tune a single model using grid or random search
- [`tune_all_models`](api/classification.md) — Tune multiple classification models using grid or random search

## Regression

Regression evaluation, model comparison, and hyperparameter tuning. See [`api/regression.md`](api/regression.md).

- [`eval_regression`](api/regression.md) — Comprehensively evaluate a regression model using multiple metrics and cross-validation techniques
- [`compare_cv_metrics`](api/regression.md) — Compare cross-validated metrics from multiple models in a single table
- [`tune_pipelines`](api/regression.md) — Perform hyperparameter tuning with grid/random search and optional curves
- [`get_model_pipeline`](api/regression.md) — Create a pipeline for a specific regression model
- [`get_hyperparameters`](api/regression.md) — Get hyperparameter grid for a specific regression model
- [`tune_single_model`](api/regression.md) — Tune a single regression model using grid or random search
- [`tune_all_models`](api/regression.md) — Tune multiple regression models using grid or random search

## A/B testing

Sample sizing, assumption checks, hypothesis tests, and end-to-end experiment analysis. See [`api/ab-testing.md`](api/ab-testing.md).

- [`calculate_sample_size`](api/ab-testing.md) — Calculate the required sample size per variation for an A/B test
- [`check_normality`](api/ab-testing.md) — Perform Shapiro-Wilk test to check for normality
- [`check_variance_homogeneity`](api/ab-testing.md) — Perform Levene's test to check for equal variances
- [`perform_t_test`](api/ab-testing.md) — Perform independent t-test for continuous metrics
- [`perform_mann_whitney_u_test`](api/ab-testing.md) — Perform Mann-Whitney U test for continuous metrics (non-parametric)
- [`perform_chi_squared_test`](api/ab-testing.md) — Perform Chi-squared test for conversion rates
- [`perform_z_test_proportions`](api/ab-testing.md) — Perform Z-test for two proportions
- [`analyze_ab_test_results`](api/ab-testing.md) — Analyze A/B test results from a DataFrame, automatically selecting appropriate tests

## Time series

Decomposition, stationarity, feature engineering, splitting, diagnostics, and forecast metrics. See [`api/time-series.md`](api/time-series.md).

- [`decompose_series`](api/time-series.md) — Decompose a time series into trend, seasonal, and residual components
- [`adf_test`](api/time-series.md) — Perform the Augmented Dickey-Fuller test for stationarity
- [`kpss_test`](api/time-series.md) — Perform the Kwiatkowski-Phillips-Schmidt-Shin (KPSS) test for stationarity
- [`check_stationarity`](api/time-series.md) — Run both ADF and KPSS stationarity tests and return a summary DataFrame
- [`make_stationary`](api/time-series.md) — Attempt to make a time series stationary using differencing
- [`create_lag_features`](api/time-series.md) — Create lagged versions of specified columns
- [`create_rolling_features`](api/time-series.md) — Create rolling-window statistics for specified columns
- [`create_date_features`](api/time-series.md) — Extract common date/time features from a datetime column
- [`split_time_series`](api/time-series.md) — Split a time-ordered DataFrame into train and test sets without shuffling
- [`time_series_cv_splits`](api/time-series.md) — Generate walk-forward cross-validation splits for time series
- [`evaluate_forecast`](api/time-series.md) — Compute common time-series forecast accuracy metrics
- [`plot_acf_pacf`](api/time-series.md) — Plot the Autocorrelation Function (ACF) and Partial Autocorrelation Function (PACF)
- [`detect_outliers_iqr`](api/time-series.md) — Detect outliers in a time series using the IQR method
- [`interpolate_series`](api/time-series.md) — Interpolate missing values in a time series
- [`resample_series`](api/time-series.md) — Resample a time series to a different frequency
- [`get_acf_pacf_values`](api/time-series.md) — Compute ACF and PACF values with confidence intervals

## Text processing

Text cleaning, tokenization, lemmatization, stemming, word clouds, and frequency analysis. See [`api/text.md`](api/text.md).

- [`TextPreprocessor`](api/text.md) — A comprehensive text preprocessing class for NLP tasks
- [`TextVisualizer`](api/text.md) — A class for creating word clouds and analyzing text data
- [`quick_clean`](api/text.md) — Quickly clean text with common preprocessing steps
- [`extract_ngrams`](api/text.md) — Extract n-grams from text
- [`get_text_stats`](api/text.md) — Calculate basic text statistics for DataFrame columns

## Translation

Language detection, row filtering, and batched translation helpers. See [`api/translation.md`](api/translation.md).

- [`detect_language_rows`](api/translation.md) — Split a DataFrame into rows containing target language(s) and other rows
- [`translate_series`](api/translation.md) — Translate a pandas Series efficiently
- [`translate_dataframe`](api/translation.md) — Translate selected columns of a DataFrame in-place or as a copy
- [`run_translation_pipeline`](api/translation.md) — Full pipeline: detect and split rows containing target language(s), translate them, then recombine into a single DataFrame
- [`translate_all_text`](api/translation.md) — Translate ALL text without language detection

## EDA report

Self-contained HTML exploratory data analysis reports. See [`api/eda-report.md`](api/eda-report.md).

- [`generate_eda_report`](api/eda-report.md) — Generate an automated Exploratory Data Analysis (EDA) report as HTML
