# Preprocessing API

Source: `scripts/utils/preprocessing.py`

> Auto-generated from the bundled source. Re-run
> `python scripts/dev/generate_references.py` after changing the package.


Data inspection, cleaning, imputation, outlier handling, scaling, and encoding.

## Quick index

| Name | Summary |
| --- | --- |
| `check_data_information` | Check basic data information including data types, null values, duplicates, unique values, and various data characteristics like zero/negative values, empty strings, and cardinality |
| `drop_columns` | Drop specified columns from a DataFrame |
| `change_binary_dtype` | Convert binary columns between numerical (0/1) and categorical (No/Yes) representations |
| `handle_missing_values` | Handle missing values using various imputation strategies |
| `filter_outliers` | Unified function to detect and/or filter outliers using IQR or Z-score method |
| `feature_scaling` | General feature scaling function with flexible options. Supports applying different scaling methods to different columns |
| `feature_encoding` | General feature encoding function supporting ordinal, one-hot, mean, label, and frequency encoding |

### `check_data_information`

```python
def check_data_information(data: pd.DataFrame, cols: List[str]) -> pd.DataFrame
```

Check basic data information including data types, null values, duplicates, unique values,
and various data characteristics like zero/negative values, empty strings, and cardinality.

**Parameters**
data : pd.DataFrame
    The DataFrame to analyze
cols : List[str]
    List of column names to check

**Returns**
pd.DataFrame
    A DataFrame containing extended information about each column

**Examples**
>>> # Check information for all columns
>>> info_df = check_data_information(df, df.columns.tolist())

### `drop_columns`

```python
def drop_columns(data: pd.DataFrame, columns: Union[str, List[str]]) -> pd.DataFrame
```

Drop specified columns from a DataFrame.

**Parameters**
data : pd.DataFrame
    The DataFrame from which to drop columns
columns : Union[str, List[str]]
    Column name(s) to drop. Can be a single column name or a list of column names.

**Returns**
pd.DataFrame
    A new DataFrame with specified columns removed

**Examples**
>>> # Drop single column
>>> df_new = drop_columns(df, 'column_to_drop')

>>> # Drop multiple columns
>>> df_new = drop_columns(df, ['col1', 'col2', 'col3'])

### `change_binary_dtype`

```python
def change_binary_dtype(data: pd.DataFrame, column: str, target_type: str='categorical') -> pd.Series
```

Convert binary columns between numerical (0/1) and categorical (No/Yes) representations.

**Parameters**
data : pd.DataFrame
    The DataFrame containing the binary column
column : str
    The name of the column to convert
target_type : str, default='categorical'
    The desired data type for the column:
    - 'categorical': Convert 0/1 to 'No'/'Yes'
    - 'numerical': Convert 'No'/'Yes' back to 0/1

**Returns**
pd.Series
    The converted column

**Examples**
>>> # Convert numerical to categorical
>>> df['status'] = change_binary_dtype(df, 'status', target_type='categorical')
>>> # Result: 0 -> 'No', 1 -> 'Yes'

>>> # Convert categorical back to numerical
>>> df['status'] = change_binary_dtype(df, 'status', target_type='numerical')
>>> # Result: 'No' -> 0, 'Yes' -> 1

### `handle_missing_values`

```python
def handle_missing_values(data: pd.DataFrame, columns: List[str], strategy: str='median', imputer: Optional[Any]=None, n_neighbors: int=5) -> Tuple[pd.DataFrame, Optional[Any]]
```

Handle missing values using various imputation strategies.

**Parameters**
data : pd.DataFrame
    The dataframe to process
columns : List[str]
    List of column names to impute
strategy : str, default='median'
    Imputation method:
    - 'median', 'mean', 'mode': Simple imputation
    - 'ffill', 'bfill': Forward/backward fill
    - 'knn': K-Nearest Neighbors imputation (advanced)
    - 'remove': Drop rows with missing values
imputer : Optional[Any], default=None
    Pre-fitted imputer for test data (for 'knn')
n_neighbors : int, default=5
    Number of neighbors for KNN imputation

**Returns**
df_imputed : pd.DataFrame
    Dataframe with imputed values
imputer : Optional[Any]
    The fitted imputer (for 'knn' or 'iterative' methods)

**Example**
# Simple imputation
df_imputed, _ = handle_missing_values(df, columns=['col1', 'col2'], strategy='median')

# KNN imputation on training data
X_train_imputed, imputer = handle_missing_values(X_train, columns=['col1', 'col2'], 
                                                   strategy='knn', n_neighbors=5)

# Apply same imputer on test data (keep strategy='knn'; the default is 'median')
X_test_imputed, _ = handle_missing_values(X_test, columns=['col1', 'col2'], 
                                           strategy='knn', imputer=imputer)

### `filter_outliers`

```python
def filter_outliers(data: pd.DataFrame, columns: List[str], method: str='iqr', threshold: float=1.5, detect_only: bool=False, return_mask: bool=False, verbose: bool=True) -> Union[pd.DataFrame, Tuple[pd.DataFrame, np.ndarray]]
```

