# fmt: off

from types import ModuleType
from pathlib import Path

__all__ = [
    'PANDAS_UNIT_TESTS',
]

################################################################################

PANDAS_UNIT_TESTS = []

def unit(fn):
    PANDAS_UNIT_TESTS.append(fn)
    return fn

################################################################################

@unit
def series_creation_and_basic_operations(numpy: ModuleType, pandas: ModuleType, tmpdir: Path):
    """Test Series creation from various inputs and fundamental operations."""
    np = numpy
    pd = pandas

    # Creation from list
    s1 = pd.Series([1, 2, 3, 4, 5])
    assert len(s1) == 5
    assert s1[0] == 1
    assert s1[4] == 5

    # Creation from numpy array
    arr = np.array([10, 20, 30])
    s2 = pd.Series(arr)
    assert len(s2) == 3
    assert s2[1] == 20

    # Creation with explicit index
    s3 = pd.Series([100, 200, 300], index=['a', 'b', 'c'])
    assert s3['a'] == 100
    assert s3['c'] == 300

    # Creation from dict (keys become index)
    s4 = pd.Series({'x': 1, 'y': 2, 'z': 3})
    assert s4['y'] == 2
    assert set(s4.index) == {'x', 'y', 'z'}

    # Arithmetic operations
    s5 = pd.Series([1, 2, 3])
    s6 = pd.Series([10, 20, 30])

    added = s5 + s6
    assert list(added) == [11, 22, 33]

    multiplied = s5 * 2
    assert list(multiplied) == [2, 4, 6]

    subtracted = s6 - s5
    assert list(subtracted) == [9, 18, 27]

    # Boolean indexing
    s7 = pd.Series([1, 2, 3, 4, 5])
    filtered = s7[s7 > 2]
    assert list(filtered) == [3, 4, 5]

    # Aggregations
    s8 = pd.Series([1, 2, 3, 4, 5])
    assert s8.sum() == 15
    assert s8.mean() == 3.0
    assert s8.min() == 1
    assert s8.max() == 5
    assert s8.std() > 0  # just check it returns something sensible

    # Name attribute
    s9 = pd.Series([1, 2, 3], name='my_series')
    assert s9.name == 'my_series'


@unit
def dataframe_creation_and_structure(numpy: ModuleType, pandas: ModuleType, tmpdir: Path):
    """Test DataFrame creation from various sources and structural properties."""
    np = numpy
    pd = pandas

    # From dict of lists
    df1 = pd.DataFrame({
        'a': [1, 2, 3],
        'b': [4, 5, 6],
        'c': [7, 8, 9]
    })
    assert df1.shape == (3, 3)
    assert list(df1.columns) == ['a', 'b', 'c']
    assert len(df1) == 3

    # From dict of numpy arrays
    df2 = pd.DataFrame({
        'x': np.array([1.0, 2.0]),
        'y': np.array([3.0, 4.0])
    })
    assert df2.shape == (2, 2)

    # With explicit index
    df3 = pd.DataFrame(
        {'col1': [10, 20], 'col2': [30, 40]},
        index=['row1', 'row2']
    )
    assert list(df3.index) == ['row1', 'row2']

    # From list of dicts (records)
    df4 = pd.DataFrame([
        {'name': 'Alice', 'age': 30},
        {'name': 'Bob', 'age': 25},
        {'name': 'Charlie', 'age': 35}
    ])
    assert df4.shape == (3, 2)
    assert 'name' in df4.columns
    assert 'age' in df4.columns

    # From 2D numpy array with column names
    arr2d = np.array([[1, 2], [3, 4], [5, 6]])
    df5 = pd.DataFrame(arr2d, columns=['p', 'q'])
    assert df5.shape == (3, 2)
    assert list(df5.columns) == ['p', 'q']

    # Empty DataFrame
    df_empty = pd.DataFrame()
    assert df_empty.shape == (0, 0)

    # dtypes property
    df6 = pd.DataFrame({'ints': [1, 2, 3], 'floats': [1.1, 2.2, 3.3]})
    assert hasattr(df6, 'dtypes')


@unit
def dataframe_column_and_row_access(numpy: ModuleType, pandas: ModuleType, tmpdir: Path):
    """Test various ways to access columns and rows in a DataFrame."""
    pd = pandas

    df = pd.DataFrame({
        'name': ['Alice', 'Bob', 'Charlie', 'Diana'],
        'age':  [25, 30, 35, 28],
        'city': ['NYC', 'LA', 'Chicago', 'Boston']
    })

    # Column access via attribute
    ages = df.age
    assert list(ages) == [25, 30, 35, 28]

    # Column access via bracket notation
    names = df['name']
    assert list(names) == ['Alice', 'Bob', 'Charlie', 'Diana']

    # Multiple column selection
    subset = df[['name', 'city']]
    assert list(subset.columns) == ['name', 'city']
    assert subset.shape == (4, 2)

    # Row access via iloc (integer location)
    first_row = df.iloc[0]
    assert first_row['name'] == 'Alice'
    assert first_row['age'] == 25

    last_row = df.iloc[-1]
    assert last_row['name'] == 'Diana'

    # Slice via iloc
    middle_rows = df.iloc[1:3]
    assert len(middle_rows) == 2
    assert list(middle_rows['name']) == ['Bob', 'Charlie']

    # iloc with row and column
    cell = df.iloc[2, 1]
    assert cell == 35  # Charlie's age

    # loc with labeled index
    df_indexed = pd.DataFrame(
        {'val': [100, 200, 300]},
        index=['a', 'b', 'c']
    )
    assert df_indexed.loc['b', 'val'] == 200
    assert df_indexed.loc['a']['val'] == 100


