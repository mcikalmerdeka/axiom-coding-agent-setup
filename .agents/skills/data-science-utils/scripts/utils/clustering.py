"""Clustering helpers for tabular data."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.figure import Figure
from sklearn.metrics import (
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)

from ._plotting import finalize_figure, save_figure
from ._unsupervised_common import (
    as_label_series,
    as_numeric_frame,
    build_clusterer,
    resolve_algorithm,
)


def _score_labels(values: np.ndarray, labels: np.ndarray) -> dict[str, float]:
    unique = np.unique(labels)
    if len(unique) < 2 or len(unique) >= len(values):
        return {
            "silhouette": np.nan,
            "calinski_harabasz": np.nan,
            "davies_bouldin": np.nan,
        }

    return {
        "silhouette": float(silhouette_score(values, labels)),
        "calinski_harabasz": float(calinski_harabasz_score(values, labels)),
        "davies_bouldin": float(davies_bouldin_score(values, labels)),
    }


def _plot_cluster_selection(
    results: pd.DataFrame,
    *,
    figsize: Optional[Tuple[float, float]] = None,
    show: bool,
    save_path: Optional[Union[str, Path]],
) -> Figure:
    metrics = [
        column for column in results.columns if results[column].notna().any()
    ]
    if not metrics:
        raise ValueError("No clustering metrics were available to plot.")

    ncols = 2 if len(metrics) > 1 else 1
    nrows = int(np.ceil(len(metrics) / ncols))
    figsize = figsize or (12, 4 * nrows)
    fig, axes = plt.subplots(
        nrows=nrows, ncols=ncols, figsize=figsize, squeeze=False
    )
    axes = axes.ravel()

    for ax, metric in zip(axes, metrics):
        valid = results[metric].dropna()
        ax.plot(
            results.index,
            results[metric],
            marker="o",
            linewidth=2,
            color="tab:blue",
        )
        if not valid.empty:
            best = (
                valid.idxmax()
                if metric in {"silhouette", "calinski_harabasz"}
                else valid.idxmin()
            )
            ax.scatter(
                [best],
                [valid.loc[best]],
                color="tab:red",
                s=70,
                zorder=3,
            )
        ax.set_title(metric.replace("_", " ").title())
        ax.set_xlabel("Number of clusters")
        ax.set_ylabel(metric.replace("_", " ").title())
        ax.grid(alpha=0.3)

    for ax in axes[len(metrics) :]:
        ax.set_visible(False)

    fig.suptitle("Cluster selection metrics")
    finalize_figure(fig, show=show)
    if save_path is not None:
        save_figure(fig, save_path)
    return fig


def find_optimal_clusters(
    data: Any,
    *,
    k_range: Iterable[int] = range(2, 11),
    algorithm: str = "kmeans",
    random_state: int = 42,
    plot: bool = True,
    show: bool = True,
    figsize: Optional[Tuple[float, float]] = None,
    save_path: Optional[Union[str, Path]] = None,
    **kwargs: Any,
) -> Tuple[pd.DataFrame, Optional[Figure]]:
    """
    Evaluate a range of cluster counts and plot the selection metrics.

    Parameters:
    -----------
    data : pd.DataFrame or array-like
        Numeric feature matrix.
    k_range : iterable of int, default=range(2, 11)
        Candidate cluster counts. Every value must be at least 2 and smaller
        than the number of samples.
    algorithm : {'kmeans', 'agglomerative', 'gmm'}, default='kmeans'
        Clustering algorithm. DBSCAN is not supported because it does not use
        a cluster count; tune ``eps`` and ``min_samples`` directly.
    random_state : int, default=42
        Random seed for the clustering estimator.
    plot : bool, default=True
        Draw a metric grid and return the figure.
    show : bool, default=True
        Call ``plt.show()`` when True.
    figsize : tuple, optional
        Figure size for the metric grid.
    save_path : str or pathlib.Path, optional
        Save the metric figure to this path.
    **kwargs
        Extra keyword arguments passed to the clustering estimator.

    Returns:
    --------
    results : pd.DataFrame
        Metrics indexed by ``k``. KMeans includes ``inertia``; GMM includes
        ``bic`` and ``aic``; every algorithm includes ``silhouette``,
        ``calinski_harabasz``, and ``davies_bouldin``.
    figure : matplotlib.figure.Figure or None
        The metric grid when ``plot=True``, otherwise ``None``.

    Examples:
    ---------
    >>> results, fig = find_optimal_clusters(X_pca, k_range=range(2, 11))
    >>> best_k = results["silhouette"].idxmax()
    """
    key = resolve_algorithm(algorithm)
    if key == "dbscan":
        raise ValueError(
            "DBSCAN does not use a cluster count. Tune eps/min_samples "
            "directly instead of calling find_optimal_clusters()."
        )
    if not plot and save_path is not None:
        raise ValueError("save_path requires plot=True.")

    frame = as_numeric_frame(data)
    values = frame.to_numpy(dtype=float)

    k_values: list[int] = []
    for value in k_range:
        if isinstance(value, bool) or not isinstance(value, (int, np.integer)):
            raise TypeError("k_range must contain integers.")
        k_values.append(int(value))
    k_values = sorted(set(k_values))

    if not k_values:
        raise ValueError("k_range must contain at least one cluster count.")
    if k_values[0] < 2:
        raise ValueError("k_range values must be at least 2.")
    if k_values[-1] >= len(frame):
        raise ValueError(
            "Every k in k_range must be smaller than the number of samples."
        )

    rows: list[dict[str, float]] = []
    for n_clusters in k_values:
        model = build_clusterer(
            key,
            n_clusters,
            len(frame),
            random_state,
            **kwargs,
        )
        labels = model.fit_predict(values)

        row: dict[str, float] = {}
        if key == "kmeans":
            row["inertia"] = float(model.inertia_)
        elif key == "gmm":
            row["bic"] = float(model.bic(values))
            row["aic"] = float(model.aic(values))
        row.update(_score_labels(values, labels))
        rows.append(row)

    results = pd.DataFrame(rows, index=pd.Index(k_values, name="k"))

    figure = None
    if plot:
        figure = _plot_cluster_selection(
            results,
            figsize=figsize,
            show=show,
            save_path=save_path,
        )

    return results, figure


def fit_clustering(
    data: Any,
    algorithm: str = "kmeans",
    n_clusters: Optional[int] = None,
    *,
    random_state: int = 42,
    **kwargs: Any,
) -> Tuple[pd.Series, Any]:
    """
    Fit a clustering algorithm and return labels plus the fitted estimator.

    Parameters:
    -----------
    data : pd.DataFrame or array-like
        Numeric feature matrix.
    algorithm : {'kmeans', 'agglomerative', 'dbscan', 'gmm'}, default='kmeans'
        Clustering algorithm.
    n_clusters : int, optional
        Number of clusters for KMeans, AgglomerativeClustering, and
        GaussianMixture. Required for those algorithms. Pass ``None`` for
        DBSCAN, which uses ``eps`` and ``min_samples`` instead.
    random_state : int, default=42
        Random seed where supported.
    **kwargs
        Extra keyword arguments passed to the scikit-learn estimator, such as
        ``eps``, ``min_samples``, ``linkage``, or ``covariance_type``.

    Returns:
    --------
    labels : pd.Series
        Cluster labels named ``cluster`` and aligned to the input index.
        DBSCAN noise points are ``-1``.
    model : sklearn estimator
        Fitted clustering estimator. KMeans and GaussianMixture support
        ``predict``; AgglomerativeClustering and DBSCAN do not.

    Examples:
    ---------
    >>> labels, kmeans = fit_clustering(X_pca, algorithm='kmeans', n_clusters=4)
    >>> labels, dbscan = fit_clustering(
    ...     X_scaled, algorithm='dbscan', n_clusters=None, eps=0.5, min_samples=5
    ... )
    """
    frame = as_numeric_frame(data)
    model = build_clusterer(
        algorithm,
        n_clusters,
        len(frame),
        random_state,
        **kwargs,
    )
    labels = model.fit_predict(frame.to_numpy(dtype=float))
    return as_label_series(labels, index=frame.index), model


def predict_clusters(model: Any, data: Any) -> pd.Series:
    """
    Assign clusters to new data with a fitted model that supports prediction.

    Parameters:
    -----------
    model : fitted clustering estimator
        A KMeans or GaussianMixture model returned by :func:`fit_clustering`.
    data : pd.DataFrame or array-like
        New numeric feature matrix with the same columns and order as training.

    Returns:
    --------
    pd.Series
        Predicted labels named ``cluster``, aligned to the new data index.

    Raises:
    -------
    ValueError
        If the model does not support prediction (AgglomerativeClustering or
        DBSCAN) or if the new data does not match the training features.
    """
    if not hasattr(model, "predict"):
        raise ValueError(
            "This clustering model does not support prediction on new data. "
            "KMeans and GaussianMixture support predict; refit "
            "AgglomerativeClustering or DBSCAN for new data instead."
        )

    frame = as_numeric_frame(data, name="new data")
    try:
        labels = model.predict(frame.to_numpy(dtype=float))
    except ValueError as exc:
        raise ValueError(
            "Could not predict clusters. Ensure the new data has the same "
            "numeric features and column order as the training data. "
            f"Original error: {exc}"
        ) from exc

    return as_label_series(labels, index=frame.index)


def evaluate_clustering(
    data: Any,
    labels: Any,
    *,
    sample_size: Optional[int] = None,
    random_state: int = 42,
) -> dict[str, Any]:
    """
    Evaluate clustering quality with internal validation metrics.

    Parameters:
    -----------
    data : pd.DataFrame or array-like
        Numeric feature matrix used for clustering.
    labels : array-like or pd.Series
        Cluster labels. DBSCAN noise labels (``-1``) are counted separately
        for reporting but remain part of the metric calculations.
    sample_size : int, optional
        Subsample size for silhouette only. Useful for large datasets.
    random_state : int, default=42
        Random seed for silhouette subsampling.

    Returns:
    --------
    dict
        ``silhouette``, ``calinski_harabasz``, ``davies_bouldin``,
        ``n_clusters``, ``n_noise``, and ``cluster_sizes``.
    """
    frame = as_numeric_frame(data)
    series = as_label_series(labels, index=frame.index, n_samples=len(frame))
    values = series.to_numpy()
    unique = np.unique(values)

    n_noise = int((values == -1).sum())
    n_clusters = len(unique) - (1 if -1 in unique else 0)

    if n_clusters < 2:
        raise ValueError(
            "Clustering evaluation requires at least two clusters "
            "(excluding noise)."
        )
    if len(unique) >= len(frame):
        raise ValueError(
            "Clustering evaluation requires at least two samples in the same "
            "cluster."
        )

    if sample_size is not None:
        if isinstance(sample_size, bool) or not isinstance(
            sample_size, (int, np.integer)
        ):
            raise TypeError("sample_size must be an integer.")
        sample_size = int(sample_size)
        if sample_size < 2:
            raise ValueError("sample_size must be at least 2.")
        if sample_size >= len(frame):
            sample_size = None

    silhouette_kwargs: dict[str, Any] = {}
    if sample_size is not None:
        silhouette_kwargs = {
            "sample_size": sample_size,
            "random_state": random_state,
        }

    try:
        silhouette = float(
            silhouette_score(
                frame.to_numpy(dtype=float),
                values,
                **silhouette_kwargs,
            )
        )
        calinski = float(
            calinski_harabasz_score(frame.to_numpy(dtype=float), values)
        )
        davies = float(
            davies_bouldin_score(frame.to_numpy(dtype=float), values)
        )
    except ValueError as exc:
        raise ValueError(f"Could not evaluate clustering: {exc}") from exc

    counts = pd.Series(values).value_counts().sort_index()
    cluster_sizes = {
        int(label) if isinstance(label, np.integer) else label: int(count)
        for label, count in counts.items()
    }

    return {
        "silhouette": silhouette,
        "calinski_harabasz": calinski,
        "davies_bouldin": davies,
        "n_clusters": int(n_clusters),
        "n_noise": n_noise,
        "cluster_sizes": cluster_sizes,
    }


def _numeric_profile(
    grouped: Any,
    columns: list[str],
    spec: Any,
) -> dict[str, pd.Series]:
    if spec is None or not columns:
        return {}

    if isinstance(spec, Mapping):
        unknown = [column for column in spec if column not in columns]
        if unknown:
            raise ValueError(
                "numeric_agg contains columns that are not numeric or not "
                f"present: {', '.join(map(str, unknown))}."
            )
        pairs: list[tuple[str, Any]] = []
        for column, aggregations in spec.items():
            if isinstance(aggregations, (list, tuple)):
                pairs.extend((column, agg) for agg in aggregations)
            else:
                pairs.append((column, aggregations))
    else:
        aggregations = spec if isinstance(spec, (list, tuple)) else [spec]
        pairs = [
            (column, agg) for column in columns for agg in aggregations
        ]

    result: dict[str, pd.Series] = {}
    for column, aggregation in pairs:
        suffix = (
            aggregation
            if isinstance(aggregation, str)
            else getattr(aggregation, "__name__", "agg")
        )
        result[f"{column}_{suffix}"] = grouped[column].agg(aggregation)
    return result


def _categorical_profile(
    grouped: Any,
    columns: list[str],
    spec: Any,
) -> dict[str, pd.Series]:
    if spec is None or not columns:
        return {}

    if isinstance(spec, Mapping):
        unknown = [column for column in spec if column not in columns]
        if unknown:
            raise ValueError(
                "categorical_agg contains columns that are not categorical or "
                f"not present: {', '.join(map(str, unknown))}."
            )
        pairs = list(spec.items())
    else:
        pairs = [(column, spec) for column in columns]

    result: dict[str, pd.Series] = {}
    for column, aggregation in pairs:
        if aggregation == "mode":
            series = grouped[column].agg(
                lambda values: (
                    values.mode().iloc[0] if not values.mode().empty else np.nan
                )
            )
            suffix = "mode"
        elif isinstance(aggregation, str):
            series = grouped[column].agg(aggregation)
            suffix = aggregation
        elif callable(aggregation):
            series = grouped[column].agg(aggregation)
            suffix = getattr(aggregation, "__name__", "agg")
        else:
            raise TypeError(
                "categorical_agg values must be 'mode', a pandas aggregation "
                "name, or a callable."
            )
        result[f"{column}_{suffix}"] = series
    return result


def profile_clusters(
    data: pd.DataFrame,
    labels: Any,
    *,
    numeric_agg: Any = "mean",
    categorical_agg: Any = "mode",
    include: Optional[Iterable[str]] = None,
    exclude: Optional[Iterable[str]] = None,
) -> pd.DataFrame:
    """
    Summarize cluster size and feature behavior.

    Parameters:
    -----------
    data : pd.DataFrame
        Original tabular data, including any categorical columns worth
        profiling. Rows must align with ``labels`` by index when ``labels`` is
        a Series.
    labels : array-like or pd.Series
        Cluster labels from :func:`fit_clustering`.
    numeric_agg : str, list, dict, or None, default='mean'
        Aggregation(s) for numeric columns. A string or list applies to every
        numeric column; a dict maps specific columns to one or more
        aggregations. Output columns are suffixed, e.g. ``Income_mean``.
    categorical_agg : {'mode'} or dict or None, default='mode'
        Aggregation for categorical columns. ``'mode'`` returns the most
        frequent value per cluster.
    include : iterable of str, optional
        Columns to keep before profiling.
    exclude : iterable of str, optional
        Columns to drop before profiling.

    Returns:
    --------
    pd.DataFrame
        Indexed by cluster label with ``count``, ``percentage``, numeric
        aggregates, and categorical summaries.
    """
    if not isinstance(data, pd.DataFrame):
        frame = pd.DataFrame(data)
    else:
        frame = data.copy()

    series = as_label_series(labels, index=frame.index, n_samples=len(frame))
    if series.name in frame.columns:
        frame = frame.drop(columns=[series.name])

    if include is not None:
        requested = list(include)
        missing = [column for column in requested if column not in frame.columns]
        if missing:
            raise ValueError(
                "include contains columns that are not in data: "
                f"{', '.join(map(str, missing))}."
            )
        frame = frame.loc[:, requested]

    if exclude is not None:
        frame = frame.drop(
            columns=[column for column in exclude if column in frame.columns]
        )

    frame = frame.copy()
    frame["__cluster__"] = series.to_numpy()
    grouped = frame.groupby("__cluster__", dropna=False, sort=True)

    result = pd.DataFrame(index=grouped.size().index)
    result.index.name = "cluster"
    result["count"] = grouped.size().astype(int)
    result["percentage"] = result["count"] / len(frame) * 100

    numeric_columns = [
        column
        for column in frame.columns
        if column != "__cluster__"
        and pd.api.types.is_numeric_dtype(frame[column])
    ]
    categorical_columns = [
        column
        for column in frame.columns
        if column != "__cluster__" and column not in numeric_columns
    ]

    for name, values in _numeric_profile(
        grouped, numeric_columns, numeric_agg
    ).items():
        result[name] = values
    for name, values in _categorical_profile(
        grouped, categorical_columns, categorical_agg
    ).items():
        result[name] = values

    return result


def plot_clusters(
    embedding: Any,
    labels: Any,
    *,
    x: Optional[str] = None,
    y: Optional[str] = None,
    hue_name: str = "Cluster",
    palette: str = "deep",
    figsize: Tuple[float, float] = (10, 6),
    point_size: float = 60,
    alpha: float = 0.7,
    show: bool = True,
    save_path: Optional[Union[str, Path]] = None,
) -> Figure:
    """
    Plot a 2D embedding colored by cluster label.

    Parameters:
    -----------
    embedding : pd.DataFrame or array-like
        Two-dimensional embedding, typically the output of
        :func:`reduce_dimensions`.
    labels : array-like or pd.Series
        Cluster labels aligned to the embedding rows.
    x, y : str, optional
        Column names to plot. Defaults to the first two columns.
    hue_name : str, default='Cluster'
        Legend and color-column title.
    palette : str, default='deep'
        Seaborn palette for non-noise clusters.
    figsize : tuple, default=(10, 6)
        Figure size.
    point_size : float, default=60
        Scatter point size.
    alpha : float, default=0.7
        Scatter transparency.
    show : bool, default=True
        Call ``plt.show()`` when True.
    save_path : str or pathlib.Path, optional
        Save the figure to this path.

    Returns:
    --------
    matplotlib.figure.Figure
    """
    if isinstance(embedding, pd.DataFrame):
        frame = embedding.copy()
    else:
        values = np.asarray(embedding)
        if values.ndim != 2 or values.shape[1] < 2:
            raise ValueError(
                "embedding must be a 2D array-like object with at least two "
                "columns."
            )
        frame = pd.DataFrame(
            values[:, :2], columns=["Component 1", "Component 2"]
        )

    if frame.shape[1] < 2:
        raise ValueError("embedding must contain at least two columns.")

    x = x if x is not None else str(frame.columns[0])
    y = y if y is not None else str(frame.columns[1])
    if x not in frame.columns or y not in frame.columns:
        raise ValueError("x and y must be column names in embedding.")
    if x == y:
        raise ValueError("x and y must be different columns.")

    series = as_label_series(labels, index=frame.index, n_samples=len(frame))
    plot_frame = frame.loc[:, [x, y]].copy()
    plot_frame[hue_name] = series.to_numpy()

    noise_mask = plot_frame[hue_name] == -1
    fig, ax = plt.subplots(figsize=figsize)

    if noise_mask.all():
        ax.scatter(
            plot_frame[x],
            plot_frame[y],
            c="lightgray",
            s=point_size,
            alpha=alpha,
            edgecolor="white",
            label="Noise (-1)",
        )
    else:
        sns.scatterplot(
            data=plot_frame.loc[~noise_mask],
            x=x,
            y=y,
            hue=hue_name,
            palette=palette,
            s=point_size,
            alpha=alpha,
            edgecolor="white",
            ax=ax,
        )
        if noise_mask.any():
            ax.scatter(
                plot_frame.loc[noise_mask, x],
                plot_frame.loc[noise_mask, y],
                c="lightgray",
                s=point_size,
                alpha=alpha,
                edgecolor="white",
                label="Noise (-1)",
            )

    ax.set_title("Cluster assignments")
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    ax.grid(alpha=0.3)
    ax.legend(
        title=hue_name,
        title_fontsize=10,
        bbox_to_anchor=(1.02, 1),
        loc="upper left",
    )

    finalize_figure(fig, show=show)
    if save_path is not None:
        save_figure(fig, save_path)
    return fig


def plot_cluster_profiles(
    profile: pd.DataFrame,
    *,
    normalize: bool = True,
    cmap: str = "viridis",
    figsize: Optional[Tuple[float, float]] = None,
    annot: bool = True,
    show: bool = True,
    save_path: Optional[Union[str, Path]] = None,
) -> Figure:
    """
    Plot a heatmap of cluster profile metrics.

    Parameters:
    -----------
    profile : pd.DataFrame
        Output of :func:`profile_clusters`.
    normalize : bool, default=True
        Min-max normalize each metric column before coloring. Annotations
        remain in the original units.
    cmap : str, default='viridis'
        Matplotlib colormap.
    figsize : tuple, optional
        Figure size. Inferred from the profile shape by default.
    annot : bool, default=True
        Annotate cells with the original metric values.
    show : bool, default=True
        Call ``plt.show()`` when True.
    save_path : str or pathlib.Path, optional
        Save the figure to this path.

    Returns:
    --------
    matplotlib.figure.Figure
    """
    if not isinstance(profile, pd.DataFrame):
        raise TypeError("profile must be a pandas DataFrame.")

    numeric = profile.select_dtypes(include=[np.number]).copy()
    metadata = [
        column for column in ("count", "percentage") if column in numeric.columns
    ]
    if metadata:
        numeric = numeric.drop(columns=metadata)

    if numeric.empty:
        raise ValueError(
            "profile does not contain numeric metrics to plot after excluding "
            "count and percentage."
        )

    if normalize:
        minimum = numeric.min()
        maximum = numeric.max()
        ranges = (maximum - minimum).replace(0, np.nan)
        heatmap_data = (numeric - minimum) / ranges
        heatmap_data = heatmap_data.fillna(0.5)
        color_label = "Normalized value"
        title = "Cluster profiles (min-max normalized)"
    else:
        heatmap_data = numeric
        color_label = "Value"
        title = "Cluster profiles"

    figsize = figsize or (
        max(8.0, 1.1 * len(numeric.columns) + 4),
        max(4.0, 0.55 * len(numeric.index) + 2),
    )
    fig, ax = plt.subplots(figsize=figsize)
    sns.heatmap(
        heatmap_data,
        cmap=cmap,
        annot=numeric.to_numpy() if annot else False,
        fmt=".2f",
        ax=ax,
        cbar_kws={"label": color_label},
    )
    ax.set_title(title)
    ax.set_xlabel("Metric")
    ax.set_ylabel("Cluster")

    finalize_figure(fig, show=show)
    if save_path is not None:
        save_figure(fig, save_path)
    return fig
