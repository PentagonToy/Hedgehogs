# Plot API

Examples assume `import matplotlib.pyplot as plt` and `import hedgehogs as hdg`. Tree and pairplot create editable Matplotlib objects. `plots.show()` finishes existing figures for display.

## API index

| API | Purpose | Returns |
| --- | --- | --- |
| `hdg.plots.tree(...)` | Draw a fitted decision tree | `list[Annotation]` |
| `hdg.plots.pairplot(...)` | Compare numeric variables by category | `(Figure, axes)` |
| `hdg.plots.show(...)` | Finish and display figures | `None` |
| `hdg.plots.save(...)` | Finish and save the current or selected figure | `tuple[Path, ...]` |

## `plots.tree`

Draw a fitted, single-output decision tree without Graphviz.

```python
hdg.plots.tree(
    decision_tree, *, max_depth=None, feature_names=None, class_names=None,
    label="all", impurity=True, node_ids=False, proportion=False,
    precision=3, ax=None, fontsize=None,
)
```

| Parameter | Default | Meaning |
| --- | --- | --- |
| `decision_tree` | Required | Fitted scikit-learn classifier or regressor |
| `max_depth` | `None` | Display depth; non-negative integer, or `None` for the complete tree |
| `feature_names` | `None` | Names in feature order; defaults to `x[index]` |
| `class_names` | `None` | Names in `classes_` order; `None` hides the class line |
| `label` | `"all"` | Field labels at every node (`"all"`), the root (`"root"`), or nowhere (`"none"`) |
| `impurity` | `True` | Show node impurity |
| `node_ids` | `False` | Show node indices |
| `proportion` | `False` | Show sample percentages and class proportions instead of counts |
| `precision` | `3` | Decimal places; non-negative integer |
| `ax` | `None` | Destination axes; defaults to the current axes or a new figure |
| `fontsize` | `None` | Positive base font size before fitting; defaults to the configured body size |

Returns the text annotations. The function clears the destination axes and retains an existing canvas size. Without an open figure, it creates a canvas that fits the tree. Invalid models, selections, or options raise `ValueError`.

`samples` counts observations; classifier `value` reports weighted class counts, and regression `value` reports the prediction. With `proportion=True`, samples become percentages of the root count and classifier values become proportions. `max_depth` marks omitted subtrees.

```python
hdg.set_style()
hdg.plots.tree(dt, feature_names=["length", "width"], max_depth=3)
plt.savefig("decision_tree.pdf")
```

## `plots.pairplot`

Compare numeric variables with scatter panels and diagonal density curves.

```python
hdg.plots.pairplot(
    data, hue=None, *, vars=None, hue_order=None, corner=False,
    diag_kind="kde", bins=15, alpha=0.85, palette=None, figsize=None,
)
```

| Parameter | Default | Meaning |
| --- | --- | --- |
| `data` | Required | DataFrame or mapping of equally sized, non-empty columns |
| `hue` | `None` | Category column; `None` draws one group |
| `vars` | `None` | Numeric columns in display order; `None` selects numeric, non-boolean columns except `hue` |
| `hue_order` | `None` | Every observed category, once each; defaults to first-occurrence order |
| `corner` | `False` | Show the diagonal and lower triangle only |
| `diag_kind` | `"kde"` | Gaussian density curves (`"kde"`) or outlined histograms (`"hist"`) |
| `bins` | `15` | Positive histogram bin count, also used for KDE fallback |
| `alpha` | `0.85` | Point and line opacity from `0` to `1` |
| `palette` | `None` | Palette name or `Palette`; defaults to the active style, then Okabe–Ito |
| `figsize` | `None` | Canvas width and height in inches; `None` sizes the matrix and legend automatically |

Returns `(fig, axes)` with an $n \times n$ axes array. Upper-triangle axes remain present but hidden when `corner=True`. The function preserves global style. Invalid columns, category order, bins, or opacity raise `ValueError`.

