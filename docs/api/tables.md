# Table API

Examples assume `import hedgehogs as hdg`.

## API index

| API | Purpose | Returns |
| --- | --- | --- |
| `hdg.Table(...)` | Create a formatted table | `Table` |
| `hdg.Table.from_dataframe(...)` | Read selected DataFrame columns | `Table` |
| `table.to_dataframe(...)` | Convert formatted rows to pandas or Polars | `DataFrame` |
| `table.add_row(...)` | Append a row | `None` |
| `table.update_row(...)` | Replace a row | `None` |
| `table.sort(...)` | Sort stored strings | `The same Table` |
| `table.show()` | Display the current table | `None` |
| `table.finish()` | Complete live output | `None` |
| `table.to_text(...)` | Render terminal text | `str` |
| `table.to_html()` | Render notebook HTML | `str` |
| `table.to_csv(...)` | Write formatted rows | `Path` |
| `table.to_latex(...)` | Render and optionally write LaTeX | `str` |

## `Table`

Construct a table with text and HTML representations.

```python
hdg.Table(title="Analysis", columns=None, mode="static", *, formatters=None)
```

`mode` selects static or live display.

| Mode | Intermediate updates | Final redirected output |
| --- | --- | --- |
| `static` | None | Written by `show()` |
| `live` | Updated in a terminal or notebook | Written once by `finish()` |
| `dynamic` | Same behaviour as `live` | Written once by `finish()` |

| Parameter | Default | Meaning |
| --- | --- | --- |
| `title` | `"Analysis"` | Display title |
| `columns` | `None` | Column names; defaults to `Parameter`, `Value`, and `Unit` |
| `mode` | `"static"` | `static`, `live`, or `dynamic` |
| `formatters` | `None` | Mapping by column name or index, or sequence in column order |

Unknown modes raise `ValueError`. Formatters accept column names, indices or an ordered sequence; values contain format specifications or callables.

Rows contain formatted strings; retain original data for numerical analysis.

### `Table.from_dataframe`

Construct a table from selected DataFrame columns.

```python
hdg.Table.from_dataframe(
    dataframe, title="Analysis", columns=None, mode="static", *, formatters=None,
)
```

Returns an independent table without the pandas index. Missing columns raise `KeyError`; an empty selection raises `ValueError`; unsupported row interfaces raise `TypeError`. pandas and Polars are optional.

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `dataframe` | pandas or Polars DataFrame | Required | Source exposing `columns` and its native row iterator |
| `title` | `str` | `"Analysis"` | Display title |
| `columns` | iterable of `str` or `None` | `None` | Selected columns in display order; `None` uses every source column |
| `mode` | `str` | `"static"` | `static`, `live`, or `dynamic` |
| `formatters` | mapping, sequence, or `None` | `None` | Existing `Table` formatting rules |

## Example

```python
table = hdg.Table("Model comparison", columns=["Case", "Error"], formatters={"Error": ".3f"})
table.add_row("candidate", 0.0184)
table.add_row("baseline", 0.0412)
table.sort("Error", key=float)
table.show()
```

## Rows and display

```python
table.add_row(*values)
table.update_row(index, *values)
table.sort(column=0, *, reverse=False, key=None)
table.show()
table.finish()
```

Rows accept separate values or one list or tuple. Width mismatches raise `ValueError`; an invalid update index raises `IndexError`. `sort()` returns the same table and orders stored strings; use `key=float` for numeric ordering.

`show()` renders a static table. Live tables refresh during row changes and emit their final state through `finish()`; redirected output suppresses intermediate updates.

## Rendering and export

```python
table.to_text(width=None)
table.to_html()
table.to_csv(path)
table.to_latex(path=None, *, caption=None, label=None)
```

| Option | Default | Meaning |
| --- | --- | --- |
| `width` | `None` | Available terminal width for text rendering |
| `path` | Required for CSV; optional for LaTeX | Destination; missing parent directories are created |
| `caption` | `None` | Optional LaTeX caption |
| `label` | `None` | Optional LaTeX cross-reference label |

`to_text()` and `to_html()` return strings. CSV writes headers and formatted rows, returning a `Path`. LaTeX returns a string and optionally writes it; include `booktabs` in the document.

## `Table.to_dataframe`

```python
table.to_dataframe(backend="pandas")
```

| Parameter | Default | Meaning |
| --- | --- | --- |
| `backend` | `"pandas"` | `"pandas"`, `"pd"`, `"polars"`, `"pl"`, or the imported pandas/Polars module |

Returns an independent DataFrame of formatted strings in column order. Original numeric types, precision, missing-value objects and indices are unavailable.

Unknown backends raise `ValueError`; unsupported objects raise `TypeError`; missing optional libraries raise `ImportError`. Backend construction errors propagate.

```python
import pandas as pd

frame = table.to_dataframe(pd)
frame = table.to_dataframe("pl")
```

The Polars call requires Polars. Retain the original dataset for numerical analysis.
