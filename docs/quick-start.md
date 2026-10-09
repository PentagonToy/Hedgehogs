# First figure

Choose physical dimensions, draw with Matplotlib, then finish the figure with Hedgehogs. This example uses synthetic data and the default Okabe–Ito palette.

```python
import numpy as np
import matplotlib.pyplot as plt
import hedgehogs as hdg

size = hdg.figsize("science", "single")
hdg.set_style(figure_size=size, palette="okabe-ito")
colours = hdg.get_palette("okabe-ito")
x = np.linspace(0, 1, 25)
y = 2 * x + 0.1 * np.sin(20 * x)

fig, ax = plt.subplots(figsize=size)
ax.scatter(x, y, color=colours[0], label="Data")
ax.plot(x, 2 * x, color=colours[1], label="Model")
ax.set(xlabel="x", ylabel="y")
ax.legend()

hdg.plots.save("first-figure.svg", fig=fig, bbox_inches=None)
hdg.plots.show(fig=fig)
```

`save()` and `show()` apply the same finishing step. The example saves a vector SVG in the current directory and displays the figure through Matplotlib's active backend. Change the file extension to PDF for publication. Figure objects remain editable; use `hdg.reset_style()` to restore Matplotlib defaults.

Compare [gallery examples](gallery.md), choose a [palette](api/palettes.md), or inspect the [figure](api/figures.md) and [plot](api/plots.md) references. For non-graphical output, start with [tables](api/tables.md) or [progress](api/terminal.md).
