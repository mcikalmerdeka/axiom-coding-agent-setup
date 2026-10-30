# Translation API

Source: `scripts/utils/translation_utils.py`

> Auto-generated from the bundled source. Re-run
> `python scripts/dev/generate_references.py` after changing the package.


Language detection, row filtering, and batched translation helpers.

## Quick index

| Name | Summary |
| --- | --- |
| `detect_language_rows` | Split a DataFrame into rows containing target language(s) and other rows |
| `translate_series` | Translate a pandas Series efficiently |
| `translate_dataframe` | Translate selected columns of a DataFrame in-place or as a copy |
| `run_translation_pipeline` | Full pipeline: detect and split rows containing target language(s), translate them, then recombine into a single DataFrame |
| `translate_all_text` | Translate ALL text without language detection |

### `detect_language_rows`

```python
def detect_language_rows(df: pd.DataFrame, columns: list[str], target_langs: Optional[Union[list[str], Set[str], str]]=None, confidence_threshold: float=0.7, use_parallel: bool=True, max_workers: Optional[int]=None, detection_batch_size: int=1000, export: bool=False, data_dir: Path=DEFAULT_DATA_DIR, filename_prefix: Optional[str]=None) -> tuple[pd.DataFrame, pd.DataFrame]
```

Split a DataFrame into rows containing target language(s) and other rows.

Optimized version with:
- Fast English pre-filtering (skips ML for obviously English text)
- Parallel processing support
- Progress tracking
- Optional CSV export

Parameters
----------
df : pd.DataFrame
    Source DataFrame
columns : list[str]
    Columns to inspect for language detection
target_langs : list[str], Set[str], or str, optional
    Language code(s) to detect. Can be:
    - Single language: 'hi' (Hindi)
    - List: ['hi', 'ml', 'ta'] (Hindi, Malayalam, Tamil)
    - Set: {'hi', 'ml'}
    - None: detects all non-English languages
    Default None (detect all non-English)
confidence_threshold : float, optional
    Minimum langid confidence to classify as target language (0–1), default 0.7
use_parallel : bool, optional
    Use parallel processing for detection, default True
max_workers : int, optional
    Number of parallel workers (None = use all CPUs)
detection_batch_size : int, optional
    Batch size for parallel detection, default 1000
export : bool, optional
    Export results to CSV files, default False
data_dir : Path, optional
    Directory to save CSV files, default "data"
filename_prefix : str, optional
    Prefix for CSV filenames (default: auto-generated with timestamp)

Returns
-------
tuple[pd.DataFrame, pd.DataFrame]
    (target_lang_df, other_df) — both preserve the original index

Examples
--------
>>> # Detect Hindi text
>>> hindi_df, other_df = detect_language_rows(df, columns=['title'], target_langs='hi')

>>> # Detect multiple Indian languages
>>> indian_langs = ['hi', 'ml', 'ta', 'te', 'kn', 'bn']
>>> indian_df, other_df = detect_language_rows(
...     df,
...     columns=['title', 'description'],
...     target_langs=indian_langs,
...     use_parallel=True
... )

>>> # Detect any non-English language
>>> non_english_df, english_df = detect_language_rows(
...     df,
...     columns=['text'],
...     target_langs=None  # detects all languages
... )

>>> # All columns at once with export
>>> target_df, other_df = detect_language_rows(
...     df,
...     columns=['title', 'tags', 'description'],
...     target_langs=['es', 'fr', 'de'],  # Spanish, French, German
...     use_parallel=True,
...     max_workers=4,
...     export=True,
...     filename_prefix="multilingual_data"
... )

>>> # Load exported data later
>>> target_df = pd.read_csv("data/multilingual_data_target.csv")
>>> other_df = pd.read_csv("data/multilingual_data_other.csv")

### `translate_series`

```python
def translate_series(series: pd.Series, src: str='auto', dest: str='en', batch_size: int=50, inter_batch_delay: float=0.5) -> pd.Series
```

Translate a pandas Series efficiently.

Parameters
----------
series : pd.Series
    Series containing text to translate
src : str, optional
    Source language code, default 'auto' (auto-detect)
dest : str, optional
    Target language code, default 'en' (English)
batch_size : int, optional
    Number of strings per API call, default 50
inter_batch_delay : float, optional
    Seconds to wait between batches (rate-limit courtesy), default 0.5

Returns
-------
pd.Series
    Series with translated text

### `translate_dataframe`

```python
def translate_dataframe(df: pd.DataFrame, columns: list[str], src: str='auto', dest: str='en', batch_size: int=50, inter_batch_delay: float=0.5, inplace: bool=False) -> pd.DataFrame
```

Translate selected columns of a DataFrame in-place or as a copy.

Parameters
----------
df : pd.DataFrame
    Source DataFrame
columns : list[str]
    Column names to translate
