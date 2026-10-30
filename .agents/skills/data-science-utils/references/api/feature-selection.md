# Feature selection API

Source: `scripts/utils/feature_selection.py`

> Auto-generated from the bundled source. Re-run
> `python scripts/dev/generate_references.py` after changing the package.


Correlation analysis, categorical association tests, VIF, and univariate importance.

## Quick index

| Name | Summary |
| --- | --- |
| `calculate_correlation_tabular` | Calculate and display correlation analysis in tabular form for feature-to-feature, feature-to-target correlations, or both |
| `analyze_categorical_relationships` | Analyze relationships between categorical features and target using Chi-Square test and calculate effect sizes using Cramér's V |
| `calculate_vif` | Calculate VIF for each feature in the dataset |
| `calculate_feature_importance` | Calculate feature importance scores using different statistical methods for classification or regression |

### `calculate_correlation_tabular`

```python
def calculate_correlation_tabular(df: pd.DataFrame, target_col: str, method: str='spearman', corr_type: str='feature_feature') -> Union[pd.DataFrame, Tuple[pd.DataFrame, pd.DataFrame]]
```

Calculate and display correlation analysis in tabular form for feature-to-feature,
feature-to-target correlations, or both.

**Parameters**
df : pandas.DataFrame
    Input DataFrame containing the features and target variable
target_col : str
    Name of the target column in the DataFrame
method : str, optional (default='spearman')
    Correlation method to use. Options include:
    - 'pearson': standard correlation coefficient
    - 'spearman': Spearman rank correlation
    - 'kendall': Kendall Tau correlation coefficient
corr_type : str, optional (default='feature_feature')
    Type of correlation analysis to perform:
    - 'feature_feature': correlations between all features
    - 'feature_target': correlations between features and target variable
    - 'both': display both feature-feature and feature-target correlations

**Examples**
>>> # Calculate feature-to-feature correlations
>>> feature_feature_df = calculate_correlation_tabular(df, target_col='target', method='spearman', corr_type='feature_feature')

>>> # Calculate feature-to-target correlations
>>> feature_target_df = calculate_correlation_tabular(df, target_col='target', method='spearman', corr_type='feature_target')

>>> # Calculate both feature-to-feature and feature-to-target correlations
>>> feature_feature_df, feature_target_df = calculate_correlation_tabular(df, target_col='target', method='spearman', corr_type='both')

**Returns**
tuple or pandas.DataFrame
    If corr_type is 'both':
        Returns a tuple (feature_feature_df, feature_target_df)
    Otherwise:
        Returns a single DataFrame containing the correlation analysis results

    DataFrame columns for feature_feature:
        - 'A': First feature name
        - 'B': Second feature name
        - 'Corr Value': Absolute correlation value
        - 'Corr Type': 'Positive' or 'Negative'
    DataFrame columns for feature_target:
        - 'Feature': Feature name
        - 'Corr Value': Absolute correlation value
        - 'Corr Type': 'Positive' or 'Negative'

**Raises**
ValueError
    If corr_type is not 'feature_feature', 'feature_target', or 'both'

### `analyze_categorical_relationships`

```python
def analyze_categorical_relationships(df: pd.DataFrame, features: List[str], target: str, alpha: float=0.05) -> pd.DataFrame
```

Analyze relationships between categorical features and target using Chi-Square test
and calculate effect sizes using Cramér's V.

**Parameters**
df : pandas DataFrame
    The input dataframe containing the features and target
features : List[str]
    List of categorical feature names
target : str
    Name of the target variable
alpha : float, optional (default=0.05)
    Significance level for the chi-square test

**Examples**
>>> # Analyze relationships between categorical features and target
>>> results = analyze_categorical_relationships(df, features=['feature1', 'feature2'], target='target', alpha=0.05)

**Returns**
pandas DataFrame
    Summary of the analysis including chi-square statistics, p-values, and effect sizes

### `calculate_vif`

```python
def calculate_vif(df: pd.DataFrame, target_col: str, high_threshold: int=10, moderate_threshold: int=5) -> pd.DataFrame
```

Calculate VIF for each feature in the dataset.

**Parameters**
df : pd.DataFrame
    Input DataFrame containing the features and target variable
target_col : str
    Name of target column to exclude
high_threshold : int, optional, default=10
    Threshold for high multicollinearity
moderate_threshold : int, optional, default=5
    Threshold for moderate multicollinearity

**Examples**
>>> # Calculate VIF for the dataset
>>> vif_data = calculate_vif(df, target_col='target', high_threshold=10, moderate_threshold=5)

**Returns**
pd.DataFrame
    DataFrame with VIF scores

### `calculate_feature_importance`

```python
def calculate_feature_importance(X: pd.DataFrame, y: pd.Series, task: str='classification', method: str='mutual_info', k: Union[int, str]='all', random_state: int=42) -> pd.DataFrame
```

Calculate feature importance scores using different statistical methods for classification or regression.

**Parameters**
X : pd.DataFrame
    Feature matrix
y : pd.Series
    Target variable
task : str, optional, default='classification'
    Task type ('classification' or 'regression')
method : str, optional, default='mutual_info'
    Method for feature selection ('mutual_info', 'anova', 'chi2' for classification; 'f_regression', 'mutual_info' for regression')
k : int or 'all', optional, default='all'
    Number of top features to select. Use 'all' to see scores for all features.
random_state : int, optional, default=42
    Random seed used by mutual-information estimators. Ignored by the
    deterministic ANOVA, chi-square, and F-regression methods.

**Examples**
>>> # Calculate feature importance scores for classification
>>> feature_importance = calculate_feature_importance(X=X, y=y, task='classification', method='mutual_info', k='all')
>>> display(feature_importance.iloc[:15].reset_index(drop=True))

>>> # Calculate feature importance scores for regression
>>> feature_importance = calculate_feature_importance(X=X, y=y, task='regression', method='f_regression', k='all')
>>> display(feature_importance.iloc[:15].reset_index(drop=True))

**Returns**
pd.DataFrame
    DataFrame with feature names, scores, and p-values (if applicable)