Unified function to detect and/or filter outliers using IQR or Z-score method.

**Parameters**
data : pd.DataFrame
    The dataframe to process
columns : List[str]
    List of column names to check for outliers
method : str, default='iqr'
    Method to detect outliers: 'iqr' or 'zscore'
threshold : float, default=1.5
    For IQR: multiplier for IQR range (default 1.5, typically 1.5-3)
    For Z-score: max absolute z-score (default 1.5, typically 2-3)
detect_only : bool, default=False
    If True, returns summary DataFrame of outliers (detection mode)
    If False, returns filtered dataframe (filtering mode)
return_mask : bool, default=False
    Only for filtering mode: if True, returns (filtered_data, mask)
verbose : bool, default=True
    Only for detection mode: if True, prints summary statistics

**Returns**
Detection mode (detect_only=True):
    pd.DataFrame: Summary with columns, bounds, counts, percentages

Filtering mode (detect_only=False):
    pd.DataFrame or tuple: Filtered data, or (filtered_data, mask) if return_mask=True

**Examples**
# Detection mode - analyze outliers
summary = filter_outliers(df, columns=['col1', 'col2'], method='iqr', detect_only=True)

# Filtering mode - remove outliers
df_clean = filter_outliers(df, columns=['col1', 'col2'], method='iqr', threshold=1.5)

# With mask for debugging
df_clean, mask = filter_outliers(df, columns=['col1'], return_mask=True)

### `feature_scaling`

```python
def feature_scaling(data: pd.DataFrame, scaling_config: Optional[Dict[str, Any]]=None, columns: Optional[List[str]]=None, method: str='standard', scaler: Optional[Union[Dict[str, Any], Any]]=None, apply_log: bool=False) -> Tuple[pd.DataFrame, Union[Dict[str, Any], Any]]
```

General feature scaling function with flexible options.
Supports applying different scaling methods to different columns.

**SCALING METHOD GUIDE**
1. 'standard' (StandardScaler): Mean=0, Std=1
   - Best for: Normally distributed data, models assuming normal distribution (linear/logistic regression)
   - Sensitive to outliers

2. 'minmax' (MinMaxScaler): Scale to [0, 1] range
   - Best for: Bounded features (counts, percentages), neural networks, image data
   - Very sensitive to outliers

3. 'robust' (RobustScaler): Uses median and IQR
   - Best for: Data with many outliers, skewed distributions
   - More resistant to outliers than standard/minmax

4. 'power' (PowerTransformer): Box-Cox or Yeo-Johnson transformation
   - Best for: Highly skewed data, making distributions more Gaussian
   - Automatically reduces skewness
   - Use 'yeo-johnson' for any data (handles zeros/negatives)
   - Use 'box-cox' only for strictly positive data

5. 'quantile' (QuantileTransformer): Maps to uniform or normal distribution
   - Best for: Heavily skewed/non-linear data, reducing impact of extreme outliers
   - Most robust to outliers
   - Output: 'normal' for Gaussian-like, 'uniform' for evenly spread [0,1]

**Parameters**
data : pd.DataFrame
    The dataframe to scale
scaling_config : Optional[Dict[str, Any]], optional
    Dictionary mapping scaling methods to column lists and options.
    Format: {
        'standard': {'columns': ['col1', 'col2'], 'apply_log': False},
        'minmax': {'columns': ['col3', 'col4'], 'apply_log': False},
        'robust': {'columns': ['col5', 'col6'], 'apply_log': True},
        'power': {'columns': ['col7'], 'method': 'yeo-johnson'},
        'quantile': {'columns': ['col8'], 'n_quantiles': 1000, 'output_distribution': 'normal'}
    }
    If provided, overrides 'columns', 'method', and 'apply_log' parameters.
columns : Optional[List[str]], optional
    List of column names to scale (used when scaling_config is None)
method : str, default='standard'
    Scaling method: 'standard', 'minmax', 'robust', 'power', or 'quantile' (used when scaling_config is None)
scaler : Optional[Union[Dict[str, Any], Any]], default=None
    For single method: sklearn scaler object
    For multiple methods: dict mapping method names to fitted scaler objects
    If None, fits new scaler(s) (for training data)
apply_log : bool, default=False
    Whether to apply log1p transformation before scaling (used when scaling_config is None)

**Returns**
df_scaled : pd.DataFrame
    Dataframe with scaled features
scaler : Union[Dict[str, Any], Any]
    For single method: the fitted scaler
    For multiple methods: dict of fitted scalers by method name

**Examples**
# Single method (legacy API - still works)
X_train_scaled, scaler = feature_scaling(
    X_train, 
    columns=['col1', 'col2'], 
    method='standard'
)
X_test_scaled, _ = feature_scaling(X_test, columns=['col1', 'col2'], scaler=scaler)

# Multiple methods (new API) - Training data
X_train_scaled, scalers = feature_scaling(
    X_train,
    scaling_config={
        'minmax': {
            'columns': ['amount_of_bathrooms', 'amount_of_bedrooms']
        },
        'standard': {
            'columns': ['land_size_sqm', 'building_size_sqm'],
            'apply_log': True
        },
        'power': {
            'columns': ['price'],
            'method': 'yeo-johnson'  # or 'box-cox' for positive-only data
        },
        'quantile': {
            'columns': ['area'],
            'n_quantiles': 1000,
            'output_distribution': 'normal'  # or 'uniform'
        }
    }
)