@unit
def dataframe_boolean_indexing_and_query(numpy: ModuleType, pandas: ModuleType, tmpdir: Path):
    """Test filtering DataFrames with boolean conditions."""
    pd = pandas

    df = pd.DataFrame({
        'product':  ['apple', 'banana', 'cherry', 'date', 'elderberry'],
        'price':    [1.20, 0.50, 2.50, 3.00, 4.50],
        'quantity': [100, 150, 50, 75, 25]
    })

    # Simple boolean filter
    expensive = df[df['price'] > 2.0]
    assert len(expensive) == 3
    assert set(expensive['product']) == {'cherry', 'date', 'elderberry'}

    # Compound conditions with & (and)
    filtered = df[(df['price'] > 1.0) & (df['quantity'] >= 50)]
    assert len(filtered) == 3  # apple, cherry, date

    # Compound conditions with | (or)
    either = df[(df['price'] < 1.0) | (df['quantity'] < 30)]
    assert 'banana' in list(either['product'])
    assert 'elderberry' in list(either['product'])

    # Negation with ~
    not_cheap = df[~(df['price'] < 1.0)]
    assert 'banana' not in list(not_cheap['product'])

    # isin for membership testing
    selected = df[df['product'].isin(['apple', 'cherry'])]
    assert len(selected) == 2


@unit
def dataframe_assignment_and_modification(numpy: ModuleType, pandas: ModuleType, tmpdir: Path):
    """Test modifying DataFrame contents: adding columns, updating values."""
    np = numpy
    pd = pandas

    df = pd.DataFrame({
        'a': [1, 2, 3],
        'b': [4, 5, 6]
    })

    # Add new column from scalar
    df['c'] = 10
    assert list(df['c']) == [10, 10, 10]

    # Add new column from list
    df['d'] = [7, 8, 9]
    assert list(df['d']) == [7, 8, 9]

    # Add column as computation of existing columns
    df['e'] = df['a'] + df['b']
    assert list(df['e']) == [5, 7, 9]

    # Modify existing column
    df['a'] = df['a'] * 2
    assert list(df['a']) == [2, 4, 6]

    # Conditional assignment using loc
    df2 = pd.DataFrame({'x': [1, 2, 3, 4, 5]})
    df2.loc[df2['x'] > 3, 'x'] = 0
    assert list(df2['x']) == [1, 2, 3, 0, 0]

    # Drop column
    df3 = pd.DataFrame({'keep': [1, 2], 'drop': [3, 4]})
    df3 = df3.drop(columns=['drop'])
    assert 'drop' not in df3.columns
    assert 'keep' in df3.columns

    # Drop row
    df4 = pd.DataFrame({'v': [10, 20, 30]}, index=['a', 'b', 'c'])
    df4 = df4.drop(index=['b'])
    assert len(df4) == 2
    assert 'b' not in df4.index


@unit
def dataframe_aggregations_and_describe(numpy: ModuleType, pandas: ModuleType, tmpdir: Path):
    """Test aggregation methods: sum, mean, std, describe, etc."""
    pd = pandas

    df = pd.DataFrame({
        'values': [10, 20, 30, 40, 50],
        'group':  ['A', 'A', 'B', 'B', 'B']
    })

    # Column-wise aggregations
    assert df['values'].sum() == 150
    assert df['values'].mean() == 30.0
    assert df['values'].min() == 10
    assert df['values'].max() == 50
    assert df['values'].count() == 5

    # Variance and std
    std = df['values'].std()
    var = df['values'].var()
    assert std > 0
    assert var > 0
    # std is sqrt of var (with same ddof)
    assert abs(std ** 2 - var) < 1e-10

    # Median
    assert df['values'].median() == 30.0

    # describe returns summary statistics
    desc = df['values'].describe()
    assert 'mean' in desc.index or hasattr(desc, 'mean')

    # DataFrame-level aggregation
    df2 = pd.DataFrame({
        'a': [1, 2, 3],
        'b': [4, 5, 6]
    })
    sums = df2.sum()
    assert sums['a'] == 6
    assert sums['b'] == 15


