# Text processing API

Source: `scripts/utils/text_preprocessing.py`

> Auto-generated from the bundled source. Re-run
> `python scripts/dev/generate_references.py` after changing the package.


Text cleaning, tokenization, lemmatization, stemming, word clouds, and frequency analysis.

## Quick index

| Name | Summary |
| --- | --- |
| `TextPreprocessor` | A comprehensive text preprocessing class for NLP tasks |
| `TextVisualizer` | A class for creating word clouds and analyzing text data |
| `quick_clean` | Quickly clean text with common preprocessing steps |
| `extract_ngrams` | Extract n-grams from text |
| `get_text_stats` | Calculate basic text statistics for DataFrame columns |

## class `TextPreprocessor`

```python
TextPreprocessor(language: str='english', custom_stopwords: Optional[Set[str]]=None)
```

A comprehensive text preprocessing class for NLP tasks.

This class provides methods for cleaning, normalizing, and transforming
text data. It supports various preprocessing steps including HTML removal,
URL/email removal, normalization, tokenization, lemmatization, and stemming.

**Parameters**
language : str, default='english'
    Language for stopwords (e.g., 'english', 'french', 'german')
custom_stopwords : Optional[Set[str]], default=None
    Additional stopwords to remove beyond the language defaults

**Examples**
>>> # Initialize preprocessor with default settings
>>> preprocessor = TextPreprocessor()

>>> # Initialize with custom stopwords
>>> preprocessor = TextPreprocessor(
...     language='english',
...     custom_stopwords={'custom', 'words', 'here'}
... )

>>> # Process single text
>>> clean_text = preprocessor.process_text("Your text here with URLs http://example.com")

>>> # Process DataFrame columns
>>> df_clean = preprocessor.preprocess_dataframe(df, columns=['title', 'description'])

### `TextPreprocessor.add_stopwords`

```python
def add_stopwords(words: Union[str, List[str], Set[str]]) -> None
```

Add custom stopwords to the existing set.

**Parameters**
words : Union[str, List[str], Set[str]]
    Stopword(s) to add. Can be a single word, list, or set.

**Examples**
>>> preprocessor = TextPreprocessor()
>>> preprocessor.add_stopwords('custom')
>>> preprocessor.add_stopwords(['word1', 'word2', 'word3'])

### `TextPreprocessor.remove_stopwords`

```python
def remove_stopwords(words: Union[str, List[str], Set[str]]) -> None
```

Remove words from the stopwords set.

**Parameters**
words : Union[str, List[str], Set[str]]
    Stopword(s) to remove. Can be a single word, list, or set.

**Examples**
>>> preprocessor = TextPreprocessor()
>>> preprocessor.remove_stopwords('not')  # Keep negations
>>> preprocessor.remove_stopwords(['good', 'bad'])  # Keep sentiment words

### `TextPreprocessor.replace_newlines`

```python
def replace_newlines(text: str) -> str
```

Replace newline characters and escaped newlines with spaces.

**Parameters**
text : str
    Input text to process

**Returns**
str
    Text with newlines replaced by spaces

**Examples**
>>> preprocessor = TextPreprocessor()
>>> preprocessor.replace_newlines("Hello\nWorld\n\nTest")
'Hello World Test'

### `TextPreprocessor.remove_html`

```python
def remove_html(text: str) -> str
```

Remove HTML tags from text using BeautifulSoup.

**Parameters**
text : str
    Input text containing HTML

**Returns**
str
    Text with HTML tags removed

**Examples**
>>> preprocessor = TextPreprocessor()
>>> preprocessor.remove_html("<p>Hello <b>World</b></p>")
'Hello World'

### `TextPreprocessor.expand_contractions`

```python
def expand_contractions(text: str) -> str
```

Expand contractions (e.g., "don't" -> "do not").

**Parameters**
text : str
    Input text with contractions

**Returns**
str
    Text with contractions expanded

**Examples**
>>> preprocessor = TextPreprocessor()
>>> preprocessor.expand_contractions("I don't think it's working")
"I do not think it is working"

### `TextPreprocessor.remove_accents`

```python
def remove_accents(text: str) -> str
```

Remove accented characters by converting to ASCII.

