"""Matplotlib plotting helpers."""

import math
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


class _SkipZeroFormatter(mticker.ScalarFormatter):
    def __call__(self, x, pos=None):
        return "" if math.isclose(x, 0.0, rel_tol=1e-5, abs_tol=1e-8) else super().__call__(x, pos)


def _to_axes_list(ax):
    if ax is None:
        return [plt.gca()]
    if hasattr(ax, "ravel") and callable(ax.ravel):
        return ax.ravel().tolist()
    if hasattr(ax, "__iter__") and not hasattr(ax, "plot"):
        return list(ax)
    return [ax]


def _fix_origin_overlap(ax=None, keep="x"):
    if ax is None:
        ax = plt.gca()
    xlim, ylim = ax.get_xlim(), ax.get_ylim()
    if not (xlim[0] <= 0 <= xlim[1] and ylim[0] <= 0 <= ylim[1]):
        return
    target = ax.yaxis if keep == "x" else ax.xaxis
    current = target.get_major_formatter()
    if isinstance(current, (mticker.ScalarFormatter, _SkipZeroFormatter)):
        fmt = _SkipZeroFormatter()
        try:
            fmt.set_useOffset(current.get_useOffset())
            fmt.set_useMathText(current.get_useMathText())
        except AttributeError:
            pass
        target.set_major_formatter(fmt)


def _apply_grid(ax=None, axis="both"):
    if ax is None:
        ax = plt.gca()
    ax.grid(True, which="major", axis=axis,
            linestyle=":", color="black", alpha=0.7)
    ax.set_axisbelow(True)


def _fix_legend_frame(ax=None):
    if ax is None:
        ax = plt.gca()
    leg = ax.get_legend()
    if leg is not None:
        frame = leg.get_frame()
        frame.set_linewidth(ax.spines["left"].get_linewidth())
        frame.set_edgecolor(plt.rcParams.get("legend.edgecolor", "black"))


def _enable_minor_ticks(ax=None, x=True, y=True):
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


def _style_colorbar(cb, label=None):
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


def _annotate_panels(axes, labels=None, loc="upper left",
                     offset=None, fontsize=None, fontweight="bold"):
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


def _finalize(ax=None, fix_origin=True, keep="x",
              grid=False, minor_ticks=False):
    for a in _to_axes_list(ax):
        if fix_origin:
            _fix_origin_overlap(a, keep=keep)
        _fix_legend_frame(a)
        if grid:
            _apply_grid(a)
        if minor_ticks:
            _enable_minor_ticks(a)


finalize           = _finalize


style_colorbar     = _style_colorbar


annotate_panels    = _annotate_panels


enable_minor_ticks = _enable_minor_ticks


apply_grid         = _apply_grid