@unit
def groupby_operations(numpy: ModuleType, pandas: ModuleType, tmpdir: Path):
    """Test groupby functionality: split-apply-combine pattern."""
    pd = pandas

    df = pd.DataFrame({
        'category': ['A', 'A', 'B', 'B', 'B', 'C'],
        'value':    [10, 20, 30, 40, 50, 60],
        'count':    [1, 2, 3, 4, 5, 6]
    })

    # Basic groupby with single aggregation
    grouped_sum = df.groupby('category')['value'].sum()
    assert grouped_sum['A'] == 30
    assert grouped_sum['B'] == 120
    assert grouped_sum['C'] == 60

    # Groupby with mean
    grouped_mean = df.groupby('category')['value'].mean()
    assert grouped_mean['A'] == 15.0
    assert grouped_mean['B'] == 40.0
    assert grouped_mean['C'] == 60.0

    # Groupby multiple columns aggregation
    agg_result = df.groupby('category').agg({'value': 'sum', 'count': 'mean'})
    assert agg_result.loc['A', 'value'] == 30
    assert agg_result.loc['A', 'count'] == 1.5

    # Groupby size (count of rows per group)
    sizes = df.groupby('category').size()
    assert sizes['A'] == 2
    assert sizes['B'] == 3
    assert sizes['C'] == 1

    # Groupby with multiple keys
    df2 = pd.DataFrame({
        'x': ['a', 'a', 'b', 'b'],
        'y': [1, 2, 1, 2],
        'z': [10, 20, 30, 40]
    })
    multi_group = df2.groupby(['x', 'y'])['z'].sum()
    assert multi_group[('a', 1)] == 10 or multi_group.loc['a', 1] == 10


@unit
def merge_and_join(numpy: ModuleType, pandas: ModuleType, tmpdir: Path):
    """Test merging/joining DataFrames on keys."""
    pd = pandas

    left = pd.DataFrame({
        'key': ['K0', 'K1', 'K2', 'K3'],
        'A':   [1, 2, 3, 4]
    })

    right = pd.DataFrame({
        'key': ['K0', 'K1', 'K2', 'K4'],
        'B':   [10, 20, 30, 40]
    })

    # Inner merge (default)
    inner = pd.merge(left, right, on='key')
    assert len(inner) == 3  # K0, K1, K2 are common
    assert set(inner.columns) == {'key', 'A', 'B'}

    # Left merge
    left_merged = pd.merge(left, right, on='key', how='left')
    assert len(left_merged) == 4  # all keys from left

    # Right merge
    right_merged = pd.merge(left, right, on='key', how='right')
    assert len(right_merged) == 4  # all keys from right

    # Outer merge
    outer = pd.merge(left, right, on='key', how='outer')
    assert len(outer) == 5  # K0, K1, K2, K3, K4

    # Merge on different column names
    df1 = pd.DataFrame({'id_left': [1, 2], 'val1': ['a', 'b']})
    df2 = pd.DataFrame({'id_right': [1, 2], 'val2': ['x', 'y']})
    merged_diff = pd.merge(df1, df2, left_on='id_left', right_on='id_right')
    assert len(merged_diff) == 2


@unit
def concat_and_append(numpy: ModuleType, pandas: ModuleType, tmpdir: Path):
    """Test concatenating DataFrames and Series."""
    pd = pandas

    df1 = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
    df2 = pd.DataFrame({'A': [5, 6], 'B': [7, 8]})

    # Vertical concat (row-wise, axis=0)
    vertical = pd.concat([df1, df2], ignore_index=True)
    assert len(vertical) == 4
    assert list(vertical['A']) == [1, 2, 5, 6]

    # Horizontal concat (column-wise, axis=1)
    df3 = pd.DataFrame({'C': [10, 20]})
    horizontal = pd.concat([df1, df3], axis=1)
    assert list(horizontal.columns) == ['A', 'B', 'C']
    assert horizontal.shape == (2, 3)

    # Concat with mismatched columns fills NaN
    df4 = pd.DataFrame({'A': [100], 'D': [200]})
    mixed = pd.concat([df1, df4], ignore_index=True)
    assert 'D' in mixed.columns
    assert pd.isna(mixed.loc[0, 'D'])  # df1 rows have NaN for D

    # Series concat
    s1 = pd.Series([1, 2, 3])
    s2 = pd.Series([4, 5, 6])
    concat_series = pd.concat([s1, s2], ignore_index=True)
    assert len(concat_series) == 6
    assert list(concat_series) == [1, 2, 3, 4, 5, 6]


