"""Shared validation and estimator helpers for unsupervised utilities."""

from __future__ import annotations

from typing import Any, Optional

import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering, DBSCAN, KMeans
from sklearn.mixture import GaussianMixture


_ALGORITHM_ALIASES = {
    "kmeans": "kmeans",
    "k_means": "kmeans",
    "agglomerative": "agglomerative",
    "agglomerative_clustering": "agglomerative",
    "hierarchical": "agglomerative",
    "dbscan": "dbscan",
    "gmm": "gmm",
    "gaussian_mixture": "gmm",
    "gaussianmixture": "gmm",
}


def as_numeric_frame(data: Any, *, name: str = "data") -> pd.DataFrame:
    """Return a numeric-only DataFrame or raise an actionable error."""
    if isinstance(data, pd.DataFrame):
        frame = data.copy()
    else:
        values = np.asarray(data)
        if values.ndim != 2:
            raise ValueError(f"{name} must be a 2D array-like object.")
        frame = pd.DataFrame(values)

    if frame.empty:
        raise ValueError(f"{name} is empty.")
    if len(frame) < 2:
        raise ValueError(f"{name} must contain at least two rows.")

    non_numeric = [
        str(column)
        for column in frame.columns
        if not pd.api.types.is_numeric_dtype(frame[column])
    ]
    if non_numeric:
        raise ValueError(
            f"{name} must contain only numeric columns; non-numeric: "
            f"{', '.join(non_numeric)}. Encode categorical columns first with "
            "feature_encoding()."
        )

    try:
        values = frame.to_numpy(dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{name} contains values that cannot be converted to numeric floats. "
            "Check the column dtypes and missing values."
        ) from exc

    if not np.isfinite(values).all():
        bad_columns = [
            str(column)
            for column in frame.columns
            if not np.isfinite(frame[column].to_numpy(dtype=float)).all()
        ]
        raise ValueError(
            f"{name} contains missing or infinite values in: "
            f"{', '.join(bad_columns)}. Handle them first with "
            "handle_missing_values() or remove the affected rows."
        )

    return frame


def as_label_series(
    labels: Any,
    *,
    index: Optional[pd.Index] = None,
    name: str = "cluster",
    n_samples: Optional[int] = None,
) -> pd.Series:
    """Return cluster labels as a Series aligned to ``index`` when possible."""
    if isinstance(labels, pd.Series):
        series = labels.copy()
        if index is not None and not series.index.equals(index):
            if len(series) != len(index):
                raise ValueError(
                    "labels length must match the number of rows in the data."
                )
            if not series.index.has_duplicates and set(series.index) == set(index):
                series = series.reindex(index)
            else:
                series = pd.Series(series.to_numpy(), index=index)
    else:
        values = np.asarray(labels)
        if values.ndim != 1:
            raise ValueError("labels must be one-dimensional.")
        if index is not None and len(values) != len(index):
            raise ValueError(
                "labels length must match the number of rows in the data."
            )
        series = pd.Series(values, index=index)

    if n_samples is not None and len(series) != n_samples:
        raise ValueError(
            "labels length must match the number of rows in the data."
        )
    if series.isna().any():
        raise ValueError("labels must not contain missing values.")

    series.name = name
    return series


def resolve_algorithm(algorithm: str) -> str:
    """Normalize a clustering algorithm name."""
    key = str(algorithm).strip().lower().replace("-", "_").replace(" ", "_")
    if key not in _ALGORITHM_ALIASES:
        supported = ", ".join(sorted(set(_ALGORITHM_ALIASES.values())))
        raise ValueError(
            f"Unknown clustering algorithm {algorithm!r}. "
            f"Supported algorithms: {supported}."
        )
    return _ALGORITHM_ALIASES[key]


def validate_n_clusters(n_clusters: Any, n_samples: int) -> int:
    """Validate an explicit cluster count for k-based algorithms."""
    if n_clusters is None:
        raise ValueError(
            "n_clusters is required for KMeans, AgglomerativeClustering, and "
            "GaussianMixture. Use find_optimal_clusters() to choose it."
        )
    if isinstance(n_clusters, bool) or not isinstance(
        n_clusters, (int, np.integer)
    ):
        raise TypeError("n_clusters must be an integer.")
    if n_clusters < 2:
        raise ValueError("n_clusters must be at least 2.")
    if n_clusters >= n_samples:
        raise ValueError(
            "n_clusters must be smaller than the number of samples so that "
            "clusters can be evaluated."
        )
    return int(n_clusters)


def build_clusterer(
    algorithm: str,
    n_clusters: Any,
    n_samples: int,
    random_state: int,
    **kwargs: Any,
):
    """Create an unfitted scikit-learn clustering estimator."""
    key = resolve_algorithm(algorithm)

    if key == "dbscan":
        if n_clusters is not None:
            raise ValueError(
                "DBSCAN does not use n_clusters. Pass n_clusters=None and tune "
                "eps/min_samples instead."
            )
        return DBSCAN(**kwargs)

    n_clusters = validate_n_clusters(n_clusters, n_samples)

    if key == "kmeans":
        params = {
            "n_clusters": n_clusters,
            "random_state": random_state,
            "n_init": 10,
        }
        params.update(kwargs)
        return KMeans(**params)

    if key == "agglomerative":
        params = {"n_clusters": n_clusters}
        params.update(kwargs)
        return AgglomerativeClustering(**params)

    params = {"n_components": n_clusters, "random_state": random_state}
    params.update(kwargs)
    return GaussianMixture(**params)
