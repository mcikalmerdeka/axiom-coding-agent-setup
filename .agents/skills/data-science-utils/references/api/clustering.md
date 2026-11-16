# Clustering API

Source: `scripts/utils/clustering.py`

> Auto-generated from the bundled source. Re-run
> `python scripts/dev/generate_references.py` after changing the package.


Cluster model selection, fitting, evaluation, profiling, and visualization.

## Quick index

| Name | Summary |
| --- | --- |
| `find_optimal_clusters` | Evaluate a range of cluster counts and plot the selection metrics |
| `fit_clustering` | Fit a clustering algorithm and return labels plus the fitted estimator |
| `predict_clusters` | Assign clusters to new data with a fitted model that supports prediction |
| `evaluate_clustering` | Evaluate clustering quality with internal validation metrics |
| `profile_clusters` | Summarize cluster size and feature behavior |
| `plot_clusters` | Plot a 2D embedding colored by cluster label |
| `plot_cluster_profiles` | Plot a heatmap of cluster profile metrics |

### `find_optimal_clusters`

```python
def find_optimal_clusters(data: Any, *, k_range: Iterable[int]=range(2, 11), algorithm: str='kmeans', random_state: int=42, plot: bool=True, show: bool=True, figsize: Optional[Tuple[float, float]]=None, save_path: Optional[Union[str, Path]]=None, **kwargs: Any) -> Tuple[pd.DataFrame, Optional[Figure]]
```

Evaluate a range of cluster counts and plot the selection metrics.

**Parameters**
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

**Returns**
results : pd.DataFrame
    Metrics indexed by ``k``. KMeans includes ``inertia``; GMM includes
    ``bic`` and ``aic``; every algorithm includes ``silhouette``,
    ``calinski_harabasz``, and ``davies_bouldin``.
figure : matplotlib.figure.Figure or None
    The metric grid when ``plot=True``, otherwise ``None``.

**Examples**
>>> results, fig = find_optimal_clusters(X_pca, k_range=range(2, 11))
>>> best_k = results["silhouette"].idxmax()

### `fit_clustering`

```python
def fit_clustering(data: Any, algorithm: str='kmeans', n_clusters: Optional[int]=None, *, random_state: int=42, **kwargs: Any) -> Tuple[pd.Series, Any]
```

Fit a clustering algorithm and return labels plus the fitted estimator.

**Parameters**
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

**Returns**
labels : pd.Series
    Cluster labels named ``cluster`` and aligned to the input index.
    DBSCAN noise points are ``-1``.
model : sklearn estimator
    Fitted clustering estimator. KMeans and GaussianMixture support
    ``predict``; AgglomerativeClustering and DBSCAN do not.

**Examples**
>>> labels, kmeans = fit_clustering(X_pca, algorithm='kmeans', n_clusters=4)
>>> labels, dbscan = fit_clustering(
...     X_scaled, algorithm='dbscan', n_clusters=None, eps=0.5, min_samples=5
... )

### `predict_clusters`

```python
def predict_clusters(model: Any, data: Any) -> pd.Series
```

Assign clusters to new data with a fitted model that supports prediction.

**Parameters**
model : fitted clustering estimator
    A KMeans or GaussianMixture model returned by :func:`fit_clustering`.
data : pd.DataFrame or array-like
    New numeric feature matrix with the same columns and order as training.

**Returns**
pd.Series
    Predicted labels named ``cluster``, aligned to the new data index.

**Raises**
ValueError
    If the model does not support prediction (AgglomerativeClustering or
    DBSCAN) or if the new data does not match the training features.

### `evaluate_clustering`

```python
def evaluate_clustering(data: Any, labels: Any, *, sample_size: Optional[int]=None, random_state: int=42) -> dict[str, Any]
```

Evaluate clustering quality with internal validation metrics.

**Parameters**
data : pd.DataFrame or array-like
    Numeric feature matrix used for clustering.
labels : array-like or pd.Series
    Cluster labels. DBSCAN noise labels (``-1``) are counted separately
    for reporting but remain part of the metric calculations.
sample_size : int, optional
    Subsample size for silhouette only. Useful for large datasets.
random_state : int, default=42
    Random seed for silhouette subsampling.

**Returns**
dict
    ``silhouette``, ``calinski_harabasz``, ``davies_bouldin``,
    ``n_clusters``, ``n_noise``, and ``cluster_sizes``.

### `profile_clusters`

```python
def profile_clusters(data: pd.DataFrame, labels: Any, *, numeric_agg: Any='mean', categorical_agg: Any='mode', include: Optional[Iterable[str]]=None, exclude: Optional[Iterable[str]]=None) -> pd.DataFrame
```

Summarize cluster size and feature behavior.

**Parameters**
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

**Returns**
pd.DataFrame
    Indexed by cluster label with ``count``, ``percentage``, numeric
    aggregates, and categorical summaries.

### `plot_clusters`

```python
def plot_clusters(embedding: Any, labels: Any, *, x: Optional[str]=None, y: Optional[str]=None, hue_name: str='Cluster', palette: str='deep', figsize: Tuple[float, float]=(10, 6), point_size: float=60, alpha: float=0.7, show: bool=True, save_path: Optional[Union[str, Path]]=None) -> Figure
```

Plot a 2D embedding colored by cluster label.

**Parameters**
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

**Returns**
matplotlib.figure.Figure

### `plot_cluster_profiles`

```python
def plot_cluster_profiles(profile: pd.DataFrame, *, normalize: bool=True, cmap: str='viridis', figsize: Optional[Tuple[float, float]]=None, annot: bool=True, show: bool=True, save_path: Optional[Union[str, Path]]=None) -> Figure
```

Plot a heatmap of cluster profile metrics.

**Parameters**
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

**Returns**
matplotlib.figure.Figure