@unit
def sorting_and_ranking(numpy: ModuleType, pandas: ModuleType, tmpdir: Path):
    """Test sorting by values and index, and ranking."""
    pd = pandas

    df = pd.DataFrame({
        'name':  ['Charlie', 'Alice', 'Bob', 'Diana'],
        'score': [85, 90, 78, 92]
    })

    # Sort by single column ascending
    sorted_asc = df.sort_values('score')
    assert list(sorted_asc['name']) == ['Bob', 'Charlie', 'Alice', 'Diana']

    # Sort by single column descending
    sorted_desc = df.sort_values('score', ascending=False)
    assert list(sorted_desc['name']) == ['Diana', 'Alice', 'Charlie', 'Bob']

    # Sort by multiple columns
    df2 = pd.DataFrame({
        'group': ['A', 'B', 'A', 'B'],
        'value': [2, 1, 1, 2]
    })
    multi_sorted = df2.sort_values(['group', 'value'])
    assert list(multi_sorted['group']) == ['A', 'A', 'B', 'B']

    # Sort index
    df3 = pd.DataFrame({'x': [1, 2, 3]}, index=['c', 'a', 'b'])
    idx_sorted = df3.sort_index()
    assert list(idx_sorted.index) == ['a', 'b', 'c']

    # Ranking
    s = pd.Series([30, 10, 20, 10])
    ranks = s.rank()
    # 30 is rank 4, 10s are ranks 1.5 (tied), 20 is rank 3
    assert ranks.iloc[0] == 4.0  # 30
    assert ranks.iloc[1] == 1.5  # first 10
    assert ranks.iloc[2] == 3.0  # 20
    assert ranks.iloc[3] == 1.5  # second 10


@unit
def missing_data_handling(numpy: ModuleType, pandas: ModuleType, tmpdir: Path):
    """Test NaN/None handling: isna, fillna, dropna."""
    np = numpy
    pd = pandas

    # Create data with missing values
    df = pd.DataFrame({
        'a': [1, np.nan, 3, np.nan, 5],
        'b': [np.nan, 2, np.nan, 4, 5],
        'c': [1, 2, 3, 4, 5]
    })

    # isna / isnull detection
    na_mask = df['a'].isna()
    assert na_mask.iloc[1] == True
    assert na_mask.iloc[0] == False

    # notna
    notna_mask = df['a'].notna()
    assert notna_mask.iloc[0] == True
    assert notna_mask.iloc[1] == False

    # fillna with scalar
    filled = df['a'].fillna(0)
    assert filled.iloc[1] == 0
    assert filled.iloc[3] == 0
    assert filled.iloc[0] == 1

    # fillna with method forward fill
    s = pd.Series([1, np.nan, np.nan, 4])
    ffilled = s.ffill()
    assert ffilled.iloc[1] == 1
    assert ffilled.iloc[2] == 1

    # dropna on Series
    s2 = pd.Series([1, np.nan, 3])
    dropped = s2.dropna()
    assert len(dropped) == 2
    assert list(dropped) == [1, 3]

    # dropna on DataFrame (row-wise)
    df_dropped = df.dropna()
    assert len(df_dropped) == 1  # only row 4 (index 4) has no NaN

    # dropna with subset
    df_subset_dropped = df.dropna(subset=['c'])
    assert len(df_subset_dropped) == 5  # column c has no NaN


@unit
def apply_and_map(numpy: ModuleType, pandas: ModuleType, tmpdir: Path):
    """Test apply/map/applymap for element-wise and row/column operations."""
    pd = pandas

    # Series.apply
    s = pd.Series([1, 2, 3, 4])
    squared = s.apply(lambda x: x ** 2)
    assert list(squared) == [1, 4, 9, 16]

    # Series.map with dict
    s2 = pd.Series(['a', 'b', 'c'])
    mapped = s2.map({'a': 1, 'b': 2, 'c': 3})
    assert list(mapped) == [1, 2, 3]

    # Series.map with function
    s3 = pd.Series(['hello', 'world'])
    upper = s3.map(str.upper)
    assert list(upper) == ['HELLO', 'WORLD']

    # DataFrame.apply column-wise (axis=0)
    df = pd.DataFrame({
        'x': [1, 2, 3],
        'y': [4, 5, 6]
    })
    col_sums = df.apply(sum, axis=0)
    assert col_sums['x'] == 6
    assert col_sums['y'] == 15

    # DataFrame.apply row-wise (axis=1)
    row_sums = df.apply(sum, axis=1)
    assert list(row_sums) == [5, 7, 9]

    # DataFrame.applymap (element-wise) - might be called map in newer pandas
    df2 = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
    if hasattr(df2, 'applymap'):
        doubled = df2.applymap(lambda x: x * 2)
    else:
        doubled = df2.map(lambda x: x * 2)
    assert doubled.loc[0, 'a'] == 2
    assert doubled.loc[1, 'b'] == 8


