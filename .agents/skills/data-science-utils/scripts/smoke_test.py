"""Verify that the bundled utils package imports and its core workflow runs.

Usage:
    python scripts/smoke_test.py

Only core dependencies from requirements.txt are required. Optional text and
translation helpers are not exercised.
"""

from __future__ import annotations

import sys
import tempfile
import warnings
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

warnings.filterwarnings("ignore", category=UserWarning)


def main() -> int:
    import numpy as np
    import pandas as pd
    from sklearn.model_selection import train_test_split

    from utils import (
        analyze_ab_test_results,
        check_data_information,
        check_stationarity,
        describe_categorical_combined,
        describe_numerical_combined,
        eval_classification,
        eval_regression,
        evaluate_forecast,
        feature_encoding,
        feature_scaling,
        filter_outliers,
        generate_eda_report,
        get_model_pipeline_classification,
        get_model_pipeline_regression,
        handle_missing_values,
        identify_distribution_types,
        split_time_series,
    )

    rng = np.random.default_rng(42)
    n_rows = 120
    data = pd.DataFrame(
        {
            "age": rng.integers(18, 70, n_rows).astype(float),
            "income": rng.normal(50_000, 15_000, n_rows),
            "city": rng.choice(["A", "B", "C"], n_rows),
            "channel": rng.choice(["web", "store"], n_rows),
            "churned": rng.integers(0, 2, n_rows),
            "signup_date": pd.date_range("2024-01-01", periods=n_rows, freq="D"),
        }
    )
    data.loc[::11, "income"] = np.nan

    info = check_data_information(data, data.columns.tolist())
    assert "Feature" in info.columns and len(info) == len(data.columns)

    describe_numerical_combined(data, ["age", "income"])
    describe_categorical_combined(data, ["city", "channel"])
    identify_distribution_types(data, ["age", "income"])

    imputed, imputer = handle_missing_values(data, ["income"], strategy="median")
    assert imputed["income"].isna().sum() == 0 and imputer is None

    knn_train, knn_imputer = handle_missing_values(
        data.iloc[:80], ["income"], strategy="knn", n_neighbors=3
    )
    knn_test, _ = handle_missing_values(
        data.iloc[80:], ["income"], strategy="knn", imputer=knn_imputer
    )
    assert knn_test["income"].isna().sum() == 0

    outlier_summary = filter_outliers(data, ["income"], detect_only=True, verbose=False)
    assert "Outlier Data" in outlier_summary.columns

    scaled, scaler = feature_scaling(imputed, columns=["age", "income"], method="standard")
    assert scaler is not None and scaled[["age", "income"]].notna().all().all()

    train, test = train_test_split(
        imputed, test_size=0.25, random_state=42, stratify=imputed["churned"]
    )
    train_encoded, encoders = feature_encoding(
        train, nominal_columns=["city"], binary_columns=["channel"], target=train["churned"]
    )
    test_encoded, _ = feature_encoding(
        test, nominal_columns=["city"], binary_columns=["channel"], encoders=encoders
    )
    assert "city_B" in train_encoded.columns and "city_B" in test_encoded.columns

    features = ["age", "income"]
    classifier = get_model_pipeline_classification("logisticregression").fit(
        train[features], train["churned"]
    )
    classification_metrics = eval_classification(
        model=classifier,
        X_test=test[features],
        y_test=test["churned"],
        X_train=train[features],
        y_train=train["churned"],
        plot_confusion_matrix=False,
        plot_roc_curve=False,
        plot_pr_curve=False,
        plot_calibration_curve=False,
        plot_threshold_analysis=False,
        n_splits=2,
        n_repeats=1,
        display=False,
    )
    assert {"cv", "accuracy", "roc_auc", "confusion_matrix"}.issubset(classification_metrics)

    regressor = get_model_pipeline_regression("linearregression").fit(
        train[["age"]], train["income"]
    )
    regression_metrics = eval_regression(
        model=regressor,
        X_test=test[["age"]],
        y_test=test["income"],
        X_train=train[["age"]],
        y_train=train["income"],
        plot_predicted_vs_actual=False,
        plot_residuals=False,
        plot_residuals_dist=False,
        n_splits=2,
        n_repeats=1,
        display=False,
    )
    assert {"cv", "mae", "rmse", "r2"}.issubset(regression_metrics)

    experiment = pd.DataFrame(
        {
            "group": np.repeat(["A", "B"], 100),
            "converted": np.r_[rng.integers(0, 2, 100), rng.integers(0, 2, 100)],
        }
    )
    ab_result = analyze_ab_test_results(
        experiment, metric_col="converted", group_col="group", metric_type="binary"
    )
    assert "p_value" in ab_result

    series = pd.Series(
        rng.normal(size=60).cumsum(),
        index=pd.date_range("2023-01-01", periods=60, freq="MS"),
    )
    assert len(check_stationarity(series)) == 2
    train_ts, test_ts = split_time_series(imputed, test_size=0.2)
    forecast = evaluate_forecast(test_ts["income"].fillna(0), test_ts["income"].fillna(1))
    assert "rmse" in forecast

    with tempfile.TemporaryDirectory() as tmp:
        report_path = Path(tmp) / "eda_report.html"
        report = generate_eda_report(data, target="churned", output_path=report_path, verbose=False)
        assert report_path.exists() and "<html" in report.lower()

    print("data-science-utils smoke test passed")
    print(f"pandas {pd.__version__}, numpy {np.__version__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
