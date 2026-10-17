# Figure API

Examples assume `import matplotlib.pyplot as plt` and `import hedgehogs as hdg`. Configure shared typography and physical figure dimensions. Create figures with Matplotlib; adjust and export them through [plots](plots.md).

## API index

| API | Purpose | Returns |
| --- | --- | --- |
| `hdg.set_style(...)` | Configure global presentation defaults | `None` |
| `hdg.reset_style()` | Restore Matplotlib defaults and methods | `None` |
| `hdg.figsize(...)` | Read physical figure dimensions | `(width, height)` |
| `hdg.figures.align(figures)` | Match plotting boxes across separate figures | `None` |

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

Filled markers receive black outlines unless overridden; unfilled markers use one stroke colour. New single panels scale relative to `figure_size`, while grids retain configured point sizes. See [Presentation rules](../developer/presentation.md).

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

Use Matplotlib's `gridspec_kw`, `sharex`, `sharey` and `layout` for panel geometry. For colour bars and nested axes, select `layout="constrained"`; `hdg.plots.square(ax=ax)` gives a square plotting box.

## `figures.align`

Match the position and physical size of plotting boxes across separate figures. Supply a list or tuple of at least two distinct Matplotlib figures with the same `figsize`.

```python
figures = []
for values, title in [(Phi_gaussian, "Gaussian RBF"), (Phi_matern, "Matern C4 RBF"), (Phi_homemade, "Homemade C4 RBF")]:
    fig, ax = plt.subplots(figsize=FIG_SIZE)
    ax.plot(x_input, values)
    ax.set(xlabel="x", ylabel="y", title=title)
    figures.append(fig)

hdg.figures.align(figures=figures)
for fig, name in zip(figures, ["gaussian", "matern", "homemade"]):
    hdg.plots.save(f"{name}.png", fig=fig, transparent=True)
hdg.plots.show()
```

Each figure is finished before measuring its labels. Alignment shares the largest fitted margins, then checks for overflow with three points of outer clearance. It preserves canvas dimensions, data limits, ticks and palettes. PNG, PDF and SVG exports retain the common plotting box; tight cropping can still produce different outer file dimensions.

The initial scope is one rectilinear panel per figure without fixed data or box aspect, colourbars, inset axes, figure-level text or figure legends. Unsupported inputs raise an error. If labels leave no common plotting area or fitting does not converge, increase `figsize` or simplify labels. Returns `None`.

Align after adding data and labels, before saving. Earlier files are not updated. Reapply after changing content, layout or canvas size; resizing releases that figure's alignment. Alignment does not keep an implicit group or adjust figures outside the supplied sequence.

## Palettes

See [Palettes and series styles](palettes.md) for colour selection, series mapping and custom palette APIs.

## Specialised plots

See [Plots](plots.md) for drawing, panel labels, square boxes, legends and output.
