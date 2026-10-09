# Figure API

Examples assume `import matplotlib.pyplot as plt` and `import hedgehogs as hdg`. Matplotlib creates figures; Hedgehogs configures their style and provides explicit helpers.

## API index

| API | Purpose | Returns |
| --- | --- | --- |
| `hdg.set_style(...)` | Configure global presentation defaults | `None` |
| `hdg.reset_style()` | Restore Matplotlib defaults and methods | `None` |
| `hdg.figsize(...)` | Read physical figure dimensions | `(width, height)` |
| `hdg.figures.annotate_panels(...)` | Label panels | `None` |
| `hdg.figures.style_colorbar(...)` | Style a colour bar | `None` |
| `hdg.figures.apply_grid(...)` | Add a major grid | `None` |
| `hdg.figures.enable_minor_ticks(...)` | Add minor tick locators | `None` |

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

### `figsize`

Read starting canvas dimensions in inches.

```python
hdg.figsize(name="science", column="single") -> tuple[float, float]
```

| Preset | Single-column size | Double-column size |
| --- | --- | --- |
| `nature` | 3.50 × 2.65 in | 7.20 × 4.80 in |
| `science` | 2.24 × 2.20 in | 4.76 × 3.40 in |
| `ieee` | 3.50 × 2.55 in | 7.16 × 4.80 in |
| `aps` | 3.40 × 2.60 in | 7.00 × 4.80 in |

`name` defaults to `"science"` and `column` to `"single"`; names ignore case. Unknown selections raise `ValueError`. Dimensions are starting points; check the target journal's requirements. Typography is configured separately through `set_style()`.

Create figures and axes with Matplotlib:

```python
size = hdg.figsize("science", "double")
hdg.set_style(figure_size=size)
fig, axes = plt.subplots(2, 2, figsize=size, layout="constrained")
```

Use Matplotlib's `gridspec_kw`, `sharex`, `sharey` and `layout` for panel geometry. For colour bars and nested axes, select `layout="constrained"`; `ax.set_box_aspect(1)` gives a square plotting box.

## Explicit figure helpers

Adjust existing axes and colour bars without changing the plotted data.

```python
hdg.figures.annotate_panels(axes, labels=None, loc="upper left", offset=None, fontsize=None, fontweight="bold")
hdg.figures.style_colorbar(cb, label=None)
hdg.figures.apply_grid(ax=None, axis="both")
hdg.figures.enable_minor_ticks(ax=None, x=True, y=True)
```

| Helper | Parameters and defaults | Behaviour |
| --- | --- | --- |
| `annotate_panels()` | Required `axes`; `labels=None` generates `(a)`, `(b)`, …; `loc="upper left"`; `offset=None`; `fontsize=None` uses the current font size; `fontweight="bold"` | Place labels in axes coordinates; `offset=(x, y)` overrides placement, and `loc` selects left or right alignment |
| `style_colorbar()` | Required `cb`; `label=None` preserves the existing label | Apply configured outline and tick styling |
| `apply_grid()` | `ax=None` selects current axes; `axis="both"` accepts `x`, `y`, or `both` | Add a dotted major grid beneath the plotted data |
| `enable_minor_ticks()` | `ax=None` selects current axes; `x=True`, `y=True` | Install automatic minor locators for linear axes |

All four helpers return `None` and operate on existing artists. Supply one panel label per axes; omitted labels generate `(a)`, `(b)`, and so on. `style_colorbar()` preserves the label unless a replacement is supplied. `apply_grid()` and `enable_minor_ticks()` default to the current axes. Minor tick locators apply to linear axes.

```python
hdg.figures.annotate_panels(axes)
hdg.figures.apply_grid(axes[0, 0], axis="y")
hdg.plots.show(fig)
```

Use `plots.show()` or `plots.save()` for automatic finishing. Custom tick formatting remains a Matplotlib choice.

## Palettes

See [Palettes and series styles](palettes.md) for colour selection, series mapping and custom palette APIs.

## Specialised plots

See the [tree and pairplot reference](plots.md) for `hdg.plots.tree()` and `hdg.plots.pairplot()`.