@unit
def string_operations(numpy: ModuleType, pandas: ModuleType, tmpdir: Path):
    """Test vectorized string operations via .str accessor."""
    pd = pandas

    s = pd.Series(['  hello  ', 'WORLD', 'Python', 'pandas'])

    # lower
    lower = s.str.lower()
    assert list(lower) == ['  hello  ', 'world', 'python', 'pandas']

    # upper
    upper = s.str.upper()
    assert list(upper) == ['  HELLO  ', 'WORLD', 'PYTHON', 'PANDAS']

    # strip
    stripped = s.str.strip()
    assert stripped.iloc[0] == 'hello'

    # contains
    has_o = s.str.contains('o')
    assert has_o.iloc[0] == True   # hello
    assert has_o.iloc[1] == False  # WORLD

    # len
    lengths = s.str.len()
    assert lengths.iloc[2] == 6  # 'Python'

    # replace
    replaced = s.str.replace('o', '0')
    assert '0' in replaced.iloc[2]  # Pyth0n

    # split
    s2 = pd.Series(['a-b-c', 'x-y'])
    split = s2.str.split('-')
    assert split.iloc[0] == ['a', 'b', 'c']

    # startswith / endswith
    s3 = pd.Series(['apple', 'apricot', 'banana'])
    starts_ap = s3.str.startswith('ap')
    assert starts_ap.iloc[0] == True
    assert starts_ap.iloc[2] == False


@unit
def datetime_operations(numpy: ModuleType, pandas: ModuleType, tmpdir: Path):
    """Test datetime parsing and dt accessor operations."""
    pd = pandas

    # Parse datetime strings
    dates = pd.to_datetime(['2023-01-15', '2023-06-20', '2024-12-25'])
    assert len(dates) == 3

    # Create Series with datetime
    s = pd.Series(pd.to_datetime(['2023-01-15', '2023-06-20', '2023-12-25']))

    # Extract year
    years = s.dt.year
    assert list(years) == [2023, 2023, 2023]

    # Extract month
    months = s.dt.month
    assert list(months) == [1, 6, 12]

    # Extract day
    days = s.dt.day
    assert list(days) == [15, 20, 25]

    # Day of week (0=Monday in pandas)
    dow = s.dt.dayofweek
    assert len(dow) == 3

    # DatetimeIndex in DataFrame
    df = pd.DataFrame({
        'date':  pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03']),
        'value': [10, 20, 30]
    })
    df = df.set_index('date')
    assert df.index[0].day == 1


@unit
def csv_read_write(numpy: ModuleType, pandas: ModuleType, tmpdir: Path):
    """Test reading and writing CSV files."""
    pd = pandas
    tmpfile = tmpdir / 'input.csv'

    # Write a simple CSV
    csv_content = """name,age,city
Alice,30,NYC
Bob,25,LA
Charlie,35,Chicago"""
    tmpfile.write_text(csv_content)

    # Read CSV
    df = pd.read_csv(tmpfile)
    assert df.shape == (3, 3)
    assert list(df.columns) == ['name', 'age', 'city']
    assert list(df['name']) == ['Alice', 'Bob', 'Charlie']
    assert list(df['age']) == [30, 25, 35]

    # Write DataFrame to CSV and read back
    df_out = pd.DataFrame({
        'x': [1, 2, 3],
        'y': ['a', 'b', 'c']
    })
    tmpfile = tmpdir / 'output.csv'
    df_out.to_csv(tmpfile, index=False)

    df_back = pd.read_csv(tmpfile)
    assert list(df_back['x']) == [1, 2, 3]
    assert list(df_back['y']) == ['a', 'b', 'c']

    # Clean up
    tmpfile.unlink()


@unit
def csv_read_options(numpy: ModuleType, pandas: ModuleType, tmpdir: Path):
    """Test various CSV reading options: sep, header, index_col, usecols, dtype."""
    pd = pandas
    tmpfile = tmpdir / 'options.csv'

    # Custom separator
    tsv_content = "a\tb\tc\n1\t2\t3\n4\t5\t6"
    tmpfile.write_text(tsv_content)
    df_tsv = pd.read_csv(tmpfile, sep='\t')
    assert df_tsv.shape == (2, 3)

    # No header
    no_header = "1,2,3\n4,5,6"
    tmpfile.write_text(no_header)
    df_no_header = pd.read_csv(tmpfile, header=None)
    assert list(df_no_header.columns) == [0, 1, 2]

    # Custom column names
    df_names = pd.read_csv(tmpfile, header=None, names=['x', 'y', 'z'])
    assert list(df_names.columns) == ['x', 'y', 'z']

    # Use specific columns only
    full_csv = "a,b,c,d\n1,2,3,4\n5,6,7,8"
    tmpfile.write_text(full_csv)
    df_subset = pd.read_csv(tmpfile, usecols=['a', 'c'])
    assert list(df_subset.columns) == ['a', 'c']

    # Skip rows
    skip_csv = "junk\nmore junk\na,b\n1,2\n3,4"
    tmpfile.write_text(skip_csv)
    df_skip = pd.read_csv(tmpfile, skiprows=2)
    assert list(df_skip.columns) == ['a', 'b']

    # Index column
    idx_csv = "idx,val\na,1\nb,2"
    tmpfile.write_text(idx_csv)
    df_idx = pd.read_csv(tmpfile, index_col='idx')
    assert list(df_idx.index) == ['a', 'b']


