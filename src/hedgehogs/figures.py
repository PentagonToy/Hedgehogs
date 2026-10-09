"""Explicit adjustments to existing Matplotlib figures and axes."""

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


def _to_axes_list(ax):
    if ax is None:
        return [plt.gca()]
    if hasattr(ax, "ravel") and callable(ax.ravel):
        return ax.ravel().tolist()
    if hasattr(ax, "__iter__") and not hasattr(ax, "plot"):
        return list(ax)
    return [ax]


def apply_grid(ax=None, axis="both"):
    """Add a dotted major grid beneath the data on the selected axes."""
    if ax is None:
        ax = plt.gca()
    ax.grid(True, which="major", axis=axis,
            linestyle=":", color="black", alpha=0.7)
    ax.set_axisbelow(True)


def enable_minor_ticks(ax=None, x=True, y=True):
    """Add automatic minor ticks to selected linear axes."""
    if ax is None:
        ax = plt.gca()
    if x:
        ax.xaxis.set_minor_locator(mticker.AutoMinorLocator())
    if y:
        ax.yaxis.set_minor_locator(mticker.AutoMinorLocator())
    major_tick = ax.xaxis.get_major_ticks()[0].tick1line
    lw = major_tick.get_markeredgewidth() * 0.6
    sz = major_tick.get_markersize() * 0.5
    ax.tick_params(which="minor", direction="out",
                   length=sz, width=lw, top=True, right=True)


def style_colorbar(cb, label=None):
    """Style an existing colour bar and optionally set its label."""
    lw = cb.ax.spines["left"].get_linewidth()
    cb.outline.set_linewidth(lw)
    cb.outline.set_edgecolor("black")
    cb.ax.tick_params(
        direction="out",
        width=cb.ax.yaxis.get_major_ticks()[0].tick1line.get_markeredgewidth(),
        length=cb.ax.yaxis.get_major_ticks()[0].tick1line.get_markersize() * 0.7,
    )
    if label is not None:
        cb.set_label(label)


def annotate_panels(axes, labels=None, loc="upper left",
                    offset=None, fontsize=None, fontweight="bold"):
    """Place one label per axes, with generated (a), (b), ... labels by default."""
    axes = _to_axes_list(axes)
    if labels is None:
        labels = [f"({chr(97 + i)})" for i in range(len(axes))]
    if fontsize is None:
        fontsize = plt.rcParams["font.size"]
    if offset is not None:
        ox, oy = offset
    elif "right" in loc:
        ox, oy = 0.94, 0.93
    else:
        ox, oy = 0.06, 0.93
    ha = "right" if "right" in loc else "left"
    for a, lbl in zip(axes, labels):
        a.text(ox, oy, lbl, transform=a.transAxes,
               fontsize=fontsize, fontweight=fontweight, va="top", ha=ha)


__all__ = ["annotate_panels", "style_colorbar", "apply_grid", "enable_minor_ticks"]


def __dir__() -> list[str]:
    """List the supported figure helpers."""
    return sorted(__all__)
