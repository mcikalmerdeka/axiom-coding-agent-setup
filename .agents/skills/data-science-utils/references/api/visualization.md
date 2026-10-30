# Visualization API

Source: `scripts/utils/visualization.py`

> Auto-generated from the bundled source. Re-run
> `python scripts/dev/generate_references.py` after changing the package.


Notebook-friendly distribution, count, relationship, and correlation plots.

## Quick index

| Name | Summary |
| --- | --- |
| `plot_dynamic_hisplots_kdeplots` | Creates a dynamic grid of histogram plots (with KDE) or KDE plots for multiple numerical columns |
| `plot_dynamic_boxplots_violinplots` | Creates a dynamic grid of either boxplots or violin plots for multiple numerical columns |
| `plot_dynamic_countplot` | Plots a dynamic grid of countplot for a list of categorical columns from a DataFrame |
| `plot_dynamic_stripplot_swarmplot` | Create multiple stripplots or swarmplots comparing a categorical column against numerical columns |
| `plot_correlation_heatmap` | Plots a correlation heatmap for the specified columns in a dataframe |

### `plot_dynamic_hisplots_kdeplots`

```python
def plot_dynamic_hisplots_kdeplots(df: pd.DataFrame, col_series: List[str], plot_type: str='histplot', ncols: int=6, figsize: Tuple[int, int]=(26, 18), hue: Optional[str]=None, multiple: str='layer', fill: Optional[bool]=None) -> None
```

Creates a dynamic grid of histogram plots (with KDE) or KDE plots for multiple numerical columns.

**Parameters**
df : pandas.DataFrame
    The DataFrame containing the data to plot.
col_series : List[str]
    List of column names to include in the plots.
plot_type : str, optional, default='histplot'
    Type of plot to generate. Options are:
    - 'histplot': Histogram with KDE overlay
    - 'kdeplot': Kernel Density Estimation plot
ncols : int, optional, default=6
    Number of columns in the subplot grid. Adjust this value to change grid width.
figsize : Tuple[int, int], optional, default=(26, 18)
    Size of the figure to control plot dimensions.
hue : Optional[str], optional, default=None
    Column name to use for color encoding. Creates separate distributions for each category.
multiple : str, optional, default='layer'
    How to display multiple distributions. Options are:
    - 'layer': Distributions are overlaid
    - 'dodge': Distributions are placed side by side
fill : Optional[bool], optional, default=None
    Whether to fill the area under the KDE curve.

**Returns**
None
    Displays a grid of distribution plots.

**Examples**
>>> # Create histogram plots with KDE
>>> plot_dynamic_hisplots_kdeplots(df, ['col1', 'col2'], plot_type='histplot')

>>> # Create KDE plots with categorical splitting
>>> plot_dynamic_hisplots_kdeplots(
...     df,
...     ['col1', 'col2'],
...     plot_type='kdeplot',
...     hue='category',
...     multiple='layer'
... )

**Notes**
- For histplots, KDE (Kernel Density Estimation) is automatically enabled
- The y-axis label adjusts automatically based on the plot type

### `plot_dynamic_boxplots_violinplots`

```python
def plot_dynamic_boxplots_violinplots(df: pd.DataFrame, col_series: List[str], plot_type: str='boxplot', ncols: int=6, figsize: Tuple[int, int]=(26, 18), orientation: str='v', hue: Optional[str]=None) -> None
```

Creates a dynamic grid of either boxplots or violin plots for multiple numerical columns.

**Parameters**
df : pandas.DataFrame
    The DataFrame containing the data to plot.
col_series : List[str]
    List of column names to include in the plots.
plot_type : str, optional, default='boxplot'
    Type of plot to generate. Options are 'boxplot' or 'violinplot'.
ncols : int, optional, default=6
    Number of columns in the subplot grid. Adjust this value to change grid width.
figsize : Tuple[int, int], optional, default=(26, 18)
    Size of the figure to control plot dimensions.
orientation : str, optional, default='v'
    Orientation of the plots. Use 'v' for vertical and 'h' for horizontal.
hue : Optional[str], optional, default=None
    Column name to use for color encoding. Creates separate plots for each category.

**Returns**
None
    Displays a grid of plots.

**Examples**
>>> # Create vertical boxplots
>>> plot_dynamic_boxplots_violinplots(df, ['col1', 'col2'], plot_type='boxplot', orientation='v')

>>> # Create horizontal violin plots with categorical splitting
>>> plot_dynamic_boxplots_violinplots(df, ['col1', 'col2'], plot_type='violinplot',
...                                     orientation='h', hue='category')

### `plot_dynamic_countplot`

