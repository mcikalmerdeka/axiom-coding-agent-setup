"""NLP utilities for language detection and translation of text data."""

import os
import re
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Optional, Union, Set

import pandas as pd

# Optional translation dependencies
try:
    from deep_translator import GoogleTranslator
    DEEP_TRANSLATOR_AVAILABLE = True
except ImportError:
    DEEP_TRANSLATOR_AVAILABLE = False
    GoogleTranslator = None

try:
    from langid.langid import LanguageIdentifier, model
    LANGID_AVAILABLE = True
except ImportError:
    LANGID_AVAILABLE = False
    LanguageIdentifier = None
    model = None

try:
    from tenacity import (
        retry,
        retry_if_exception_type,
        stop_after_attempt,
        wait_exponential,
    )
    TENACITY_AVAILABLE = True
except ImportError:
    TENACITY_AVAILABLE = False

    # No-op fallback decorators if tenacity is not installed
    def retry(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

    def retry_if_exception_type(exc):
        return None

    def stop_after_attempt(n):
        return None

    def wait_exponential(*args, **kwargs):
        return None

from tqdm import tqdm

# ── Default export directory ───────────────────────────────────────────────────
DEFAULT_DATA_DIR = Path("data")

# ── Constants ──────────────────────────────────────────────────────────────────

# Default language codes to support in detection (empty = all languages)
# Common language codes: 'en' (English), 'es' (Spanish), 'fr' (French), 
# 'de' (German), 'it' (Italian), 'pt' (Portuguese), 'zh' (Chinese), 
# 'ja' (Japanese), 'ko' (Korean), 'ar' (Arabic), 'hi' (Hindi), etc.
DEFAULT_TARGET_LANGS: Set[str] = set()

# Fast English detection - if text matches this, skip expensive ML detection
# Matches: ASCII letters, numbers, common punctuation, spaces only
_ENGLISH_ONLY_RE = re.compile(r"^[\x00-\x7F]+$")

# Common English words - if text contains mostly these, likely English
_COMMON_ENGLISH_WORDS = frozenset([
    'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i',
    'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at',
    'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she',
    'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their',
    'what', 'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go',
    'me', 'when', 'make', 'can', 'like', 'time', 'no', 'just', 'him', 'know',
    'take', 'people', 'into', 'year', 'your', 'good', 'some', 'could', 'them',
    'see', 'other', 'than', 'then', 'now', 'look', 'only', 'come', 'its', 'over',
    'think', 'also', 'back', 'after', 'use', 'two', 'how', 'our', 'work',
    'first', 'well', 'way', 'even', 'new', 'want', 'because', 'any', 'these',
    'give', 'day', 'most', 'us', 'is', 'was', 'are', 'were', 'been', 'has',
    'had', 'did', 'does', 'doing', 'done', 'video', 'watch', 'subscribe',
    'channel', 'music', 'song', 'official', 'movie', 'film', 'trailer'
])

# Lazy-loaded langid identifiers. The constrained one is reused for explicit
# target sets; the all-language one is kept separate so a previous constrained
# call cannot leak into a later "detect all non-English" call.
_identifier: Optional[LanguageIdentifier] = None
_identifier_all: Optional[LanguageIdentifier] = None


def _require_detection_deps() -> None:
    """Raise a clear ImportError if language-detection dependencies are missing."""
    if not LANGID_AVAILABLE:
        raise ImportError(
            "Language detection requires the optional 'langid' package. "
            "Install with: uv sync --extra translate "
            "(or pip install data-science-utils[translate])"
        )


def _require_translation_deps() -> None:
    """Raise a clear ImportError if translation dependencies are missing.

    ``tenacity`` is optional: the module ships no-op fallback decorators.
    """
    if not DEEP_TRANSLATOR_AVAILABLE:
        raise ImportError(
            "Translation requires the optional 'deep-translator' package. "
            "Install with: uv sync --extra translate "
            "(or pip install data-science-utils[translate])"
        )


def _get_identifier(
    target_langs: Optional[Set[str]] = None,
) -> LanguageIdentifier:
    """Return a langid identifier, optionally constrained to target languages."""
    global _identifier, _identifier_all
    _require_detection_deps()

    if target_langs:
        if _identifier is None:
            _identifier = LanguageIdentifier.from_modelstring(model, norm_probs=True)
        _identifier.set_languages(list(target_langs) + ['en'])
        return _identifier

    if _identifier_all is None:
        _identifier_all = LanguageIdentifier.from_modelstring(model, norm_probs=True)
    return _identifier_all


def _get_script_pattern(languages: Optional[Set[str]] = None) -> re.Pattern:
    """
    Get regex pattern for script detection based on target languages.
    
    Parameters
    ----------
    languages : Set[str], optional
        Set of target language codes. If None or empty, returns empty pattern.
    
    Returns
    -------
    re.Pattern
        Regex pattern matching scripts of target languages
    """
    if not languages:
        return re.compile(r'(?!.*)')  # Pattern that never matches
    
    # Map common language codes to their Unicode ranges
    script_ranges = {
        # Indian scripts
        'hi': r'\u0900-\u097F',  # Devanagari
        'ml': r'\u0D00-\u0D7F',  # Malayalam
        'ta': r'\u0B80-\u0BFF',  # Tamil
        'te': r'\u0C00-\u0C7F',  # Telugu
        'kn': r'\u0C80-\u0CFF',  # Kannada
        'bn': r'\u0980-\u09FF',  # Bengali
        'gu': r'\u0A80-\u0AFF',  # Gujarati
        'pa': r'\u0A00-\u0A7F',  # Gurmukhi
        'or': r'\u0B00-\u0B7F',  # Oriya
        'as': r'\u0980-\u09FF',  # Assamese (shares Bengali script)
        'mr': r'\u0900-\u097F',  # Marathi (Devanagari)
        # East Asian scripts
        'zh': r'\u4E00-\u9FFF',  # Chinese
        'ja': r'\u3040-\u309F\u30A0-\u30FF',  # Japanese (Hiragana + Katakana)
        'ko': r'\uAC00-\uD7AF',  # Korean
        # Arabic script
        'ar': r'\u0600-\u06FF',  # Arabic
        'fa': r'\u0600-\u06FF',  # Persian
        'ur': r'\u0600-\u06FF',  # Urdu
        # Cyrillic script
        'ru': r'\u0400-\u04FF',  # Russian
        'uk': r'\u0400-\u04FF',  # Ukrainian
        # Greek script
        'el': r'\u0370-\u03FF',  # Greek
        # Thai script
        'th': r'\u0E00-\u0E7F',  # Thai
        # Hebrew script
        'he': r'\u0590-\u05FF',  # Hebrew
    }
    
    ranges = []
    for lang in languages:
        if lang in script_ranges:
            ranges.append(script_ranges[lang])
    
    if not ranges:
        return re.compile(r'(?!.*)')
    
    return re.compile(f'[{ "".join(ranges) }]')


# ── Core detection helpers ─────────────────────────────────────────────────────

def _is_obviously_english(text: str) -> bool:
    """
    Fast heuristics to detect obviously English text without ML.
    Returns True if text is very likely English (safe to skip ML detection).
    """
    if not isinstance(text, str) or not text.strip():
        return True  # Empty/missing = treat as English (no translation needed)
    
    text_lower = text.lower()
    words = text_lower.split()
    
    # If it only contains ASCII characters and spaces
    if _ENGLISH_ONLY_RE.match(text):
        # Further check: if it contains mostly common English words
        if len(words) == 0:
            return True
        
        # Count how many words are common English words
        english_word_count = sum(1 for word in words if word in _COMMON_ENGLISH_WORDS)
        
        # If >30% of words are common English words, likely English
        if english_word_count / len(words) > 0.3:
            return True

    return False


def _is_target_language(
    text: str, 
    target_langs: Set[str],
    identifier: LanguageIdentifier,
    confidence_threshold: float = 0.7
) -> bool:
    """
    Multi-stage detection:
      1. Fast ASCII/English check - skip ML for obviously English text
      2. Unicode script check - catch target language characters instantly
      3. Constrained langid ML model - for detection
    
    Parameters
    ----------
    text : str
        Text to analyze
    target_langs : Set[str]
        Set of target language codes to detect
    identifier : LanguageIdentifier
        Configured langid identifier
    confidence_threshold : float, optional
        Minimum confidence to classify as target language, default 0.7
    
    Returns
    -------
    bool
        True if text is in one of the target languages
    """
    if not isinstance(text, str) or not text.strip():
        return False

    # Stage 0: Fast English filter. Only use it in "all non-English" mode;
    # explicit target sets must go through detection even for short ASCII text.
    if not target_langs and _is_obviously_english(text):
        return False

    # Stage 1: Unicode fast path — if target script characters are present, done
    script_pattern = _get_script_pattern(target_langs)
    if script_pattern.search(text):
        return True

    # Stage 2: ML detection
    try:
        lang, confidence = identifier.classify(text)
        if confidence < confidence_threshold:
            return False
        if target_langs:
            return lang in target_langs
        return lang != "en"
    except Exception:
        return False


def _detect_batch(
    texts: list[tuple[str, Set[str], float]], 
    identifier: LanguageIdentifier
) -> list[tuple[str, bool]]:
    """
    Process a batch of texts for language detection.
    Used for parallel processing.
    
    Parameters
    ----------
    texts : list[tuple[str, Set[str], float]]
        List of (text, target_langs, confidence_threshold) tuples
    identifier : LanguageIdentifier
        Configured langid identifier
    
    Returns
    -------
    list[tuple[str, bool]]
        List of (text, is_target_lang) results
    """
    return [
        (text, _is_target_language(text, target_langs, identifier, threshold))
        for text, target_langs, threshold in texts
    ]


# ── Row-level detection with deduplication ────────────────────────────────────

def _row_contains_target_language(
    row: pd.Series, 
    columns: list[str],
    target_langs: Set[str],
    identifier: LanguageIdentifier,
    confidence_threshold: float = 0.7
) -> bool:
    """Return True if any of the specified columns contain target language text."""
    return any(
        _is_target_language(row[col], target_langs, identifier, confidence_threshold)
        for col in columns
        if col in row.index and pd.notnull(row[col])
    )


def detect_language_rows(
    df: pd.DataFrame,
    columns: list[str],
    target_langs: Optional[Union[list[str], Set[str], str]] = None,
    confidence_threshold: float = 0.7,
    use_parallel: bool = True,
    max_workers: Optional[int] = None,
    detection_batch_size: int = 1000,
    export: bool = False,
    data_dir: Path = DEFAULT_DATA_DIR,
    filename_prefix: Optional[str] = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
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
    """
    # Normalize target_langs to a set
    if target_langs is None:
        # Detect all languages (except English)
        target_langs = set()
    elif isinstance(target_langs, str):
        target_langs = {target_langs}
    elif isinstance(target_langs, list):
        target_langs = set(target_langs)
    
    target_lang_label = ', '.join(sorted(target_langs)) if target_langs else 'non-English'

    # Collect all unique non-null strings across all target columns
    print(f"Collecting unique texts from columns: {columns}...")
    all_texts: set[str] = set()
    for col in columns:
        if col in df.columns:
            all_texts.update(df[col].dropna().unique())

    total_unique = len(all_texts)
    print(f"Found {total_unique:,} unique texts to check")

    # No texts means detection needs no optional dependencies at all.
    if total_unique == 0:
        return df.iloc[0:0], df

    # Detection needs langid only; translation dependencies are not required.
    _require_detection_deps()

    # Configure the identifier with target languages + English.
    identifier = _get_identifier(target_langs)

    # Prepare data for detection
    text_list = list(all_texts)
    
    if use_parallel and total_unique > 100:
        # Parallel detection for large datasets
        print(f"Running parallel detection with {max_workers or 'auto'} workers...")
        
        # Split into batches
        batches = [
            [(text, target_langs, confidence_threshold) for text in text_list[i:i + detection_batch_size]]
            for i in range(0, len(text_list), detection_batch_size)
        ]
        
        text_cache: dict[str, bool] = {}
        
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Submit all batches
            futures = {executor.submit(_detect_batch, batch, identifier): i for i, batch in enumerate(batches)}
            
            # Collect results with progress bar
            with tqdm(total=len(batches), desc="Detection batches") as pbar:
                for future in as_completed(futures):
                    batch_idx = futures[future]
                    try:
                        results = future.result()
                        for text, is_target in results:
                            text_cache[text] = is_target
                    except Exception as e:
                        print(f"Batch {batch_idx} failed: {e}")
                    pbar.update(1)
    else:
        # Sequential detection for small datasets
        print("Running sequential detection...")
        text_cache: dict[str, bool] = {}
        for text in tqdm(text_list, desc="Detecting languages"):
            text_cache[text] = _is_target_language(text, target_langs, identifier, confidence_threshold)

    # Build mask using cached results
    def _row_is_target(row: pd.Series) -> bool:
        return any(
            text_cache.get(row[col], False)
            for col in columns
            if col in row.index and pd.notnull(row[col])
        )

    print("Classifying rows...")
    tqdm.pandas(desc="Classifying rows")
    mask = df.apply(_row_is_target, axis=1)

    # Use df.index explicitly to prevent index misalignment
    target_lang_df = df.loc[mask]
    other_df = df.loc[~mask]
    
    print(f"Results: {len(target_lang_df):,} {target_lang_label} rows, {len(other_df):,} others")
    
    # Export to CSV if requested
    if export:
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename prefix with timestamp if not provided
        if filename_prefix is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            prefix = f"language_detection_{timestamp}"
        else:
            prefix = filename_prefix
        
        target_path = data_dir / f"{prefix}_target.csv"
        other_path = data_dir / f"{prefix}_other.csv"
        
        print(f"\n── Exporting to CSV ──")
        target_lang_df.to_csv(target_path, index=False)
        other_df.to_csv(other_path, index=False)
        print(f"   Target rows saved to: {target_path}")
        print(f"   Other rows saved to: {other_path}")
        print(f"\nTo load later:")
        print(f"   target_df = pd.read_csv('{target_path}')")
        print(f"   other_df = pd.read_csv('{other_path}')")

    return target_lang_df, other_df


# ── Translation helpers ────────────────────────────────────────────────────────

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
def _translate_batch_with_retry(
    texts: list[str],
    src: str = "auto",
    dest: str = "en",
) -> list[str]:
    """Translate a list of strings with automatic retry on failure."""
    return GoogleTranslator(source=src, target=dest).translate_batch(texts)


def translate_series(
    series: pd.Series,
    src: str = "auto",
    dest: str = "en",
    batch_size: int = 50,
    inter_batch_delay: float = 0.5,
) -> pd.Series:
    """
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
    """
    _require_translation_deps()
    result = series.copy()

    # Work only with non-null values
    non_null_mask = series.notna()
    unique_values = series[non_null_mask].unique().tolist()

    if not unique_values:
        return result

    # Translate only unique values
    translation_map: dict[str, str] = {}
    batches = [
        unique_values[i : i + batch_size]
        for i in range(0, len(unique_values), batch_size)
    ]

    for batch in tqdm(batches, desc=f"Translating ({src}→{dest})"):
        try:
            translated = _translate_batch_with_retry(batch, src=src, dest=dest)
            translation_map.update(dict(zip(batch, translated)))
        except Exception as e:
            print(f"[Warning] Batch failed after retries: {e}. Keeping originals.")
            translation_map.update({text: text for text in batch})  # fallback

        if inter_batch_delay > 0:
            time.sleep(inter_batch_delay)

    # Map translations back to the full Series
    result[non_null_mask] = series[non_null_mask].map(translation_map)
    return result


def translate_dataframe(
    df: pd.DataFrame,
    columns: list[str],
    src: str = "auto",
    dest: str = "en",
    batch_size: int = 50,
    inter_batch_delay: float = 0.5,
    inplace: bool = False,
) -> pd.DataFrame:
    """
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
    """
    _require_translation_deps()
    out = df if inplace else df.copy()

    for col in columns:
        if col not in out.columns:
            print(f"[Warning] Column '{col}' not found, skipping.")
            continue
        print(f"\n── Column: '{col}' ──")
        out[col] = translate_series(
            out[col],
            src=src,
            dest=dest,
            batch_size=batch_size,
            inter_batch_delay=inter_batch_delay,
        )

    return out


def run_translation_pipeline(
    df: pd.DataFrame,
    columns: list[str],
    target_langs: Optional[Union[list[str], Set[str], str]] = None,
    dest: str = "en",
    use_parallel: bool = True,
    max_workers: Optional[int] = None,
    export: bool = False,
    data_dir: Path = DEFAULT_DATA_DIR,
    filename_prefix: Optional[str] = None,
) -> pd.DataFrame:
    """
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
    """
    _require_detection_deps()
    print("── Step 1: Language Detection ──")
    target_lang_df, other_df = detect_language_rows(
        df, 
        columns,
        target_langs=target_langs,
        use_parallel=use_parallel,
        max_workers=max_workers,
        export=export,
        data_dir=data_dir,
        filename_prefix=filename_prefix,
    )
    
    target_lang_label = ', '.join(sorted(target_langs)) if isinstance(target_langs, (list, set)) else (target_langs or 'non-English')

    if len(target_lang_df) == 0:
        print(f"No {target_lang_label} rows found. Returning original DataFrame.")
        if export:
            data_dir.mkdir(parents=True, exist_ok=True)
            if filename_prefix is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                prefix = f"translation_{timestamp}"
            else:
                prefix = filename_prefix
            final_path = data_dir / f"{prefix}_translated.csv"
            df.to_csv(final_path, index=False)
            print(f"   Original data saved to: {final_path}")
        return df

    print(f"\n── Step 2: Translation ──")
    translated_df = translate_dataframe(target_lang_df, columns=columns, src="auto", dest=dest)

    print("\n── Step 3: Recombine ──")
    final_df = (
        pd.concat([translated_df, other_df])
        .sort_index()  # restore original row order
        .reset_index(drop=True)
    )
    print(f"   Final shape: {final_df.shape}")
    
    # Export final dataframe if requested
    if export:
        data_dir.mkdir(parents=True, exist_ok=True)
        
        if filename_prefix is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            prefix = f"translation_{timestamp}"
        else:
            prefix = filename_prefix
        
        final_path = data_dir / f"{prefix}_translated.csv"
        final_df.to_csv(final_path, index=False)
        
        print(f"\n── Export Complete ──")
        print(f"   Final translated data saved to: {final_path}")
        print(f"\nTo load this data later:")
        print(f"   import pandas as pd")
        print(f"   final_df = pd.read_csv('{final_path}')")
    
    return final_df


# ── Alternative: Skip detection and translate everything ───────────────────────

def translate_all_text(
    df: pd.DataFrame,
    columns: list[str],
    dest: str = "en",
    batch_size: int = 50,
    inter_batch_delay: float = 0.5,
    export: bool = False,
    data_dir: Path = DEFAULT_DATA_DIR,
    filename_prefix: Optional[str] = None,
) -> pd.DataFrame:
    """
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
    """
    _require_translation_deps()
    result = df.copy()
    
    for col in columns:
        if col not in result.columns:
            print(f"[Warning] Column '{col}' not found, skipping.")
            continue
        print(f"\n── Translating column: '{col}' ──")
        result[col] = translate_series(
            result[col],
            src="auto",
            dest=dest,
            batch_size=batch_size,
            inter_batch_delay=inter_batch_delay,
        )
    
    # Export if requested
    if export:
        data_dir.mkdir(parents=True, exist_ok=True)
        
        if filename_prefix is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            prefix = f"translation_{timestamp}"
        else:
            prefix = filename_prefix
        
        final_path = data_dir / f"{prefix}_translated.csv"
        result.to_csv(final_path, index=False)
        
        print(f"\n── Export Complete ──")
        print(f"   Translated data saved to: {final_path}")
        print(f"\nTo load this data later:")
        print(f"   import pandas as pd")
        print(f"   final_df = pd.read_csv('{final_path}')")
    
    return result