Missing values are omitted per panel; missing `hue` values exclude the row. Each category has an independently normalised density. Singleton and constant groups use a histogram when KDE cannot estimate a distribution.

```python
hdg.set_style()
fig, axes = hdg.plots.pairplot(df, hue="species", corner=True)
fig.savefig("iris_pairs.pdf")
```

The outer y labels identify row variables. Diagonal curves use hidden density axes: their heights cannot be read from the outer ticks or compared across diagonal panels. Use separate, labelled density plots for quantitative reporting.

See [Figures](figures.md) for style and export guidance, and [Presentation proportions](../developer/presentation.md) for layout and scaling rules.

## `plots.show`

Finish complete figures, then display them through Matplotlib.

```python
hdg.plots.show(fig=None, *, block=None) -> None
```

| Parameter | Default | Meaning |
| --- | --- | --- |
| `fig` | `None` | Figure to finish; `None` finishes all open figures |
| `block` | `None` | Matplotlib display mode: `True`, `False`, or the backend default (`None`) |

Returns `None`; an invalid `fig` raises `TypeError`. Display follows `plt.show()`, including notebook and interactive-backend behaviour. A selected `fig` limits finishing; Matplotlib can still display other open windows.

Finishing restores point-sized bases, refines default typography and numeric tick density, compares legend positions, and separates supported bar-value labels along their bars. Data, axis limits, and category order remain unchanged. Explicit font options, custom tick locators and legend anchors retain their settings. Only `loc="best"` requests automatic search within the axes. Named locations and explicit anchors remain fixed; outside placement requires `bbox_to_anchor`. A warning reports remaining bar-label collisions.

```python
hdg.set_style()
fig, ax = plt.subplots(figsize=(7, 4.5))
bars = ax.barh(operations, times, label="Runtime")
ax.bar_label(bars, fmt="%.2f")
ax.legend()
hdg.plots.show()
```

`hdg.plots.save()` applies the same finishing step. Unchanged repeated output retains its layout; edits reopen measurement without cumulative resizing. Ordinary `plt.show()` uses the ordinary styled-rendering policy. Finishing neither rasterises nor subsamples points; PDF and SVG output stays vector unless rasterisation is explicitly requested. See [Presentation rules](../developer/presentation.md#legend-fitting-and-limits) for fitting and reproducibility.

## `plots.save`

Export a figure to one or more files.

```python
hdg.plots.save(
    filename, *, fig=None, formats=None, dpi=300, transparent=False,
    bbox_inches="tight", metadata=None, close=False, **savefig_kw,
)
```

Finish the figure, write each requested format, and return paths in format order. The finishing step matches `hdg.plots.show()`; see the [show reference](plots.md#plotsshow).

| Parameter | Default | Meaning |
| --- | --- | --- |
| `fig` | `None` | Figure to save; `None` selects the current pyplot figure |
| `filename` | Required | Output filename, or a path without an extension for multiple formats |
| `formats` | `None` | Without an extension: format name or non-empty iterable; `None` writes PDF and PNG |
| `dpi` | `300` | Raster resolution |
| `transparent` | `False` | Transparent figure and axes backgrounds |
| `bbox_inches` | `"tight"` | Crop to content; `None` preserves the canvas dimensions |
| `metadata` | `None` | Format-specific metadata |
| `close` | `False` | Close the figure after all exports succeed |
| `**savefig_kw` | Empty | Additional Matplotlib `savefig()` options |

Without a current figure, omitted `fig` raises `ValueError` without creating an empty figure. An invalid explicit figure raises `TypeError`. An extension selects one format and preserves the filename. Without an extension, `formats=None` writes PDF and PNG. Supplying both an extension and `formats`, an empty format list, or a Matplotlib `format` override raises `ValueError`. Missing parent directories are created; backend and filesystem errors propagate. Exports are sequential, so a later failure can leave earlier files on disk.

```python
paths = hdg.plots.save("figures/result.pdf", bbox_inches=None)
paths = hdg.plots.save("figures/result", fig=fig, formats=("pdf", "png"), bbox_inches=None)
```