@unit
def pivot_and_melt(numpy: ModuleType, pandas: ModuleType, tmpdir: Path):
    """Test reshaping with pivot/pivot_table and melt."""
    pd = pandas

    # Data for pivoting
    df = pd.DataFrame({
        'date':    ['2023-01', '2023-01', '2023-02', '2023-02'],
        'product': ['A', 'B', 'A', 'B'],
        'sales':   [100, 150, 120, 180]
    })

    # pivot_table
    pivoted = df.pivot_table(index='date', columns='product', values='sales')
    assert pivoted.loc['2023-01', 'A'] == 100
    assert pivoted.loc['2023-02', 'B'] == 180

    # melt (unpivot)
    wide_df = pd.DataFrame({
        'id': [1, 2],
        'A':  [10, 20],
        'B':  [30, 40]
    })
    melted = pd.melt(wide_df, id_vars=['id'], value_vars=['A', 'B'])
    assert 'variable' in melted.columns
    assert 'value' in melted.columns
    assert len(melted) == 4

    # stack/unstack (if supported)
    if hasattr(pd.DataFrame, 'stack'):
        df2 = pd.DataFrame(
            {'x': [1, 2], 'y': [3, 4]},
            index=['a', 'b']
        )
        stacked = df2.stack()
        assert len(stacked) == 4


@unit
def unique_and_value_counts(numpy: ModuleType, pandas: ModuleType, tmpdir: Path):
    """Test unique values and value counting."""
    pd = pandas

    s = pd.Series(['a', 'b', 'a', 'c', 'b', 'a', 'a'])

    # unique
    uniques = s.unique()
    assert set(uniques) == {'a', 'b', 'c'}

    # nunique
    assert s.nunique() == 3

    # value_counts
    counts = s.value_counts()
    assert counts['a'] == 4
    assert counts['b'] == 2
    assert counts['c'] == 1

    # value_counts normalized
    norm_counts = s.value_counts(normalize=True)
    assert abs(norm_counts['a'] - 4 / 7) < 1e-10

    # duplicated
    dups = s.duplicated()
    assert dups.iloc[0] == False  # first 'a'
    assert dups.iloc[2] == True  # second 'a'

    # drop_duplicates on Series
    no_dups = s.drop_duplicates()
    assert len(no_dups) == 3

    # drop_duplicates on DataFrame
    df = pd.DataFrame({
        'x': [1, 1, 2],
        'y': [1, 1, 2]
    })
    df_no_dups = df.drop_duplicates()
    assert len(df_no_dups) == 2


@unit
def set_and_reset_index(numpy: ModuleType, pandas: ModuleType, tmpdir: Path):
    """Test index manipulation: set_index, reset_index."""
    pd = pandas

    df = pd.DataFrame({
        'key':   ['a', 'b', 'c'],
        'value': [1, 2, 3]
    })

    # set_index
    indexed = df.set_index('key')
    assert list(indexed.index) == ['a', 'b', 'c']
    assert 'key' not in indexed.columns
    assert indexed.loc['b', 'value'] == 2

    # reset_index brings index back as column
    reset = indexed.reset_index()
    assert 'key' in reset.columns
    assert list(reset['key']) == ['a', 'b', 'c']

    # reset_index with drop=True discards the index
    reset_drop = indexed.reset_index(drop=True)
    assert 'key' not in reset_drop.columns

    # Multi-level set_index
    df2 = pd.DataFrame({
        'a': ['x', 'x', 'y', 'y'],
        'b': [1, 2, 1, 2],
        'c': [10, 20, 30, 40]
    })
    multi_indexed = df2.set_index(['a', 'b'])
    assert multi_indexed.loc[('x', 1), 'c'] == 10


@unit
def copy_and_views(numpy: ModuleType, pandas: ModuleType, tmpdir: Path):
    """Test copy behavior and avoiding SettingWithCopyWarning issues."""
    pd = pandas

    df = pd.DataFrame({
        'a': [1, 2, 3],
        'b': [4, 5, 6]
    })

    # Explicit copy
    df_copy = df.copy()
    df_copy['a'] = [10, 20, 30]

    # Original should be unchanged
    assert list(df['a']) == [1, 2, 3]

    # Deep copy (default)
    df_deep = df.copy(deep=True)
    assert list(df_deep['a']) == [1, 2, 3]

    # Shallow copy shares data
    df_shallow = df.copy(deep=False)
    # Behavior may vary; just check it exists
    assert df_shallow.shape == df.shape


