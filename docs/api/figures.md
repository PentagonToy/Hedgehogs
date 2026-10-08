# Figure API

Examples assume `import hedgehogs as hdg`.

## API index

| API | Purpose | Returns |
| --- | --- | --- |
| `hdg.set_style(...)` | Configure global presentation defaults | `None` |
| `hdg.reset_style()` | Restore Matplotlib defaults and methods | `None` |
| `hdg.journal_preset(...)` | Read a journal preset | `dict` |
| `hdg.set_journal_style(...)` | Apply a journal preset | `dict` |
| `hdg.figsize(...)` | Read physical figure dimensions | `(width, height)` |
| `hdg.subplots(...)` | Create a figure and axes | `(Figure, axes)` |
| `hdg.finalize(...)` | Adjust existing axes and legend styling | `None` |
| `hdg.annotate_panels(...)` | Label panels | `None` |
| `hdg.style_colorbar(...)` | Style a colour bar | `None` |
| `hdg.apply_grid(...)` | Add a major grid | `None` |
| `hdg.enable_minor_ticks(...)` | Add minor tick locators | `None` |

## Styling and layout

### `set_style`

Apply global Matplotlib presentation defaults and enable proportional sizing for newly created figures.

```python
hdg.set_style(
    base_fontsize=10.5, linewidth=1.1, figure_size=(2.24, 2.20),
    subplot=None, use_tex=False, auto_scale=False,
    scale_exponent=0.5, palette="okabe-ito",
)
```

| Parameter | Type | Default | Constraint or meaning |
| --- | --- | --- | --- |
| `base_fontsize` | `float` | `10.5` | Body-text size in points before optional width scaling |
| `linewidth` | `float` | `1.1` | Base stroke width before optional scaling |
| `figure_size` | `tuple[float, float]` | `(2.24, 2.20)` | Reference canvas width and height in inches |
| `subplot` | mapping or `None` | `None` | Overrides fixed `left`, `bottom`, `right`, or `top` fractions |
| `use_tex` | `bool` | `False` | Enable Matplotlib TeX rendering |
| `auto_scale` | `bool` | `False` | Apply the initial width-based calculation; automatic resizing operates independently |
| `scale_exponent` | `float` | `0.5` | Width-scaling exponent |
| `palette` | `str` | `"okabe-ito"` | Registered palette name |

Returns `None`. Filled markers receive black outlines unless an edge colour is supplied; unfilled markers such as `"x"` use a single stroke colour. The style applies to new Matplotlib figures. Single panels scale relative to `figure_size`; subplot grids retain configured point sizes. See [Presentation proportions](../developer/presentation.md) for the scaling rules.

### `reset_style`

Stop automatic figure sizing and restore Matplotlib defaults.

```python
hdg.reset_style() -> None
```

Returns `None`.

### `journal_preset`, `set_journal_style`, and `figsize`

Read or apply a named journal preset.

```python
hdg.journal_preset(name="science", column="single") -> dict[str, object]
hdg.set_journal_style(name="science", column="single", **overrides) -> dict[str, object]
hdg.figsize(name="science", column="single") -> tuple[float, float]
```

Supported journal names are `nature`, `science`, `ieee`, and `aps`; supported column widths are `single` and `double`. Journal typography uses stable point sizes at both column widths. `journal_preset()` returns a new dictionary containing `figure_size`, `base_fontsize`, and `linewidth`; `set_journal_style()` applies and returns those options with any `set_style()` overrides. `figsize()` returns dimensions in inches. Unknown journal names or column selections raise `ValueError`.

| Preset | Typical use | Single-column width | Double-column width |
| --- | --- | ---: | ---: |
| `nature` | Nature-family starting point | 3.50 in | 7.20 in |
| `science` | Science-family starting point | 2.24 in | 4.76 in |
| `ieee` | IEEE two-column papers | 3.50 in | 7.16 in |
| `aps` | APS journals | 3.40 in | 7.00 in |

