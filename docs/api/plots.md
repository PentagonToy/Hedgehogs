# Plot API

Examples assume `import matplotlib.pyplot as plt` and `import hedgehogs as hdg`. Specialised plots create editable Matplotlib objects. `plots.show()` finishes existing figures for display.

SHAP-value drawings and SHAP integration have a separate [SHAP reference](shap.md). The Python calls remain under `hdg.plots`.

## API index

| API | Purpose | Returns |
| --- | --- | --- |
| `hdg.plots.tree(...)` | Draw a fitted decision tree | `list[Annotation]` |
| `hdg.plots.pairplot(...)` | Compare numeric variables by category | `(Figure, axes)` |
| `hdg.plots.decision_regions(...)` | Draw two-feature classification regions and samples | `Axes` |
| `hdg.plots.label(...)` | Add or update panel labels with optional halos and boxes | `list[Text]` |
| `hdg.plots.square(...)` | Set or release square plotting boxes | `None` |
| `hdg.plots.annotate_panels(...)` | Place explicit panel annotations | `None` |
| `hdg.plots.style_colorbar(...)` | Style a colour bar | `None` |
| `hdg.plots.apply_grid(...)` | Add a major grid | `None` |
| `hdg.plots.enable_minor_ticks(...)` | Add minor tick locators | `None` |
| `hdg.plots.legend(...)` | Place a panel or shared legend inside or outside | `Legend` |
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

Draw a fitted, single-output decision tree without Graphviz. Text follows the configured `font.serif` fallback list. With `set_style()`, DejaVu Serif is used when Times New Roman and Times are unavailable; installing Times is optional.

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

Branch labels preserve transparent exports.

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

## `plots.label`

```python
hdg.plots.label(
    labels=None, *, bullets="a", axes=None, loc="upper left",
    halo=True, box=False, color=None, fontsize=None, fontweight="bold",
)
```

Add one label per visible panel, excluding colour bars. Accept a single axes or nested grid without flattening. Repeated calls update the labels and return editable text artists.

| Option | Default | Meaning |
| --- | --- | --- |
| `labels` | `None` | Panel names; omitted names show bullets only |
| `bullets` | `"a"` | `a)`, `b)`, …; `"1"` gives numbers; `None` preserves literal labels |
| `axes` | `None` | Current figure panels, or explicit axes/grid in display order |
| `loc` | `"upper left"` | Upper, centre or lower position, such as `"lower right"` |
| `halo` | `True` | Contrasting text outline |
| `box` | `False` | Borderless, translucent white background; independent of `halo` |
| `color` | `None` | Automatic black/white contrast, or an explicit Matplotlib colour |
| `fontsize` | `None` | Shared typography, or an explicit positive point size |
| `fontweight` | `"bold"` | Matplotlib font weight |

Automatic contrast includes the axes background, images and optional box. Set `color` for complex backgrounds. Supply one name per selected panel; invalid counts raise `ValueError`.

```python
hdg.plots.label(["Data", "AND", "OR", "NAND"], halo=True, box=False)
hdg.plots.show()

# Box without a halo; updates the existing labels
hdg.plots.label(["Data", "AND", "OR", "NAND"], halo=False, box=True)
```

## `plots.square`

```python
hdg.plots.square(enabled=True, *, ax=None) -> None
```

Make plotting boxes square without changing `figsize` or requesting equal data units. Resizing refits them within the available space.

By default, select all current-figure panels except colour bars. Pass `ax` to select one panel or an axes grid. `False` clears the constraint; other non-boolean values raise `TypeError`. Existing data-aspect settings remain active.

```python
hdg.plots.square()                 # All panels
hdg.plots.square(ax=axes[0, 0])     # One panel
hdg.plots.square(False)            # Release all panels
```

Default single-panel vertical colour bars follow the plotting-box height. Custom placement, shared or horizontal bars and extension markers retain Matplotlib behaviour.

## Other adjustments

Adjust existing axes and colour bars without changing the plotted data.

```python
hdg.plots.annotate_panels(
    axes, labels=None, loc="upper left", offset=None,
    fontsize=None, fontweight="bold",
)
hdg.plots.style_colorbar(cb, label=None)
hdg.plots.apply_grid(ax=None, axis="both")
hdg.plots.enable_minor_ticks(ax=None, x=True, y=True)
```