@unit
def head_tail_sample(numpy: ModuleType, pandas: ModuleType, tmpdir: Path):
    """Test head, tail, and sample methods."""
    pd = pandas

    df = pd.DataFrame({
        'x': list(range(100))
    })

    # head default (5 rows)
    h = df.head()
    assert len(h) == 5
    assert list(h['x']) == [0, 1, 2, 3, 4]

    # head with n
    h10 = df.head(10)
    assert len(h10) == 10

    # tail default (5 rows)
    t = df.tail()
    assert len(t) == 5
    assert list(t['x']) == [95, 96, 97, 98, 99]

    # tail with n
    t3 = df.tail(3)
    assert len(t3) == 3

    # sample
    sampled = df.sample(n=10)
    assert len(sampled) == 10

    # sample with fraction
    sampled_frac = df.sample(frac=0.1)
    assert len(sampled_frac) == 10

    # sample with random_state for reproducibility
    s1 = df.sample(n=5, random_state=42)
    s2 = df.sample(n=5, random_state=42)
    assert list(s1['x']) == list(s2['x'])


@unit
def rename_columns_and_index(numpy: ModuleType, pandas: ModuleType, tmpdir: Path):
    """Test renaming columns and index labels."""
    pd = pandas

    df = pd.DataFrame({
        'old_name': [1, 2, 3],
        'another':  [4, 5, 6]
    })

    # Rename columns with dict
    renamed = df.rename(columns={'old_name': 'new_name'})
    assert 'new_name' in renamed.columns
    assert 'old_name' not in renamed.columns

    # Rename with function
    upper_cols = df.rename(columns=str.upper)
    assert 'OLD_NAME' in upper_cols.columns

    # Rename index
    df2 = pd.DataFrame({'x': [1, 2]}, index=['a', 'b'])
    renamed_idx = df2.rename(index={'a': 'alpha', 'b': 'beta'})
    assert list(renamed_idx.index) == ['alpha', 'beta']

    # columns attribute assignment
    df3 = pd.DataFrame({'a': [1], 'b': [2]})
    df3.columns = ['X', 'Y']
    assert list(df3.columns) == ['X', 'Y']


@unit
def astype_and_dtype_conversion(numpy: ModuleType, pandas: ModuleType, tmpdir: Path):
    """Test dtype conversions."""
    np = numpy
    pd = pandas

    df = pd.DataFrame({
        'ints':    [1, 2, 3],
        'floats':  [1.5, 2.5, 3.5],
        'strings': ['1', '2', '3']
    })

    # Convert int to float
    as_float = df['ints'].astype(float)
    assert as_float.dtype == np.float64 or 'float' in str(as_float.dtype)

    # Convert string to int
    as_int = df['strings'].astype(int)
    assert list(as_int) == [1, 2, 3]

    # Convert float to int
    floats_to_int = df['floats'].astype(int)
    assert list(floats_to_int) == [1, 2, 3]

    # Convert to string
    as_str = df['ints'].astype(str)
    assert list(as_str) == ['1', '2', '3']


@unit
def clip_and_replace(numpy: ModuleType, pandas: ModuleType, tmpdir: Path):
    """Test clip and replace operations."""
    np = numpy
    pd = pandas

    s = pd.Series([1, 5, 10, 15, 20])

    # clip
    clipped = s.clip(lower=5, upper=15)
    assert list(clipped) == [5, 5, 10, 15, 15]

    # replace single value
    replaced = s.replace(10, 100)
    assert 100 in list(replaced)
    assert 10 not in list(replaced)

    # replace with dict
    s2 = pd.Series(['a', 'b', 'c'])
    replaced_dict = s2.replace({'a': 'x', 'b': 'y'})
    assert list(replaced_dict) == ['x', 'y', 'c']

    # replace in DataFrame
    df = pd.DataFrame({'col': [1, 2, 3, 2, 1]})
    df_replaced = df.replace({1: 100, 2: 200})
    assert list(df_replaced['col']) == [100, 200, 3, 200, 100]


@unit
def where_and_mask(numpy: ModuleType, pandas: ModuleType, tmpdir: Path):
    """Test conditional replacement with where and mask."""
    np = numpy
    pd = pandas

    s = pd.Series([1, 2, 3, 4, 5])

    # where: keep values where condition is True, replace others
    result = s.where(s > 2, other=0)
    assert list(result) == [0, 0, 3, 4, 5]

    # mask: replace values where condition is True (opposite of where)
    masked = s.mask(s > 2, other=-1)
    assert list(masked) == [1, 2, -1, -1, -1]

    # np.where style (for reference, works with numpy arrays)
    arr = np.array([1, 2, 3, 4, 5])
    np_result = np.where(arr > 2, arr, 0)
    assert list(np_result) == [0, 0, 3, 4, 5]


@unit
def shift_and_diff(numpy: ModuleType, pandas: ModuleType, tmpdir: Path):
    """Test time series operations: shift and diff."""
    np = numpy
    pd = pandas

    s = pd.Series([10, 20, 30, 40, 50])

    # shift forward (lag)
    shifted = s.shift(1)
    assert pd.isna(shifted.iloc[0])
    assert shifted.iloc[1] == 10
    assert shifted.iloc[4] == 40

    # shift backward (lead)
    shifted_back = s.shift(-1)
    assert shifted_back.iloc[0] == 20
    assert pd.isna(shifted_back.iloc[4])

    # diff (difference with previous)
    diffed = s.diff()
    assert pd.isna(diffed.iloc[0])
    assert diffed.iloc[1] == 10  # 20 - 10
    assert diffed.iloc[2] == 10  # 30 - 20

    # pct_change
    pct = s.pct_change()
    assert pd.isna(pct.iloc[0])
    assert abs(pct.iloc[1] - 1.0) < 1e-10  # (20-10)/10 = 1.0


