# Plot API

Examples assume `import matplotlib.pyplot as plt` and `import hedgehogs as hdg`. Specialised plots create editable Matplotlib objects. `plots.show()` finishes existing figures for display.

SHAP-value drawings and SHAP integration have a separate [SHAP reference](shap.md). The Python calls remain under `hdg.plots`.

## API index

| API | Purpose | Returns |
| --- | --- | --- |
| `hdg.plots.tree(...)` | Draw a fitted decision tree | `list[Annotation]` |
| `hdg.plots.pairplot(...)` | Compare numeric variables by category | `(Figure, axes)` |
| `hdg.plots.decision_regions(...)` | Draw two-feature classification regions and samples | `Axes` |
| `hdg.plots.legend(...)` | Place the current axes legend inside or outside | `Legend` |
| `hdg.plots.show(...)` | Finish and display figures | `None` |
| `hdg.plots.save(...)` | Finish and save the current or selected figure | `tuple[Path, ...]` |

## `plots.decision_regions`

Draw a fitted classifier's regions and labelled observations on the current Matplotlib axes.

```python
hdg.plots.decision_regions(
    X, y, classifier, *, categories=None, markers=None, palette=None,
)
```

| Parameter | Default | Meaning |
| --- | --- | --- |
| `X` | Required | Two numeric feature columns, supplied as an array, list, DataFrame or mapping of columns |
| `y` | Required | One class label per row, supplied as a vector, Series or one-column table |
| `classifier` | Required | Fitted model with `predict(X)` returning one label per row |
| `categories` | `None` | Mapping from class labels to non-empty display names, such as `{0: "malignant", 1: "benign"}`; omitted labels retain their original names |
| `markers` | `None` | Marker sequence; defaults to square, filled plus, circle, upward triangle and downward triangle |
| `palette` | `None` | Palette name or `Palette`; uses the active style palette, falling back to Okabe–Ito |

Returns the current `Axes` and retains existing artists. Select another axes with `plt.sca(ax)`. Inputs require matching row counts, finite features and non-missing, hashable labels. Numeric strings in `X` are converted to floats.

Class order follows `classifier.classes_`, or first occurrence in `y` when absent. Predictions must use those classes. Colours and markers repeat as needed; filled markers have black outlines. Classifiers with `feature_names_in_` receive named DataFrame columns.

`categories` changes legend names only. Its keys must belong to the model classes; predictions and class order remain unchanged.