| Helper | Parameters and defaults | Behaviour |
| --- | --- | --- |
| `annotate_panels()` | Required `axes`; `labels=None` generates `(a)`, `(b)`, …; `loc="upper left"`; `offset=None`; `fontsize=None` uses the current font size; `fontweight="bold"` | Place labels in axes coordinates; `offset=(x, y)` overrides placement, and `loc` selects left or right alignment |
| `style_colorbar()` | Required `cb`; `label=None` preserves the existing label | Apply configured outline and tick styling |
| `apply_grid()` | `ax=None` selects current axes; `axis="both"` accepts `x`, `y`, or `both` | Add a dotted major grid beneath the plotted data |
| `enable_minor_ticks()` | `ax=None` selects current axes; `x=True`, `y=True` | Install automatic minor locators for linear axes |

All four helpers return `None` and edit existing artists. Supply one label per panel.

```python
hdg.plots.annotate_panels(axes)
hdg.plots.apply_grid(axes[0, 0], axis="y")
hdg.plots.show(fig)
```

Use `plots.show()` or `plots.save()` for automatic finishing. Custom tick formatting remains a Matplotlib choice.

## `plots.legend`

Place a legend for the current axes or share one across panels.

```python
hdg.plots.legend(loc="best", domain="inside", ncol=1, *, shared=False, title=None)
```

| Parameter | Default | Meaning |
| --- | --- | --- |
| `loc` | `"best"` | Matplotlib location name or code |
| `domain` | `"inside"` | `inside` (`in`, `i`) or `outside` (`out`, `o`) |
| `ncol` | `1` | Positive column count |
| `shared` | `False` | Collect unique labels across visible panels in the current figure, excluding colour bars |
| `title` | `None` | Title centred above the entries, for any column count |

Returns an editable `Legend`. Outside `upper` and `lower` locations clear titles and labels; `center left/right` sit beside them. Outside `best` selects the right side; `center` is invalid. Placement follows resizing; an explicit `bbox_to_anchor` takes control.

`shared=True` deduplicates labels in panel order and centres on the panel grid. Marker styles follow the plotted data. Conflicting styles warn and use the first; existing panel legends remain. Single-panel figures also work.

Default inside legends fit a bounded space budget, including shared legends, while preserving axis typography and panel geometry. Automatic outside legends fit a canvas-based budget without changing the requested location or column count; long default axis labels limit text enlargement to preserve plotting space. Marker and patch outlines follow the plotted sources. Explicit font sizes and anchors remain under user control.

```python
# Current panel
hdg.plots.legend(loc="upper right")

# Common legend above all panels
hdg.plots.legend(loc="upper center", domain="outside", ncol=2, shared=True, title="Output")
hdg.plots.show()
```

## `plots.show`

Finish and display the selected figure, or all open figures when omitted.

```python
hdg.plots.show(fig=None, *, block=None) -> None
```

| Parameter | Default | Meaning |
| --- | --- | --- |
| `fig` | `None` | Figure to finish and display; `None` selects all open figures |
| `block` | `None` | Matplotlib display mode: `True`, `False`, or the backend default (`None`) |

With no selection, display follows `plt.show()`. With `fig`, only that figure is displayed. Other GUI windows stay open. An invalid figure raises `TypeError`.

In Jupyter inline mode, selecting a figure displays only that figure and clears the current open-figure list by default. Earlier plots therefore do not reappear in the next cell's `plt.show()` or `plots.show()`. Retained Figure objects remain available for saving or explicit display:

```python
hdg.plots.show(fig=fig_gaussian)
hdg.plots.show()  # No remaining figures from that batch.
hdg.plots.show(fig=fig_matern)  # The object remains available.
```

An explicit `InlineBackend.close_figures=False` setting keeps figures open. Selected display suppresses the pending cell-end flush; new plotting calls can schedule another automatic flush. `block` has no effect in inline mode.

For GUI backends, `block=True` waits until the selected window closes; `False` returns immediately and requires the environment to process GUI events. The default follows interactive/IPython mode. Non-GUI backends do not enter a GUI event loop, even with `block=True`.

Finishing adjusts default typography, automatic numeric ticks and supported bar-value labels while preserving data, limits and explicit settings. On 3D axes, it bounds font scaling, spaces axis labels and fits labels inside the canvas. Automatic linear ticks use projected lengths, omit endpoints and reduce density when labels overlap. Explicit fonts, label padding and tick locators stay unchanged. Only `loc="best"` searches for an internal legend position; named locations and anchors stay fixed. Remaining bar-label collisions produce a warning.

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

Bar-end labels created with Matplotlib’s `bar_label()` receive measured space on automatically scaled axes during finishing. Explicit axis limits remain unchanged.
