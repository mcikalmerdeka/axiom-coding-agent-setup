"""Dimensionality-reduction helpers for tabular data."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Optional, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from sklearn.decomposition import PCA, TruncatedSVD
from sklearn.manifold import TSNE

from ._plotting import finalize_figure, save_figure
from ._unsupervised_common import as_numeric_frame


_METHOD_ALIASES = {
    "pca": "pca",
    "principal_component_analysis": "pca",
    "tsvd": "tsvd",
    "truncated_svd": "tsvd",
    "svd": "tsvd",
    "tsne": "tsne",
    "t_sne": "tsne",
}


def _resolve_method(method: str) -> str:
    key = str(method).strip().lower().replace("-", "_").replace(" ", "_")
    if key not in _METHOD_ALIASES:
        supported = ", ".join(sorted(set(_METHOD_ALIASES.values())))
        raise ValueError(
            f"Unknown dimensionality-reduction method {method!r}. "
            f"Supported methods: {supported}."
        )
    return _METHOD_ALIASES[key]


def _validate_components(
    n_components: Any,
    n_samples: int,
    n_features: int,
    method: str,
) -> Union[int, float, None]:
    if n_components is None:
        if method == "pca":
            return None
        raise ValueError("n_components is required for TruncatedSVD.")

    if isinstance(n_components, bool):
        raise TypeError("n_components must be an integer or a float in (0, 1).")

    if isinstance(n_components, (int, np.integer)):
        value = int(n_components)
        if value < 1:
            raise ValueError("n_components must be at least 1.")
        max_components = min(n_samples, n_features)
        if value > max_components:
            raise ValueError(
                f"n_components={value} is too large; the maximum for this "
                f"dataset is {max_components}."
            )
        if method == "tsvd" and value >= n_features:
            raise ValueError(
                "TruncatedSVD requires n_components to be smaller than the "
                "number of features."
            )
        return value

    if isinstance(n_components, (float, np.floating)):
        if not 0 < n_components < 1:
            raise ValueError(
                "Float n_components must be between 0 and 1 (exclusive)."
            )
        return float(n_components)

    raise TypeError("n_components must be an integer or a float in (0, 1).")


def _validate_tsne_components(n_components: Any, n_samples: int) -> int:
    if isinstance(n_components, bool) or not isinstance(
        n_components, (int, np.integer)
    ):
        raise TypeError("n_components must be an integer for t-SNE.")
    value = int(n_components)
    if value < 1:
        raise ValueError("n_components must be at least 1.")
    if n_samples < 3:
        raise ValueError("t-SNE requires at least three samples.")
    if value >= n_samples:
        raise ValueError(
            "n_components must be smaller than the number of samples for t-SNE."
        )
    return value


def reduce_dimensions(
    data: Any,
    method: str = "pca",
    n_components: Union[int, float, None] = 0.85,
    *,
    columns: Optional[Iterable[str]] = None,
    random_state: int = 42,
    **kwargs: Any,
) -> Tuple[pd.DataFrame, Any]:
    """
    Reduce a numeric feature matrix with PCA, TruncatedSVD, or t-SNE.

    Parameters:
    -----------
    data : pd.DataFrame or array-like
        Numeric feature matrix. Categorical columns must be encoded first and
        missing values handled first.
    method : {'pca', 'tsvd', 'tsne'}, default='pca'
        Dimensionality-reduction method. ``'truncated_svd'`` and ``'t-sne'``
        aliases are accepted.
    n_components : int or float, default=0.85
        Number of components. For PCA and TruncatedSVD, a float in (0, 1)
        selects enough components to explain that fraction of variance.
        t-SNE requires an integer.
    columns : iterable of str, optional
        Subset of DataFrame columns to use. Only valid for DataFrame input.
    random_state : int, default=42
        Random seed for PCA, TruncatedSVD, and t-SNE.
    **kwargs
        Extra keyword arguments passed to the scikit-learn estimator.

    Returns:
    --------
    reduced : pd.DataFrame
        Reduced feature matrix with columns ``PC 1...``, ``SVD 1...``, or
        ``TSNE 1...``. The input index is preserved.
    reducer : sklearn estimator
        Fitted PCA, TruncatedSVD, or TSNE object. PCA and TruncatedSVD support
        ``transform`` for new data; t-SNE is visualization-only and does not.

    Examples:
    ---------
    >>> X_pca, pca = reduce_dimensions(X_scaled, method='pca', n_components=0.85)
    >>> X_test_pca = pca.transform(X_test_scaled)
    """
    key = _resolve_method(method)

    if isinstance(data, pd.DataFrame):
        frame = data.copy()
        if columns is not None:
            requested = list(columns)
            missing = [column for column in requested if column not in frame.columns]
            if missing:
                raise ValueError(
                    "columns contains names that are not in data: "
                    f"{', '.join(map(str, missing))}."
                )
            frame = frame.loc[:, requested]
    else:
        if columns is not None:
            raise ValueError("columns is only supported when data is a DataFrame.")
        frame = data

    frame = as_numeric_frame(frame)
    n_samples, n_features = frame.shape

    if key in {"pca", "tsvd"}:
        components = _validate_components(
            n_components, n_samples, n_features, key
        )
        if key == "pca":
            reducer = PCA(
                n_components=components,
                random_state=random_state,
                **kwargs,
            )
            prefix = "PC"
        else:
            reducer = TruncatedSVD(
                n_components=components,
                random_state=random_state,
                **kwargs,
            )
            prefix = "SVD"
        transformed = reducer.fit_transform(frame)
    else:
        components = _validate_tsne_components(n_components, n_samples)
        perplexity = kwargs.pop(
            "perplexity",
            min(30.0, max(1.0, (n_samples - 1) / 3.0)),
        )
        if not 1 <= perplexity < n_samples:
            raise ValueError(
                "perplexity must be at least 1 and smaller than the number of "
                "samples for t-SNE."
            )
        reducer = TSNE(
            n_components=components,
            random_state=random_state,
            perplexity=perplexity,
            **kwargs,
        )
        prefix = "TSNE"
        transformed = reducer.fit_transform(frame)

    reduced = pd.DataFrame(
        transformed,
        index=frame.index,
        columns=[f"{prefix} {i}" for i in range(1, transformed.shape[1] + 1)],
    )
    return reduced, reducer


def explained_variance_table(reducer: Any) -> pd.DataFrame:
    """
    Return a table of explained variance for a fitted PCA or TruncatedSVD.

    Parameters:
    -----------
    reducer : fitted PCA or TruncatedSVD
        Estimator returned by :func:`reduce_dimensions`.

    Returns:
    --------
    pd.DataFrame
        Columns: ``component``, ``explained_variance``,
        ``explained_variance_ratio``, and ``cumulative_ratio``.
    """
    ratios = getattr(reducer, "explained_variance_ratio_", None)
    if ratios is None:
        raise ValueError(
            "explained_variance_table requires a fitted PCA or TruncatedSVD "
            "estimator with explained_variance_ratio_."
        )

    ratios = np.asarray(ratios, dtype=float)
    variance = getattr(reducer, "explained_variance_", None)
    if variance is None:
        variance = np.full(len(ratios), np.nan)
    else:
        variance = np.asarray(variance, dtype=float)

    return pd.DataFrame(
        {
            "component": np.arange(1, len(ratios) + 1),
            "explained_variance": variance,
            "explained_variance_ratio": ratios,
            "cumulative_ratio": np.cumsum(ratios),
        }
    )


def plot_explained_variance(
    reducer: Any,
    *,
    threshold: Optional[float] = None,
    figsize: Tuple[float, float] = (8, 5),
    show: bool = True,
    save_path: Optional[Union[str, Path]] = None,
) -> Figure:
    """
    Plot individual and cumulative explained variance for PCA or TruncatedSVD.

    Parameters:
    -----------
    reducer : fitted PCA or TruncatedSVD
        Estimator returned by :func:`reduce_dimensions`.
    threshold : float, optional
        Cumulative variance threshold to mark, for example ``0.85``.
    figsize : tuple, default=(8, 5)
        Figure size.
    show : bool, default=True
        Call ``plt.show()`` when True.
    save_path : str or pathlib.Path, optional
        Save the figure to this path.

    Returns:
    --------
    matplotlib.figure.Figure
    """
    table = explained_variance_table(reducer)
    if threshold is not None and not 0 < threshold <= 1:
        raise ValueError("threshold must be between 0 and 1.")

    fig, ax = plt.subplots(figsize=figsize)
    components = table["component"].to_numpy()
    ax.bar(
        components,
        table["explained_variance_ratio"],
        alpha=0.65,
        color="tab:blue",
        label="Individual",
    )
    ax.set_xlabel("Component")
    ax.set_ylabel("Explained variance ratio")
    ax.set_xticks(components)
    ax.set_title("Explained variance by component")
    ax.grid(axis="y", alpha=0.3)

    ax2 = ax.twinx()
    ax2.plot(
        components,
        table["cumulative_ratio"],
        color="tab:red",
        marker="o",
        linewidth=2,
        label="Cumulative",
    )
    ax2.set_ylabel("Cumulative explained variance")
    ax2.set_ylim(0, 1.05)

    if threshold is not None:
        ax2.axhline(
            threshold,
            color="gray",
            linestyle="--",
            linewidth=1,
            label=f"Threshold ({threshold:.0%})",
        )
        reached = table["cumulative_ratio"].to_numpy() >= threshold
        if reached.any():
            needed = int(np.argmax(reached)) + 1
            ax2.annotate(
                f"{needed} component{'s' if needed != 1 else ''}",
                xy=(needed, threshold),
                xytext=(5, 8),
                textcoords="offset points",
                color="gray",
                fontsize=9,
            )

    handles1, labels1 = ax.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(handles1 + handles2, labels1 + labels2, loc="center right")

    finalize_figure(fig, show=show)
    if save_path is not None:
        save_figure(fig, save_path)
    return fig