src : str, optional
    Source language code, default 'auto' (auto-detect)
dest : str, optional
    Target language code, default 'en' (English)
batch_size : int, optional
    Strings per API call, default 50
inter_batch_delay : float, optional
    Seconds to wait between batches (rate-limit courtesy), default 0.5
inplace : bool, optional
    Modify df directly if True, otherwise return a copy, default False

Returns
-------
pd.DataFrame
    DataFrame with translated columns

Examples
--------
>>> columns_to_translate = ["title", "description"]
>>> translated_df = translate_dataframe(
...     df,
...     columns=columns_to_translate,
...     src="auto",   # auto-detect source language
...     dest="en",    # translate to English
... )
>>> 
>>> # Translate to Spanish instead
>>> spanish_df = translate_dataframe(
...     df,
...     columns=columns_to_translate,
...     src="en",     # from English
...     dest="es",    # to Spanish
... )

### `run_translation_pipeline`

```python
def run_translation_pipeline(df: pd.DataFrame, columns: list[str], target_langs: Optional[Union[list[str], Set[str], str]]=None, dest: str='en', use_parallel: bool=True, max_workers: Optional[int]=None, export: bool=False, data_dir: Path=DEFAULT_DATA_DIR, filename_prefix: Optional[str]=None) -> pd.DataFrame
```

Full pipeline: detect and split rows containing target language(s), translate them,
then recombine into a single DataFrame.

This is a thin orchestrator — each step stays independent and debuggable.

Parameters
----------
df : pd.DataFrame
    Source DataFrame
columns : list[str]
    Columns to check for target languages and translate
target_langs : list[str], Set[str], or str, optional
    Language code(s) to detect before translating. Can be:
    - Single language: 'hi' (Hindi)
    - List: ['hi', 'ml', 'ta'] (Hindi, Malayalam, Tamil)
    - Set: {'hi', 'ml'}
    - None: detects all non-English languages
    Default None (detect all non-English)
dest : str, optional
    Target language code, default 'en' (English)
use_parallel : bool, optional
    Use parallel processing for detection, default True
max_workers : int, optional
    Number of parallel workers (None = use all CPUs)
export : bool, optional
    Export results to CSV files, default False
data_dir : Path, optional
    Directory to save CSV files, default "data"
filename_prefix : str, optional
    Prefix for CSV filenames (default: auto-generated with timestamp)

Returns
-------
pd.DataFrame
    Final DataFrame with all rows, target language rows translated

Examples
--------
>>> # Detect and translate Hindi text
>>> final_df = run_translation_pipeline(df, columns=['title'], target_langs='hi')

>>> # Detect multiple languages with parallel processing and export
>>> final_df = run_translation_pipeline(
...     df,
...     columns=['title', 'description'],
...     target_langs=['es', 'fr', 'de'],  # Spanish, French, German
...     use_parallel=True,
...     max_workers=4,
...     export=True,
...     filename_prefix="multilingual_translated"
... )

>>> # Detect any non-English language
>>> final_df = run_translation_pipeline(
...     df,
...     columns=['text'],
...     target_langs=None  # detect all non-English
... )

>>> # Load final translated data later
>>> final_df = pd.read_csv("data/multilingual_translated_translated.csv")

### `translate_all_text`

```python
def translate_all_text(df: pd.DataFrame, columns: list[str], dest: str='en', batch_size: int=50, inter_batch_delay: float=0.5, export: bool=False, data_dir: Path=DEFAULT_DATA_DIR, filename_prefix: Optional[str]=None) -> pd.DataFrame
```

Translate ALL text without language detection.

Use this if:
- You know most of your data needs translation
- Detection is taking too long
- You want to translate everything as a batch

Much faster than detection + translation, but will translate text already in target language.

Parameters
----------
df : pd.DataFrame
    Source DataFrame
columns : list[str]
    Column names to translate
dest : str, optional
    Target language code, default 'en' (English)
batch_size : int, optional
    Strings per API call, default 50
inter_batch_delay : float, optional
    Seconds to wait between batches, default 0.5
export : bool, optional
    Export results to CSV files, default False
data_dir : Path, optional
    Directory to save CSV files, default "data"
filename_prefix : str, optional
    Prefix for CSV filenames (default: auto-generated with timestamp)

Returns
-------
pd.DataFrame
    DataFrame with all specified columns translated

Examples
--------
>>> # Fastest option - skip detection entirely
>>> final_df = translate_all_text(
...     df, 
...     columns=['title', 'description'],
...     dest='en',
...     export=True,
...     filename_prefix="all_translated"
... )

>>> # Translate to Spanish
>>> spanish_df = translate_all_text(
...     df,
...     columns=['text'],
...     dest='es'
... )

>>> # Load later
>>> final_df = pd.read_csv("data/all_translated_translated.csv")