@unit
def cumulative_operations(numpy: ModuleType, pandas: ModuleType, tmpdir: Path):
    """Test cumulative sum, product, min, max."""
    pd = pandas

    s = pd.Series([1, 2, 3, 4, 5])

    # cumsum
    cs = s.cumsum()
    assert list(cs) == [1, 3, 6, 10, 15]

    # cumprod
    cp = s.cumprod()
    assert list(cp) == [1, 2, 6, 24, 120]

    # cummax
    s2 = pd.Series([3, 1, 4, 1, 5, 9, 2])
    cmax = s2.cummax()
    assert list(cmax) == [3, 3, 4, 4, 5, 9, 9]

    # cummin
    cmin = s2.cummin()
    assert list(cmin) == [3, 1, 1, 1, 1, 1, 1]


@unit
def rolling_window(numpy: ModuleType, pandas: ModuleType, tmpdir: Path):
    """Test rolling window calculations."""
    np = numpy
    pd = pandas

    s = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

    # Rolling mean with window of 3
    rolling_mean = s.rolling(window=3).mean()
    # First two values are NaN (not enough data)
    assert pd.isna(rolling_mean.iloc[0])
    assert pd.isna(rolling_mean.iloc[1])
    assert rolling_mean.iloc[2] == 2.0  # (1+2+3)/3
    assert rolling_mean.iloc[3] == 3.0  # (2+3+4)/3

    # Rolling sum
    rolling_sum = s.rolling(window=3).sum()
    assert rolling_sum.iloc[2] == 6.0  # 1+2+3

    # Rolling std
    rolling_std = s.rolling(window=3).std()
    assert rolling_std.iloc[2] > 0

    # Rolling with min_periods
    rolling_mp = s.rolling(window=3, min_periods=1).mean()
    assert rolling_mp.iloc[0] == 1.0  # just the first value
    assert rolling_mp.iloc[1] == 1.5  # (1+2)/2


@unit
def expanding_window(numpy: ModuleType, pandas: ModuleType, tmpdir: Path):
    """Test expanding (cumulative) window calculations."""
    pd = pandas

    s = pd.Series([1, 2, 3, 4, 5])

    # Expanding mean (cumulative mean)
    exp_mean = s.expanding().mean()
    assert exp_mean.iloc[0] == 1.0
    assert exp_mean.iloc[1] == 1.5
    assert exp_mean.iloc[2] == 2.0
    assert exp_mean.iloc[4] == 3.0

    # Expanding sum (same as cumsum)
    exp_sum = s.expanding().sum()
    assert list(exp_sum) == [1.0, 3.0, 6.0, 10.0, 15.0]


@unit
def null_construction_and_comparison(numpy: ModuleType, pandas: ModuleType, tmpdir: Path):
    """Test pd.NA, pd.NaT, and null comparisons."""
    np = numpy
    pd = pandas

    # pd.isna and pd.notna as functions
    assert pd.isna(np.nan) == True
    assert pd.notna(1.0) == True

    # Check None handling
    s = pd.Series([1, None, 3])
    assert pd.isna(s.iloc[1]) == True

    # NaT for datetime
    if hasattr(pd, 'NaT'):
        assert pd.isna(pd.NaT) == True


@unit
def info_and_memory(numpy: ModuleType, pandas: ModuleType, tmpdir: Path):
    """Test info() method and memory_usage."""
    pd = pandas

    df = pd.DataFrame({
        'a': [1, 2, 3],
        'b': [1.1, 2.2, 3.3],
        'c': ['x', 'y', 'z']
    })

    # memory_usage returns bytes per column
    mem = df.memory_usage()
    assert hasattr(mem, '__len__')  # it's a Series-like object

    # info() just needs to run without error (usually prints)
    # Some implementations return None, some return a string
    import io

    buf = io.StringIO()
    result = df.info(buf=buf)
    # Just check it doesn't crash


@unit
def equals_and_comparison(numpy: ModuleType, pandas: ModuleType, tmpdir: Path):
    """Test DataFrame/Series equality checks."""
    pd = pandas

    df1 = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    df2 = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    df3 = pd.DataFrame({'a': [1, 2, 99], 'b': [4, 5, 6]})

    # equals method
    assert df1.equals(df2) == True
    assert df1.equals(df3) == False

    # Series equals
    s1 = pd.Series([1, 2, 3])
    s2 = pd.Series([1, 2, 3])
    s3 = pd.Series([1, 2, 4])

    assert s1.equals(s2) == True
    assert s1.equals(s3) == False