A 200 × 200 grid approximates the boundaries. Very narrow regions may need finer analysis. See the [drawing rules](../developer/architecture.md#specialised-drawings) for grid and opacity defaults.

Additional scatter or line data can expand the axes through Matplotlib autoscaling; the background follows the new limits. Explicit axis limits remain fixed.

```python
hdg.set_style()
ax = hdg.plots.decision_regions(X, y, classifier, markers=["o", "s", "^"])
ax.set(xlabel="Petal length [cm]", ylabel="Petal width [cm]")
ax.legend()
hdg.plots.show()
```

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

Returns text annotations. The tree replaces the axes content and fits the existing canvas, or creates a canvas when none is open. Invalid models or options raise `ValueError`.

`samples` counts observations; classifier `value` reports weighted class counts, and regression `value` reports the prediction. With `proportion=True`, samples become percentages of the root count and classifier values become proportions. `max_depth` marks omitted subtrees.

```python
hdg.set_style()
hdg.plots.tree(dt, feature_names=["length", "width"], max_depth=3)
hdg.plots.save("decision_tree.pdf")
```

Branch labels have no background fill. Connectors leave a measured gap around `True` and `False`, preserving transparent exports without white label boxes.

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

Returns `(fig, axes)` with an $n \times n$ array. `corner=True` hides upper panels. Global style is preserved; invalid selections or options raise `ValueError`.

Missing values are omitted per panel; missing `hue` values exclude the row. Each category has an independently normalised density. Singleton and constant groups use a histogram when KDE cannot estimate a distribution.

```python
hdg.set_style()
fig, axes = hdg.plots.pairplot(df, hue="species", corner=True)
hdg.plots.save("iris_pairs.pdf", fig=fig)
```

The outer y labels identify row variables. Diagonal curves use hidden density axes: their heights cannot be read from the outer ticks or compared across diagonal panels. Use separate, labelled density plots for quantitative reporting.

## `plots.legend`

Place a legend for the current axes, using Hedgehogs style defaults.

```python
hdg.plots.legend(loc="best", domain="inside", ncol=1)
```

| Parameter | Default | Meaning |
| --- | --- | --- |
| `loc` | `"best"` | Matplotlib location name or code |
| `domain` | `"inside"` | `inside` (`in`, `i`) or `outside` (`out`, `o`) |
| `ncol` | `1` | Positive column count |

Inside placement follows `plt.legend()`. Outside, `upper` locations sit above the title, `lower` locations below the x label, and `center left/right` beside the axis labels. Outside `best` selects the right side; `center` has no outside meaning.

Returns an editable `Legend`. Outside placement follows resizing and label edits. Set its `bbox_to_anchor` explicitly to take over placement.

```python
plt.plot(x, y, label="Model")
hdg.plots.legend(loc="lower center", domain="outside", ncol=3)
hdg.plots.show()
```

## `plots.show`

Finish complete figures, then display them through Matplotlib.

```python
hdg.plots.show(fig=None, *, block=None) -> None
```

| Parameter | Default | Meaning |
| --- | --- | --- |
| `fig` | `None` | Figure to finish; `None` finishes all open figures |
| `block` | `None` | Matplotlib display mode: `True`, `False`, or the backend default (`None`) |

Display follows `plt.show()`. Selecting `fig` limits finishing, although Matplotlib may display other windows. An invalid figure raises `TypeError`.

Finishing adjusts default typography, numeric ticks and supported bar-value labels. It preserves data, limits and explicit settings. Only `loc="best"` searches for an internal legend position; named locations and anchors stay fixed. Remaining bar-label collisions produce a warning.

```python
hdg.set_style()
fig, ax = plt.subplots(figsize=(7, 4.5))
bars = ax.barh(operations, times, label="Runtime")
ax.bar_label(bars, fmt="%.2f")
ax.legend()
hdg.plots.show()
```

`save()` uses the same finishing. Repeated output avoids cumulative resizing. PDF and SVG remain vector unless rasterisation is explicitly requested. [Presentation rules](../developer/presentation.md#legend-fitting-and-limits) describe fitting and reproducibility.

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

An omitted `fig` requires an open figure; otherwise saving raises `ValueError`. Invalid explicit figures raise `TypeError`. An extension selects one format; an extensionless path defaults to PDF and PNG. Conflicting or empty format selections raise `ValueError`.

Missing directories are created. Backend and filesystem errors propagate; a later export failure may leave earlier files on disk.

```python
paths = hdg.plots.save("figures/result.pdf", bbox_inches=None)
paths = hdg.plots.save("figures/result", fig=fig, formats=("pdf", "png"), bbox_inches=None)
```

## External plotting libraries

XGBoost and LightGBM importance plots can create their own axes. Call `hdg.plots.show()` afterwards; a separate `plt.subplots()` is optional.

```python
xgboost.plot_importance(model, importance_type="cover")
plt.title("Feature importance — cover")
hdg.plots.show()

lightgbm.plot_importance(model, importance_type="gain")
hdg.plots.show()
```

Finishing may enlarge an implicit canvas for dense horizontal bars, categorical heatmaps or long axis titles. Explicit sizes, resized canvases, grids, data and limits are preserved. See [Canvas expansion](../developer/presentation.md#default-canvas-fitting) for thresholds.

### Other scientific libraries

Use the original plotting function, then finish its Matplotlib figure. These libraries remain optional; Hedgehogs does not compute their statistics or replace their plotting API.

```python
sns.heatmap(correlation, annot=True, cmap="cividis")
hdg.plots.show()

ConfusionMatrixDisplay.from_predictions(y_true, y_pred)
hdg.plots.show()

dataframe.plot(secondary_y="Pressure")
hdg.plots.show()

sm.graphics.tsa.plot_acf(series)
hdg.plots.show()
```

For Seaborn figure-level plots, pass the returned figure when selecting one among several open figures: `hdg.plots.show(grid.figure)`. Native facet, joint and clustered layouts retain their explicitly selected canvas geometry. External colour maps and statistical annotations remain library-owned.

Checks cover representative Seaborn, scikit-learn, pandas and statsmodels plots. Compatibility depends on library versions and plot types. Very long labels or large category counts may need an explicit canvas.