| Parameter | Type | Default | Allowed values |
| --- | --- | --- | --- |
| `name` | `str` | `"science"` | `science`, `nature`, `ieee`, or `aps` |
| `column` | `str` | `"single"` | `single` or `double` |
| `**overrides` | keyword arguments | Empty | `set_style()` options; accepted by `set_journal_style()` only |

### `subplots`

Create a Matplotlib figure and its subplot axes.

```python
hdg.subplots(
    nrows=1, ncols=1, *, figsize=None, journal=None, column="single",
    subplot=None, gridspec_kw=None, widths=None, heights=None,
    sharex=False, sharey=False, squeeze=True, layout=None, **ax_kw,
)
```

Create ordinary Matplotlib objects. `widths` and `heights` are concise forms of GridSpec's `width_ratios` and `height_ratios`; do not supply both forms for the same dimension.

| Parameter | Default | Meaning |
| --- | --- | --- |
| `nrows`, `ncols` | `1`, `1` | Subplot grid dimensions |
| `figsize` | `None` | Explicit physical size in inches |
| `journal`, `column` | `None`, `"single"` | Optional journal-derived size |
| `subplot` | `None` | Fixed margin overrides |
| `gridspec_kw` | `None` | Matplotlib GridSpec options |
| `widths`, `heights` | `None` | Concise panel-ratio lists |
| `sharex`, `sharey` | `False` | Matplotlib shared-axis configuration |
| `squeeze` | `True` | Apply Matplotlib axes squeezing |
| `layout` | `None` | Matplotlib layout engine name |
| `**ax_kw` | Empty | Axes constructor options, passed as Matplotlib `subplot_kw` |

Returns `(fig, axes)`; axes shape follows `nrows`, `ncols`, and `squeeze`. Combining `figsize` with `journal`, or a ratio alias with its matching GridSpec key, raises `ValueError`.

For colour bars and nested axes, select `layout="constrained"`. Use `ax.set_box_aspect(1)` for a square plotting box.

```python
fig, axes = hdg.subplots(2, 2, layout="constrained")
```

### Figure finishing helpers

Adjust existing axes and colour bars without changing the plotted data.

```python
hdg.finalize(ax=None, fix_origin=True, keep="x", grid=False, minor_ticks=False)
hdg.annotate_panels(axes, labels=None, loc="upper left", offset=None, fontsize=None, fontweight="bold")
hdg.style_colorbar(cb, label=None)
hdg.apply_grid(ax=None, axis="both")
hdg.enable_minor_ticks(ax=None, x=True, y=True)
```

| Helper | Parameters and defaults | Behaviour |
| --- | --- | --- |
| `finalize()` | `ax=None` selects current axes; also accepts an axes collection; `fix_origin=True`, `keep="x"`, `grid=False`, `minor_ticks=False` | Suppress one zero tick label when both ranges include zero, style existing legend frames, and optionally add grids or minor ticks |
| `annotate_panels()` | Required `axes`; `labels=None` generates `(a)`, `(b)`, …; `loc="upper left"`; `offset=None`; `fontsize=None` uses the current font size; `fontweight="bold"` | Place labels in axes coordinates; `offset=(x, y)` overrides placement, and `loc` selects left or right alignment |
| `style_colorbar()` | Required `cb`; `label=None` preserves the existing label | Apply configured outline and tick styling |
| `apply_grid()` | `ax=None` selects current axes; `axis="both"` accepts `x`, `y`, or `both` | Add a dotted major grid beneath the plotted data |
| `enable_minor_ticks()` | `ax=None` selects current axes; `x=True`, `y=True` | Install automatic minor locators for linear axes |

All five helpers return `None`. `finalize()` styles an existing legend; it does not create one. With `keep="x"`, the y-axis zero label is suppressed; use `keep="y"` to retain the y-axis zero label. Supply one custom panel label per axes because labels and axes are paired with `zip()`.

```python
ax.legend()
hdg.finalize(ax, grid=True)
```

## Palettes

See [Palettes and series styles](palettes.md) for colour selection, series mapping and custom palette APIs.

## Specialised plots

See the [tree and pairplot reference](plots.md) for `hdg.plots.tree()` and `hdg.plots.pairplot()`.
