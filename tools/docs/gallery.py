"""Render committed gallery examples explicitly from the checked-out package."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import hedgehogs as hdg


def example(palette_name, output):
    size = hdg.figsize("science", "single")
    hdg.set_style(figure_size=size, palette=palette_name)
    colours = hdg.get_palette(palette_name)
    matplotlib.rcParams["svg.hashsalt"] = "hedgehogs-gallery"
    x = np.linspace(0, 1, 25)
    y = 2 * x + 0.1 * np.sin(20 * x)
    fig, ax = plt.subplots(figsize=size)
    ax.scatter(x, y, color=colours[0], label="Data")
    ax.plot(x, 2 * x, color=colours[1], label="Model")
    ax.set(xlabel="x", ylabel="y")
    ax.legend()
    hdg.plots.save(output, fig=fig, bbox_inches=None, metadata={"Date": None})
    output.write_text("\n".join(line.rstrip() for line in output.read_text().splitlines()) + "\n")
    plt.close(fig)
    hdg.reset_style()


if __name__ == "__main__":
    destination = ROOT / "docs/assets/gallery"
    destination.mkdir(parents=True, exist_ok=True)
    for palette in ("okabe-ito", "paul-tol-bright", "ibm"):
        example(palette, destination / f"{palette}.svg")