**Parameters**
text : str
    Input text with accented characters

**Returns**
str
    Text with accents removed

**Examples**
>>> preprocessor = TextPreprocessor()
>>> preprocessor.remove_accents("café résumé")
'cafe resume'

### `TextPreprocessor.remove_urls`

```python
def remove_urls(text: str) -> str
```

Remove URLs from text.

**Parameters**
text : str
    Input text containing URLs

**Returns**
str
    Text with URLs removed

**Examples**
>>> preprocessor = TextPreprocessor()
>>> preprocessor.remove_urls("Visit http://example.com for more info")
'Visit  for more info'

### `TextPreprocessor.remove_emails`

```python
def remove_emails(text: str) -> str
```

Remove email addresses from text.

**Parameters**
text : str
    Input text containing email addresses

**Returns**
str
    Text with emails removed

**Examples**
>>> preprocessor = TextPreprocessor()
>>> preprocessor.remove_emails("Contact me at test@example.com")
'Contact me at '

### `TextPreprocessor.remove_social_handles`

```python
def remove_social_handles(text: str) -> str
```

Remove social media handles (@mentions and #hashtags).

**Parameters**
text : str
    Input text containing handles

**Returns**
str
    Text with social handles removed

**Examples**
>>> preprocessor = TextPreprocessor()
>>> preprocessor.remove_social_handles("Follow @user and check #hashtag")
'Follow  and check '

### `TextPreprocessor.remove_special_chars`

```python
def remove_special_chars(text: str, keep_punctuation: bool=False) -> str
```

Remove special characters and optionally keep punctuation.

**Parameters**
text : str
    Input text to clean
keep_punctuation : bool, default=False
    If True, keeps basic punctuation marks (. , ! ? -)

**Returns**
str
    Cleaned text with special characters removed

**Examples**
>>> preprocessor = TextPreprocessor()
>>> preprocessor.remove_special_chars("Hello! How are you? @#$%")
'Hello How are you '
>>> preprocessor.remove_special_chars("Hello! How are you?", keep_punctuation=True)
'Hello! How are you?'

### `TextPreprocessor.correct_spelling`

```python
def correct_spelling(text: str) -> str
```

Correct spelling using TextBlob.

Note: This is computationally expensive and should be used sparingly.

**Parameters**
text : str
    Input text with potential spelling errors

**Returns**
str
    Text with corrected spelling

**Examples**
>>> preprocessor = TextPreprocessor()
>>> preprocessor.correct_spelling("Ths is a tst sentnce")
'This is a test sentence'

### `TextPreprocessor.tokenize`

```python
def tokenize(text: str) -> List[str]
```

Tokenize text into individual words.

**Parameters**
text : str
    Input text to tokenize

**Returns**
List[str]
    List of tokens

**Examples**
>>> preprocessor = TextPreprocessor()
>>> preprocessor.tokenize("Hello world test")
['Hello', 'world', 'test']

### `TextPreprocessor.remove_stopwords_from_tokens`

```python
def remove_stopwords_from_tokens(tokens: List[str]) -> List[str]
```

Remove stopwords from a list of tokens.

**Parameters**
tokens : List[str]
    List of word tokens

**Returns**
List[str]
    Tokens with stopwords removed

**Examples**
>>> preprocessor = TextPreprocessor()
>>> preprocessor.remove_stopwords_from_tokens(['the', 'quick', 'brown', 'fox'])
['quick', 'brown', 'fox']

### `TextPreprocessor.lemmatize_tokens`

```python
def lemmatize_tokens(tokens: List[str]) -> List[str]
```

Lemmatize a list of tokens.

**Parameters**
tokens : List[str]
    List of word tokens

**Returns**
List[str]
    Lemmatized tokens

**Examples**
>>> preprocessor = TextPreprocessor()
>>> preprocessor.lemmatize_tokens(['running', 'better', 'dogs'])
['running', 'better', 'dog']

### `TextPreprocessor.stem_tokens`

```python
def stem_tokens(tokens: List[str]) -> List[str]
```

Stem a list of tokens using Porter Stemmer.

**Parameters**
tokens : List[str]
    List of word tokens

**Returns**
List[str]
    Stemmed tokens

**Examples**
>>> preprocessor = TextPreprocessor()
>>> preprocessor.stem_tokens(['running', 'better', 'dogs'])
['run', 'better', 'dog']

### `TextPreprocessor.process_text`

```python
def process_text(text: Union[str, None], options: Optional[Dict[str, Any]]=None) -> str
```

Process text with specified preprocessing options.

This is the main method for text preprocessing that applies a configurable
pipeline of text cleaning operations.

**Parameters**
text : Union[str, None]
    Input text to process. If None or NaN, returns empty string.
options : Optional[Dict[str, Any]], default=None
    Dictionary of preprocessing options. If None, uses default options.
    Available options:
    - replace_newlines: bool, default=True - Replace newline characters
    - remove_html: bool, default=True - Remove HTML tags
    - remove_urls: bool, default=True - Remove URLs
    - remove_emails: bool, default=True - Remove email addresses
    - remove_social: bool, default=True - Remove @mentions and #hashtags
    - expand_contractions: bool, default=True - Expand contractions
    - remove_accents: bool, default=True - Remove accented characters
    - lowercase: bool, default=True - Convert to lowercase
    - remove_special_chars: bool, default=True - Remove special characters
    - keep_punctuation: bool, default=False - Keep punctuation marks
    - spell_correction: bool, default=False - Correct spelling (slow)
    - remove_stopwords: bool, default=True - Remove stopwords
    - lemmatize: bool, default=True - Apply lemmatization
    - stem: bool, default=False - Apply stemming (don't use with lemmatize)
    - min_token_length: int, default=1 - Minimum token length to keep

**Returns**
str
    Processed text

**Examples**
>>> preprocessor = TextPreprocessor()

>>> # Process with default options
>>> clean_text = preprocessor.process_text("Hello World! http://example.com")

>>> # Process with custom options
>>> options = {
...     'remove_stopwords': False,
...     'lemmatize': False,
...     'stem': True
... }
>>> clean_text = preprocessor.process_text("Hello World!", options=options)

### `TextPreprocessor.preprocess_dataframe`

```python
def preprocess_dataframe(df: pd.DataFrame, columns: List[str], options: Optional[Dict[str, Any]]=None, inplace: bool=False) -> pd.DataFrame
```

Process multiple text columns in a DataFrame.

**Parameters**
df : pd.DataFrame
    DataFrame containing text columns to process
columns : List[str]
    List of column names to preprocess
options : Optional[Dict[str, Any]], default=None
    Preprocessing options (see process_text for details)
inplace : bool, default=False
    If True, modify the DataFrame in place. Otherwise, return a copy.

**Returns**
pd.DataFrame
    DataFrame with preprocessed text columns

**Examples**
>>> preprocessor = TextPreprocessor()

>>> # Process specific columns
>>> df_clean = preprocessor.preprocess_dataframe(
...     df, 
...     columns=['title', 'description', 'content']
... )

>>> # Process with custom options
>>> options = {'remove_stopwords': False, 'lemmatize': True}
>>> df_clean = preprocessor.preprocess_dataframe(
...     df,
...     columns=['text'],
...     options=options
... )

### `TextPreprocessor.preprocess_dataframe_vectorized`

```python
def preprocess_dataframe_vectorized(df: pd.DataFrame, columns: List[str], options: Optional[Dict[str, Any]]=None) -> pd.DataFrame
```

Process multiple text columns using vectorized operations for better performance.

This method is faster for large DataFrames but may use more memory.

**Parameters**
df : pd.DataFrame
    DataFrame containing text columns to process
columns : List[str]
    List of column names to preprocess
options : Optional[Dict[str, Any]], default=None
    Preprocessing options (see process_text for details)

**Returns**
pd.DataFrame
    DataFrame with preprocessed text columns

**Examples**
>>> preprocessor = TextPreprocessor()
>>> df_clean = preprocessor.preprocess_dataframe_vectorized(
...     df,
...     columns=['title', 'description']
... )

## class `TextVisualizer`

```python
TextVisualizer(style: Optional[str]=None)
```

A class for creating word clouds and analyzing text data.

This class provides methods for visualizing text data through word clouds
and frequency analysis. It's useful for exploratory data analysis of
text corpora.

**Parameters**
style : Optional[str], default=None
    Matplotlib style to use for plots (e.g., 'seaborn', 'ggplot')

**Examples**
>>> # Initialize with default style
>>> visualizer = TextVisualizer()

>>> # Initialize with custom style
>>> visualizer = TextVisualizer(style='seaborn-darkgrid')

>>> # Create word clouds
>>> fig = visualizer.create_wordclouds(df, text_columns=['title', 'content'])

>>> # Analyze word frequencies
>>> fig = visualizer.analyze_word_frequencies(df, text_columns=['title'])

### `TextVisualizer.create_wordclouds`

```python
def create_wordclouds(df: pd.DataFrame, text_columns: List[str], mask_path: Optional[str]=None, background_color: str='white', max_words: int=200, width: int=800, height: int=400, colormap: str='viridis', figsize: Optional[Tuple[int, int]]=None) -> plt.Figure
```

Create word clouds for multiple text columns.

**Parameters**
df : pd.DataFrame
    DataFrame containing the text columns
text_columns : List[str]
    List of column names to visualize
mask_path : Optional[str], default=None
    Path to an image file for shaping the word cloud
background_color : str, default='white'
    Background color of the word clouds
max_words : int, default=200
    Maximum number of words per cloud
width : int, default=800
    Width of each word cloud in pixels
height : int, default=400
    Height of each word cloud in pixels
colormap : str, default='viridis'
    Matplotlib colormap for word colors
figsize : Optional[Tuple[int, int]], default=None
    Figure size (width, height) in inches. Auto-calculated if None.

**Returns**
plt.Figure
    Matplotlib figure containing all word clouds

**Examples**
>>> visualizer = TextVisualizer()
>>> fig = visualizer.create_wordclouds(
...     df,
...     text_columns=['title', 'description'],
...     max_words=100,
...     colormap='plasma'
... )
>>> fig.savefig('wordclouds.png', dpi=300, bbox_inches='tight')

### `TextVisualizer.create_combined_wordcloud`

```python
def create_combined_wordcloud(df: pd.DataFrame, text_columns: List[str], **kwargs) -> plt.Figure
```

Create a single word cloud from combined text columns.

**Parameters**
df : pd.DataFrame
    DataFrame containing the text columns
text_columns : List[str]
    List of column names to combine and visualize
**kwargs
    Additional arguments passed to WordCloud

**Returns**
plt.Figure
    Matplotlib figure with the word cloud

**Examples**
>>> visualizer = TextVisualizer()
>>> fig = visualizer.create_combined_wordcloud(
...     df,
...     text_columns=['title', 'description', 'content'],
...     max_words=300,
...     colormap='coolwarm'
... )

### `TextVisualizer.create_single_wordcloud`

```python
def create_single_wordcloud(text: str, title: Optional[str]='Word Cloud', **kwargs) -> plt.Figure
```

Create a single word cloud with custom settings.

**Parameters**
text : str
    Text to generate word cloud from
title : Optional[str], default='Word Cloud'
    Title for the plot
**kwargs
    Additional WordCloud parameters:
    - background_color: str, default='white'
    - max_words: int, default=200
    - width: int, default=800
    - height: int, default=400
    - colormap: str, default='viridis'
    - mask: numpy array for custom shape

**Returns**
plt.Figure
    Matplotlib figure with the word cloud

**Examples**
>>> visualizer = TextVisualizer()
>>> text = "Python data science machine learning visualization"
>>> fig = visualizer.create_single_wordcloud(
...     text,
...     title='My Word Cloud',
...     colormap='plasma',
...     max_words=50
... )

### `TextVisualizer.analyze_word_frequencies`

```python
def analyze_word_frequencies(df: pd.DataFrame, text_columns: List[str], top_n: int=20, show_percentages: bool=True, figsize: Optional[Tuple[int, int]]=None, save_path: Optional[str]=None) -> plt.Figure
```

Analyze and visualize word frequencies for text columns.

Creates frequency bar charts showing the most common words in each
column, optionally including percentage distributions.

**Parameters**
df : pd.DataFrame
    DataFrame containing the text columns
text_columns : List[str]
    List of column names to analyze
top_n : int, default=20
    Number of top frequent words to display
show_percentages : bool, default=True
    Whether to show percentage distributions alongside counts
figsize : Optional[Tuple[int, int]], default=None
    Figure size (width, height) in inches. Auto-calculated if None.
save_path : Optional[str], default=None
    Path to save the figure (e.g., 'frequencies.png')

**Returns**
plt.Figure
    Matplotlib figure containing frequency visualizations

**Examples**
>>> visualizer = TextVisualizer()
>>> fig = visualizer.analyze_word_frequencies(
...     df,
...     text_columns=['title', 'description'],
...     top_n=15,
...     save_path='word_frequencies.png'
... )

### `TextVisualizer.get_word_frequency_table`

```python
def get_word_frequency_table(df: pd.DataFrame, text_columns: List[str], top_n: int=20) -> pd.DataFrame
```

Get word frequency data as a DataFrame for further analysis.

**Parameters**
df : pd.DataFrame
    DataFrame containing the text columns
text_columns : List[str]
    List of column names to analyze
top_n : int, default=20
    Number of top frequent words to include

**Returns**
pd.DataFrame
    DataFrame with columns: 'column', 'word', 'frequency', 'percentage'

**Examples**
>>> visualizer = TextVisualizer()
>>> freq_df = visualizer.get_word_frequency_table(
...     df,
...     text_columns=['title', 'description'],
...     top_n=50
... )
>>> print(freq_df.head())

### `quick_clean`

```python
def quick_clean(text: Union[str, pd.Series], lowercase: bool=True, remove_urls: bool=True, remove_emails: bool=True, remove_html: bool=True) -> Union[str, pd.Series]
```

Quickly clean text with common preprocessing steps.

This is a convenience function for quick text cleaning without
initializing the full TextPreprocessor class.

**Parameters**
text : Union[str, pd.Series]
    Input text or pandas Series to clean
lowercase : bool, default=True
    Convert text to lowercase
remove_urls : bool, default=True
    Remove URLs from text
remove_emails : bool, default=True
    Remove email addresses
remove_html : bool, default=True
    Remove HTML tags

**Returns**
Union[str, pd.Series]
    Cleaned text (same type as input)

**Examples**
>>> # Clean single string
>>> clean_text = quick_clean("Hello! Visit http://example.com")

>>> # Clean pandas Series
>>> df['clean_text'] = quick_clean(df['text'])

### `extract_ngrams`

```python
def extract_ngrams(text: Union[str, List[str]], n: int=2, preprocessor: Optional[TextPreprocessor]=None) -> List[Tuple[str, ...]]
```

Extract n-grams from text.

**Parameters**
text : Union[str, List[str]]
    Input text string or list of tokens
n : int, default=2
    Size of n-grams (2 for bigrams, 3 for trigrams, etc.)
preprocessor : Optional[TextPreprocessor], default=None
    TextPreprocessor instance for text cleaning. If None, uses default.

**Returns**
List[Tuple[str, ...]]
    List of n-gram tuples

**Examples**
>>> # Extract bigrams
>>> bigrams = extract_ngrams("machine learning is great", n=2)
[('machine', 'learning'), ('learning', 'is'), ('is', 'great')]

>>> # Extract trigrams with preprocessing
>>> preprocessor = TextPreprocessor()
>>> trigrams = extract_ngrams("Machine learning algorithms", n=3, preprocessor=preprocessor)

### `get_text_stats`

```python
def get_text_stats(df: pd.DataFrame, text_columns: List[str]) -> pd.DataFrame
```

Calculate basic text statistics for DataFrame columns.

**Parameters**
df : pd.DataFrame
    DataFrame containing text columns
text_columns : List[str]
    List of column names to analyze

**Returns**
pd.DataFrame
    DataFrame with text statistics per column:
    - total_documents: Number of non-null documents
    - total_words: Total word count
    - avg_words_per_doc: Average words per document
    - unique_words: Number of unique words
    - avg_word_length: Average word length

**Examples**
>>> stats = get_text_stats(df, ['title', 'description'])
>>> print(stats)
