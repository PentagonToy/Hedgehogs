"""Render deterministic notebook-inspired figures without a Jupyter kernel.

Run from the repository: python tools/render_figures.py OUTPUT_DIRECTORY
Uses synthetic data; no research datasets or model checkpoints are required.
"""

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

import hedgehogs as hdg


def render(output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    hdg.set_style()
    palette = hdg.get_palette()
    width, height = hdg.figsize()
    rng = np.random.default_rng(42)
    x = np.linspace(0, 10, 100)
    y = x ** 2 + rng.normal(0, 10, x.size)
    prediction = np.polyval(np.polyfit(x, y, 1), x)

    for explicit in (False, True):
        fig, ax = plt.subplots(figsize=(width * 1.5, height * 1.5))
        options = {"s": 20} if explicit else {}
        ax.scatter(x, y, color=palette["blue"], alpha=.7,
                   label="Training Data", **options)
        ax.plot(x, prediction, color=palette["black"], label="Fitted Line (Numpy)")
        ax.set(title="Toy Example: Linear Fit to Quadratic Data", xlabel="X", ylabel="y")
        ax.legend()
        fig.tight_layout()
        save(fig, output, "toy_explicit" if explicit else "toy_default")

    fig, axes = plt.subplots(3, 5, figsize=(width * 3.5, height * 2),
                             sharex=True, sharey=True, layout="constrained")
    coordinate = np.linspace(0, 1, 40)
    X, Y = np.meshgrid(coordinate, coordinate)
    for row, panels in enumerate(axes):
        for column, ax in enumerate(panels):
            field = np.exp(-((X - .2 - .1 * column)**2 + (Y - .2 - .25 * row)**2) / .025)
            image = ax.imshow(field, origin="lower", extent=(0, 1, 0, 1), rasterized=True)
            ax.set_box_aspect(1)
            if row == 0:
                ax.set_title(("PaSR", r"$\beta$-Presumed", "Marginal", "Joint", "LRF")[column])
            if column == 0:
                ax.set_ylabel(r"$c$")
            if row == 2:
                ax.set_xlabel(r"$Z$")
        fig.colorbar(image, ax=panels, pad=.01).set_label(r"$P(Z,c)$")
    save(fig, output, "shared_colourbars")

    fig, axes = plt.subplots(2, 2, figsize=(width * 1.5, height * 1.5),
                             sharex=True, sharey=True, layout="constrained")
    actual = rng.uniform(400, 2200, 2000)
    for ax in axes.flat:
        ax.scatter(actual, actual + rng.normal(0, 100, actual.size), s=2,
                   alpha=.3, color=palette["black"], rasterized=True)
        ax.plot([400, 2200], [400, 2200], color=palette["red"], linestyle="--")
        ax.set_box_aspect(1)
    for ax in axes[-1]:
        ax.set_xlabel(r"PaSR $\langle T\rangle$ [K]")
    for ax in axes[:, 0]:
        ax.set_ylabel(r"Predicted $\langle T\rangle$ [K]")
    save(fig, output, "dense_scatter")

    fig, ax = plt.subplots(figsize=(5, 5))
    ax.set_aspect("equal")
    ax.axis("off")
    x = np.linspace(0, 4, 200)
    ax.plot(x, (x - 3)**2 / 4 + .5, color=palette["blue"], linewidth=2.2)
    ax.scatter([.5, 1.5, 2.5], [2.0625, 1.0625, .5625], s=75, color="black")
    ax.annotate("", xy=(2.5, .5625), xytext=(1.5, 1.0625),
                arrowprops={"arrowstyle": "-|>", "mutation_scale": 14})
    ax.text(3.5, 2, r"$\nabla f(x)$", fontsize=20)
    fig.tight_layout()
    save(fig, output, "explicit_diagram")
    hdg.reset_style()


def save(fig, output: Path, name: str) -> None:
    for suffix in ("png", "pdf", "svg"):
        fig.savefig(output / f"{name}.{suffix}", dpi=300, transparent=True)
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    render(parser.parse_args().output)