```python
def plot_dynamic_countplot(df: pd.DataFrame, col_series: List[str], ncols: int=6, figsize: Tuple[int, int]=(26, 18), stat: str='count', hue: Optional[str]=None, order: Optional[List[Any]]=None) -> None
```

Plots a dynamic grid of countplot for a list of categorical columns from a DataFrame.

**Parameters**
df : pandas.DataFrame
    The DataFrame containing the data to plot.
col_series : List[str]
    List of column names to include in the countplots.
ncols : int, optional, default=6
    Number of columns in the subplot grid. Adjust this value to change grid width.
figsize : Tuple[int, int], optional, default=(26, 18)
    Size of the figure to control plot dimensions.
stat : str, optional, default='count'
    The statistic to compute for the bars
hue : Optional[str], optional, default=None
    Column name to use for color encoding
order : Optional[List[Any]], optional, default=None
    Specific ordering for the categorical variables

**Returns**
None
    Displays a grid of countplots.

**Examples**
>>> # Basic countplot
>>> plot_dynamic_countplot(df, ['gender', 'department', 'job_title'])

>>> # Countplot with hue grouping
>>> plot_dynamic_countplot(df, ['department', 'job_title'], hue='gender')

>>> # With custom order
>>> order_list = [['A', 'B', 'C'], ['Small', 'Medium', 'Large']]
>>> plot_dynamic_countplot(df, ['category', 'size'], order=order_list, ncols=2)

>>> # Show top 5 categories for each column (most frequent)
>>> cats_cols = ['Category', 'Province', 'City']
>>> plot_dynamic_countplot(
...     df=df,
...     col_series=cats_cols,
...     ncols=1,
...     figsize=(12, 10),
...     order=[df[cat].value_counts().iloc[:5].index.tolist() for cat in cats_cols]
... )

>>> # Show bottom 5 categories for each column (least frequent)
>>> plot_dynamic_countplot(
...     df=df,
...     col_series=cats_cols,
...     ncols=1,
...     figsize=(12, 10),
...     order=[df[cat].value_counts().iloc[-5:].index.tolist() for cat in cats_cols]
... )

### `plot_dynamic_stripplot_swarmplot`

```python
def plot_dynamic_stripplot_swarmplot(df: pd.DataFrame, cat_col: str, nums_cols_series: List[str], hue_col: str=None, n_cols: int=2, figsize: Tuple[int, int]=(14, 10), plot_type: str='stripplot') -> None
```

Create multiple stripplots or swarmplots comparing a categorical column against numerical columns.

**Parameters**
df : pandas.DataFrame
    The input dataframe containing the data
cat_col : str
    The name of the categorical column to plot on x-axis
nums_cols_series : List[str]
    List of numerical column names to plot on y-axis
hue_col : str, optional, default=None
    Column name to use for color coding (default: None)
n_cols : int, optional
    Number of columns in the subplot grid (default: 2)
figsize : Tuple[int, int], optional, default=(14, 10)
    Figure size in inches (width, height) (default: (14, 10))
plot_type : str, optional, default='stripplot'
    Type of plot to create: 'stripplot' or 'swarmplot' (default: 'stripplot')

**Examples**
>>> # Create stripplots for numerical columns
>>> plot_dynamic_stripplot_swarmplot(df, cat_col='category', nums_cols_series=['col1', 'col2'], hue_col='hue_col', plot_type='stripplot')

>>> # Create swarmplots for numerical columns
>>> plot_dynamic_stripplot_swarmplot(df, cat_col='category', nums_cols_series=['col1', 'col2'], hue_col='hue_col', plot_type='swarmplot')

**Returns**
None
    Display a grid of plots

### `plot_correlation_heatmap`

```python
def plot_correlation_heatmap(df: pd.DataFrame, col_series: List[str], corr_method: str='pearson', figsize: Tuple[int, int]=(8, 6), cmap: str='coolwarm') -> None
```

Plots a correlation heatmap for the specified columns in a dataframe.

**Parameters**
df : pd.DataFrame
    The input dataframe containing the data.
col_series : List[str]
    List of column names to include in the correlation matrix.
corr_method : str 
    Correlation method ('pearson', 'spearman', or 'kendall'). Default is 'pearson'.
figsize : Tuple[int, int]
    Size of the heatmap figure (width, height). Default is (8, 6).
cmap : str
    Color map for the heatmap. Default is 'coolwarm'.

**Returns**
None
    Displays the correlation heatmap.

**Examples**
>>> included_col = ['Income', 'Total_Spending', 'Age', 'CVR']
>>> plot_correlation_heatmap(df_filtered_outliers, col_series=included_col, corr_method='pearson')
>>> plot_correlation_heatmap(df_filtered_outliers, col_series=included_col, corr_method='spearman')
