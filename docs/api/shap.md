# SHAP visualisation

Draw supplied single-output SHAP values with Matplotlib, without importing SHAP or requiring JavaScript. These functions return the current `Axes`; call `plots.show()` or `plots.save()` afterwards.

Examples use `import hedgehogs as hdg`. Compute attributions with an explainer first; Hedgehogs supplies the drawings. Use the [general plot API](plots.md) for figure finishing, legends and export.

| API | Purpose | Returns |
| --- | --- | --- |
| `hdg.plots.force_plot(...)` | Draw one additive explanation | `Axes` |
| `hdg.plots.summary_plot(...)` | Draw attribution importance or distributions | `Axes` |
| `hdg.plots.waterfall_plot(...)` | Show cumulative steps for one observation | `Axes` |
| `hdg.plots.dependence_plot(...)` | Compare feature values and their attributions | `Axes` |
| `hdg.plots.decision_plot(...)` | Compare cumulative attribution paths | `Axes` |

Optional `features` must match the contribution shape. DataFrame columns or Series indices supply names unless `feature_names` is explicit. Select one model output before drawing; Explanation objects, interaction arrays and multi-observation force plots are unsupported.

## `plots.force_plot`

```python
hdg.plots.force_plot(base_value, shap_values, features=None, *, feature_names=None, max_display=8)
```

Provide one finite baseline and a finite feature vector for one observation. The endpoint equals `base_value + sum(shap_values)` in the supplied units: log-odds remain log-odds. Contributions beyond `max_display` are grouped by sign, preserving the sum.

The active palette's first colour marks decreases and its second marks increases; the fallback is Okabe–Ito blue and orange. Labels connect to their segments and include feature values when supplied. Crowded labels use additional rows; narrow contributions can leave overlaps with straight leaders.

An unchanged implicit single-panel canvas expands to 7.2 × 2.6 inches. Explicit sizes and multi-panel canvases are preserved. The drawing is static; SHAP's HTML controls and interactive ordering are unavailable.

```python
hdg.plots.force_plot(explainer.expected_value, shap_values[1, :], X_test.iloc[1, :])
hdg.plots.show()
```

## `plots.summary_plot`

```python
hdg.plots.summary_plot(shap_values, features=None, *, feature_names=None, plot_type="dot", max_display=20, cmap=None)
```

Provide a finite `(observations, features)` array. Features appear in descending mean absolute SHAP value, with stable ties; features beyond `max_display` are omitted.

| Option | Behaviour |
| --- | --- |
| `plot_type="bar"` | Mean absolute SHAP value in the first palette colour |
| `plot_type="dot"` | Every observation in deterministic lanes; dense points can overlap |
| `cmap=None` | Interpolate the active palette's first two colours; fall back to Okabe–Ito when unavailable |
| `cmap` name or object | Matplotlib colormap for dot plots; ignored by bar plots |

Numeric feature colours use each feature's fifth and ninety-fifth percentiles as endpoints. Values outside that range use the endpoint colours; constant features use the low colour. Missing, infinite and non-numeric feature values appear grey. Palette access uses positions, not colour names.

Dot plots neither sample nor rasterise observations. Vertical offsets separate points; they represent no measured quantity or exact density estimate. See [drawing rules](../developer/architecture.md#specialised-drawings) for placement.

```python
hdg.plots.summary_plot(shap_values, X_test, plot_type="bar")
hdg.plots.show()

hdg.plots.summary_plot(shap_values, X_test, cmap="viridis")
hdg.plots.show()
```

See [SHAP's introduction](https://shap.readthedocs.io/en/latest/example_notebooks/overviews/An%20introduction%20to%20explainable%20AI%20with%20Shapley%20values.html) for attribution interpretation.

## `plots.waterfall_plot`

```python
hdg.plots.waterfall_plot(base_value, shap_values, features=None, *, feature_names=None, max_display=10)
```

Accepts the same finite baseline, feature vector and optional feature data as `force_plot`. Rows follow descending absolute contribution, with stable ties. If features exceed `max_display`, the final row combines all remaining contributions, reserving one display slot. `max_display=1` then shows their total. Reading from the bottom row to the top moves from the baseline to the complete additive output.

Positive and negative bars use the active palette's second and first colours. Small bar values sit outside the bar. The complete sum is retained, including cancellation in a grouped row. An unchanged implicit single-panel canvas fits the row count; explicit sizes remain unchanged.

```python
hdg.plots.waterfall_plot(explainer.expected_value, shap_values[1, :], X_test.iloc[1, :])
hdg.plots.show()
```

## `plots.dependence_plot`

```python
hdg.plots.dependence_plot(feature, shap_values, features, *, feature_names=None, color_by=None, cmap=None)
```

Supply matching `(observations, features)` arrays. `feature` selects a unique name or non-negative column index: the x coordinate is its feature value, and y is its SHAP value. Select numeric columns; encode categories explicitly. Non-finite x values are omitted, and a column without finite observations raises `ValueError`.

`color_by` optionally selects another numeric feature. Colours use that column's full finite range; missing colour values appear grey. `cmap` accepts a Matplotlib name or object and otherwise interpolates the active palette's first two colours. No interaction strength, jitter or histogram is calculated automatically.

```python
hdg.plots.dependence_plot("age", shap_values, X_test, color_by="sex", cmap="viridis")
hdg.plots.show()
```

## `plots.decision_plot`

```python
hdg.plots.decision_plot(base_value, shap_values, features=None, *, feature_names=None, feature_order=None, max_display=20, highlight=None, cmap=None)
```

Accept one feature vector or an `(observations, features)` matrix and one shared finite baseline. Each line starts at the baseline and adds contributions in a common feature order; its final coordinate equals the baseline plus the complete row sum. The top-to-bottom default order is descending mean absolute contribution, with stable ties.

`feature_order` may supply a complete permutation of names or column indices. Changing this order changes intermediate paths, not final predictions. Reuse an explicit order when comparing separate figures. `max_display` reserves a final grouped row when needed, preserving endpoints. Crowded populations require an explicit selection by the caller; the function draws every supplied observation.

`highlight` lists observation indices drawn with dashed, opaque lines. `cmap` colours paths by their final output, using the active palette's first two colours by default. Multiple paths include an output colour bar. Feature values appear in row labels only for vector input. An unchanged implicit single-panel canvas fits the row count; explicit sizes remain unchanged.

```python
hdg.plots.decision_plot(explainer.expected_value, shap_values[:20, :], X_test.iloc[:20, :], highlight=[1])
hdg.plots.show()
```

All cumulative values retain their supplied units. These functions perform no model inference, probability conversion, interaction estimation or clustering.

## Using SHAP's own plots

Pass `show=False` to SHAP plots, then finish with Hedgehogs. SHAP's canvas sizes, explicit fonts and colour maps are retained.

```python
shap.summary_plot(shap_values, X, show=False)
hdg.plots.show()

shap.dependence_plot("Age", shap_values, X, show=False)
hdg.plots.show()
```

The same sequence applies to Matplotlib-backed SHAP bar, beeswarm and waterfall plots.

For one sample, use `shap.force_plot(..., matplotlib=True, show=False)` followed by `hdg.plots.show()`. Multi-sample force plots use HTML: display with `shap.initjs()` or export with `shap.save_html()`. Notebook trust and viewer restrictions apply.

The same finishing and export functions apply to these Matplotlib figures. Multi-sample HTML output remains SHAP-owned.
