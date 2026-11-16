# Dimensionality reduction API

Source: `scripts/utils/dimensionality_reduction.py`

> Auto-generated from the bundled source. Re-run
> `python scripts/dev/generate_references.py` after changing the package.


PCA, TruncatedSVD, and t-SNE with explained-variance diagnostics.

## Quick index

| Name | Summary |
| --- | --- |
| `reduce_dimensions` | Reduce a numeric feature matrix with PCA, TruncatedSVD, or t-SNE |
| `explained_variance_table` | Return a table of explained variance for a fitted PCA or TruncatedSVD |
| `plot_explained_variance` | Plot individual and cumulative explained variance for PCA or TruncatedSVD |

### `reduce_dimensions`

```python
def reduce_dimensions(data: Any, method: str='pca', n_components: Union[int, float, None]=0.85, *, columns: Optional[Iterable[str]]=None, random_state: int=42, **kwargs: Any) -> Tuple[pd.DataFrame, Any]
```

Reduce a numeric feature matrix with PCA, TruncatedSVD, or t-SNE.

**Parameters**
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

**Returns**
reduced : pd.DataFrame
    Reduced feature matrix with columns ``PC 1...``, ``SVD 1...``, or
    ``TSNE 1...``. The input index is preserved.
reducer : sklearn estimator
    Fitted PCA, TruncatedSVD, or TSNE object. PCA and TruncatedSVD support
    ``transform`` for new data; t-SNE is visualization-only and does not.

**Examples**
>>> X_pca, pca = reduce_dimensions(X_scaled, method='pca', n_components=0.85)
>>> X_test_pca = pca.transform(X_test_scaled)

### `explained_variance_table`

```python
def explained_variance_table(reducer: Any) -> pd.DataFrame
```

Return a table of explained variance for a fitted PCA or TruncatedSVD.

**Parameters**
reducer : fitted PCA or TruncatedSVD
    Estimator returned by :func:`reduce_dimensions`.

**Returns**
pd.DataFrame
    Columns: ``component``, ``explained_variance``,
    ``explained_variance_ratio``, and ``cumulative_ratio``.

### `plot_explained_variance`

```python
def plot_explained_variance(reducer: Any, *, threshold: Optional[float]=None, figsize: Tuple[float, float]=(8, 5), show: bool=True, save_path: Optional[Union[str, Path]]=None) -> Figure
```

Plot individual and cumulative explained variance for PCA or TruncatedSVD.

**Parameters**
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

**Returns**
matplotlib.figure.Figure