# Multiple methods - Test data (reuse fitted scalers)
X_test_scaled, _ = feature_scaling(
    X_test,
    scaling_config={
        'minmax': {'columns': ['amount_of_bathrooms', 'amount_of_bedrooms']},
        'standard': {'columns': ['land_size_sqm', 'building_size_sqm'], 'apply_log': True},
        'power': {'columns': ['price'], 'method': 'yeo-johnson'},
        'quantile': {'columns': ['area'], 'n_quantiles': 1000, 'output_distribution': 'normal'}
    },
    scaler=scalers
)

### `feature_encoding`

```python
def feature_encoding(data: pd.DataFrame, ordinal_columns: Optional[List[str]]=None, nominal_columns: Optional[List[str]]=None, mean_encoding_columns: Optional[List[str]]=None, binary_columns: Optional[List[str]]=None, frequency_columns: Optional[List[str]]=None, ordinal_categories: Optional[Dict[str, List[Any]]]=None, drop_first: bool=True, preserve_dtypes: bool=True, handle_unknown: str='error', target: Optional[pd.Series]=None, encoders: Optional[Dict[str, Any]]=None, mean_target_type: str='continuous', mean_smooth: Union[str, float]='auto', mean_cv: int=5) -> Tuple[pd.DataFrame, Dict[str, Any]]
```

General feature encoding function supporting ordinal, one-hot, mean, label, and frequency encoding.

Uses sklearn's TargetEncoder for mean encoding with built-in cross-fitting to prevent data leakage.
Label encoding for binary features (2 unique values) converts them to 0/1.
Frequency encoding replaces categories with their occurrence count from training data.

**Parameters**
data : pd.DataFrame
    The dataframe to encode
ordinal_columns : Optional[List[str]], optional
    List of column names for ordinal encoding
nominal_columns : Optional[List[str]], optional
    List of column names for one-hot encoding
mean_encoding_columns : Optional[List[str]], optional
    List of column names for mean encoding.
    Each category is replaced with the mean of the target variable for that category.
    Best for high-cardinality categorical features.
binary_columns : Optional[List[str]], optional
    List of column names for label encoding (binary features with only 2 unique values).
    Converts categories to 0/1 integers (e.g., 'yes'/'no' -> 1/0).
frequency_columns : Optional[List[str]], optional
    List of column names for frequency encoding.
    Each category is replaced with its frequency count from training data.
    Best for high-cardinality categorical features where count is informative.
ordinal_categories : Optional[Dict[str, List[Any]]], optional
    Dictionary mapping ordinal column names to their category order lists
drop_first : bool, default=True
    Whether to drop first category in one-hot encoding (avoid dummy trap)
preserve_dtypes : bool, default=True
    Whether to preserve original dtypes for non-encoded columns
handle_unknown : str, default='error'
    How to handle unknown categories: 'error', 'use_encoded_value', 'ignore'
target : Optional[pd.Series], default=None
    Target variable for mean encoding. REQUIRED when mean_encoding_columns is specified
    and encoders is None (i.e., for training data).
encoders : Optional[Dict[str, Any]], default=None
    Dictionary of pre-fitted encoders (for validation/test data).
    If provided, uses these encoders instead of fitting new ones.
    Keys include: 'ordinal_*', 'onehot_*', 'mean_encoder', 'binary_*', 'frequency_*'
mean_target_type : str, default='continuous'
    Type of target variable for mean encoding: 'continuous' for regression, 'binary' for classification.
mean_smooth : Union[str, float], default='auto'
    Smoothing parameter for mean encoding. 'auto' uses empirical Bayes, or provide a float.
mean_cv : int, default=5
    Number of cross-validation folds for internal cross-fitting to prevent data leakage.

**Returns**
Tuple[pd.DataFrame, Dict[str, Any]]
    Encoded dataframe and dictionary of fitted encoders

**Examples**
>>> # Fit on training data with all encoding types
>>> X_train_encoded, encoders = feature_encoding(
...     X_train,
...     ordinal_columns=['Class'],
...     nominal_columns=['BuildingType'],
...     mean_encoding_columns=['District'],
...     binary_columns=['sales_channel'],  # Label encode binary features
...     frequency_columns=['route', 'booking_origin'],  # Frequency encode high cardinality
...     ordinal_categories={'Class': ['Low', 'Medium', 'High']},
...     target=y_train
... )

>>> # Transform validation data using fitted encoders
>>> X_val_encoded, _ = feature_encoding(
...     X_val,
...     ordinal_columns=['Class'],
...     nominal_columns=['BuildingType'],
...     mean_encoding_columns=['District'],
...     binary_columns=['sales_channel'],
...     frequency_columns=['route', 'booking_origin'],
...     ordinal_categories={'Class': ['Low', 'Medium', 'High']},
...     encoders=encoders
... )
