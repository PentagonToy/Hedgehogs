# Hedgehogs

<p align="center">
  <a href="https://github.com/PentagonToy/Hedgehogs/blob/main/others/assets/icon.svg">
    <img src="https://raw.githubusercontent.com/PentagonToy/Hedgehogs/main/others/assets/icon.svg?revision=06f2afbe7a60" alt="Hedgehogs logo and wordmark, with blue accents" width="270">
  </a>
</p>

**Scientific figures and reports for Python.**

[Documentation](https://pentagontoy.github.io/Hedgehogs/) · [Installation](https://pentagontoy.github.io/Hedgehogs/installation/) · [API](https://pentagontoy.github.io/Hedgehogs/api/)

Hedgehogs prepares Matplotlib figures and presents tables, progress and status messages in notebooks and terminals.

- Journal-oriented figure presets for single- and double-column layouts.
- Colour-blind-friendly palettes, such as Okabe–Ito, Paul Tol and IBM schemes.
- Consistent figure dimensions across local and remote notebook display and export.
- Clear tables, status messages and progress bars in notebooks, terminals and redirected logs.

## Installation

Requires **Python 3.10+**.

```bash
pip install hedgehogs
```

## Usage Example

### Figures

Choose the journal dimensions first, then draw with Matplotlib. The style supplies typography, line widths, marker sizes and outlines; finishing measures the complete figure and adjusts supported legend and bar-label placement.

```python
import numpy as np
import matplotlib.pyplot as plt
import hedgehogs as hdg

fig_x, fig_y = hdg.figsize(name="science", column="single")
palette = hdg.get_palette("okabe-ito")
hdg.set_style(figure_size=(fig_x, fig_y), palette="okabe-ito")

x = np.linspace(0, 1, 25)
y = 2 * x + 0.1 * np.sin(20 * x)
fitted = np.polyval(np.polyfit(x, y, 1), x)

fig, ax = plt.subplots(figsize=(fig_x, fig_y))
ax.scatter(x, y, color=palette["blue"], label="Data")
ax.plot(x, fitted, color=palette["black"], label="Linear fit")
ax.set(xlabel="x", ylabel="y")
ax.legend()

hdg.plots.save("linear_fit.pdf", bbox_inches=None)
hdg.plots.show()
```

`figsize()` returns width and height in inches for `science`, `nature`, `ieee` or `aps`, with `single` or `double` columns. Presets provide starting dimensions; check the target journal's author instructions. Use an extensionless path with `formats=("pdf", "png")` for multiple outputs. Matplotlib arguments and artist properties remain editable.

[Tree diagrams and pairplots](https://github.com/PentagonToy/Hedgehogs/blob/main/docs/api/plots.md) also return editable Matplotlib objects. Keep text readable at the final document width; select fewer variables or split crowded figures before reducing font size.

### Tables

Display the same table in a notebook or terminal, then export its formatted values to CSV and LaTeX.

```python
table = hdg.Table("Model comparison", columns=["Case", "RMSE"], formatters={"RMSE": ".3f"})
table.add_row("baseline", 0.0412)
table.add_row("model", 0.0184)
table.show()
table.to_csv("errors.csv")
table.to_latex("errors.tex", caption="Model errors", label="tab:errors")
```

`Table.from_dataframe()` accepts existing **pandas** and **Polars** DataFrames. The LaTeX output requires `booktabs`. Tables or accompanying data provide precise values; figures communicate patterns and comparisons.

### Progress

Wrap an iterable with `Progress` to report progress in notebooks, terminals and redirected logs.

```python
import time

for step in hdg.Progress(range(20), desc="Processing"):
    time.sleep(0.05)
```

For manually advanced work, `Progress` supports `update()`, metric reporting through `set()` and a context manager. See the [progress reference](https://github.com/PentagonToy/Hedgehogs/blob/main/docs/api/terminal.md#progress).

### Terminal output

```python
hdg.echo("Reading data", tone="info")
hdg.echo("Run completed", tone="success")
hdg.rule("Summary")
```

Terminal output includes colour where supported. Redirected output remains plain; `NO_COLOR` and `TERM=dumb` disable colour.

## Documentation and tutorials

Read the [documentation site](https://pentagontoy.github.io/Hedgehogs/) for installation, first use, a gallery and API references.

Use the [documentation roadmap](https://github.com/PentagonToy/Hedgehogs/blob/main/docs/README.md) for guides, API references and developer documentation. Runnable tutorials cover [plots](https://github.com/PentagonToy/Hedgehogs/blob/main/tutorials/plots.ipynb), [tables](https://github.com/PentagonToy/Hedgehogs/blob/main/tutorials/tables.ipynb), and [CLI output](https://github.com/PentagonToy/Hedgehogs/blob/main/tutorials/cli.ipynb).

Existing Onsaemiro code can replace its import with `import hedgehogs as hdg`. Wrap iterable work with `hdg.Progress(iterable, ...)` and use the standard `time.sleep()` for delays.
