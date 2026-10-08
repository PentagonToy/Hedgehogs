"""Small scatter-and-histogram matrices built from Matplotlib axes."""

from collections import Counter
from collections.abc import Mapping, Sequence
from math import ceil, exp, isfinite, pi, sqrt
from statistics import stdev
from numbers import Real
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator

from ..core.palette import Palette, get_palette
from . import style
from .typography import panel_scale


def _density(sample: Sequence[float], grid: Sequence[float]) -> list[float] | None:
    """Equal-weight Gaussian KDE with Scott bandwidth; no singular estimate."""
    if len(sample) < 2:
        return None
    bandwidth = stdev(sample) * len(sample) ** (-.2)
    if not isfinite(bandwidth) or bandwidth <= 0:
        return None
    counts = Counter(sample)
    normalisation = len(sample) * bandwidth * sqrt(2 * pi)
    return [sum(count * exp(-.5 * ((x - value) / bandwidth) ** 2)
                for value, count in counts.items()) / normalisation for x in grid]


def pairplot(
    data: Any,
    hue: str | None = None,
    *,
    vars: Sequence[str] | None = None,
    hue_order: Sequence[Any] | None = None,
    corner: bool = False,
    diag_kind: str = 'kde',
    bins: int = 15,
    alpha: float = .85,
    palette: str | Palette | None = None,
    figsize: tuple[float, float] | None = None,
) -> tuple[Figure, Any]:
    """Return a Matplotlib figure and square axes array for numeric columns.

    Accept a DataFrame or mapping of equally sized columns. Missing/non-finite
    numeric observations are omitted per panel. Diagonal densities use Gaussian KDE, with
    histogram fallback for singleton or constant samples. No global style is changed.
    """
    columns = list(data.keys() if isinstance(data, Mapping) else data.columns)
    if len(set(columns)) != len(columns):
        raise ValueError('Column names must be unique.')
    values = {name: list(data[name]) for name in columns}
    lengths = {len(column) for column in values.values()}
    if len(lengths) != 1 or not lengths or next(iter(lengths)) == 0:
        raise ValueError('data must contain non-empty, equally sized columns.')
    if hue is not None and hue not in values:
        raise ValueError(f'Unknown hue column: {hue!r}.')
    if isinstance(bins, bool) or not isinstance(bins, int) or bins < 1:
        raise ValueError('bins must be a positive integer.')
    if diag_kind not in ('kde', 'hist'):
        raise ValueError("diag_kind must be 'kde' or 'hist'.")
    if not isinstance(alpha, Real) or not isfinite(alpha) or not 0 <= alpha <= 1:
        raise ValueError('alpha must be finite and between zero and one.')
    if hue is None and hue_order is not None:
        raise ValueError('hue_order requires a hue column.')

    def numeric(value: Any) -> bool:
        return isinstance(value, Real) and not isinstance(value, bool) and isfinite(value)

    def missing(value: Any) -> bool:
        return value is None or type(value).__name__ in ('NAType', 'NaTType') or (
            isinstance(value, Real) and not isfinite(value))

    selected = list(vars) if vars is not None else [
        name for name, column in values.items() if name != hue
        and any(numeric(value) for value in column)
        and all(numeric(value) or missing(value) for value in column)
    ]
    if not selected or len(set(selected)) != len(selected):
        raise ValueError('vars must select at least one unique numeric column.')
    for name in selected:
        if name not in values or name == hue:
            raise ValueError(f'Invalid numeric variable: {name!r}.')
        if not any(numeric(value) for value in values[name]) or not all(
                numeric(value) or missing(value) for value in values[name]):
            raise ValueError(f'Variable {name!r} must contain numeric observations.')
    groups: dict[Any, list[int]] = {}
    for index in range(next(iter(lengths))):
        key = values[hue][index] if hue is not None else None
        if hue is not None and missing(key):
            continue
        try:
            groups.setdefault(key, []).append(index)
        except TypeError as error:
            raise ValueError('hue values must be hashable categories.') from error
    order = list(groups) if hue_order is None else list(hue_order)
    if not order or len(set(order)) != len(order) or set(order) != set(groups):
        raise ValueError('hue_order must contain every observed category exactly once.')
    colours = get_palette(palette) if palette is not None else (
        style._active_palette if style._active_palette is not None else get_palette())
    colour_values = list(colours)
    markers = ('o',)
    n = len(selected)
    fig, axes = plt.subplots(n, n, figsize=figsize or (2.24 * n, 2.2 * n),
                             sharex='col', squeeze=False, layout='constrained')
    # Outer axes describe variables by row. Diagonal densities use separate,
    # hidden inset axes so their values are never relabelled as variable values.
    for row in range(n):
        for col in range(1, n):
            axes[row, col].sharey(axes[row, 0])
    limits = {}
    for name in selected:
        finite = [float(value) for value in values[name] if numeric(value)]
        low, high = min(finite), max(finite)
        span = high - low
        pad = span * .05 if span else max(abs(low) * .05, .5)
        limits[name] = (low - pad, high + pad)
    for row, y_name in enumerate(selected):
        for col, x_name in enumerate(selected):
            ax = axes[row, col]
            if corner and col > row:
                ax.set_visible(False)
                continue
            ax._hedgehogs_fixed_scale = True
            ax.set_box_aspect(1)
            density_ax = None
            if row == col:
                density_ax = ax.inset_axes([0, 0, 1, 1])
                density_ax.sharex(ax)
                density_ax.set_axis_off()
                density_ax.patch.set_visible(False)
            low, high = limits[x_name]
            edges = [low + (high - low) * i / bins for i in range(bins + 1)]
            for group_index, key in enumerate(order):
                indices = groups[key]
                colour = colour_values[group_index % len(colour_values)]
                if row == col:
                    sample = [float(values[x_name][i]) for i in indices if numeric(values[x_name][i])]
                    if sample:
                        grid = [low + (high - low) * i / 255 for i in range(256)]
                        density = _density(sample, grid) if diag_kind == 'kde' else None
                        if density is None:
                            density_ax.hist(sample, bins=edges, density=True, color=colour,
                                    histtype='step', linewidth=plt.rcParams['lines.linewidth'], alpha=alpha)
                        else:
                            density_ax.plot(grid, density, color=colour, linewidth=plt.rcParams['lines.linewidth'], alpha=alpha)
                            density_ax.fill_between(grid, density, color=colour, alpha=.12 * alpha,
                                            edgecolor='none', linewidth=0)
                else:
                    sample = [i for i in indices if numeric(values[x_name][i]) and numeric(values[y_name][i])]
                    ax.scatter([values[x_name][i] for i in sample], [values[y_name][i] for i in sample],
                               color=colour, marker=markers[group_index % len(markers)],
                               edgecolors='black', s=plt.rcParams['lines.markersize'] ** 2,
                               linewidths=plt.rcParams['lines.markeredgewidth'], alpha=alpha)
            ax.set_xlim(*limits[x_name])
            ax.set_ylim(*limits[y_name])
            if density_ax is not None:
                density_ax.set_ylim(bottom=0)
            ax.tick_params(axis='both', which='both',
                           bottom=row == n - 1, labelbottom=row == n - 1,
                           left=col == 0, labelleft=col == 0, top=False, right=False)
            if row == n - 1:
                ax.set_xlabel(str(x_name))
            if col == 0:
                ax.set_ylabel(str(y_name))
    # Use the same locator policy in both orientations: identical variables
    # receive identical tick values, independently of label visibility.
    for col in range(n):
        axes[-1, col].xaxis.set_major_locator(MaxNLocator(nbins=4, steps=[1, 2, 2.5, 5, 10], min_n_ticks=2))
    for row in range(n):
        axes[row, 0].yaxis.set_major_locator(MaxNLocator(nbins=4, steps=[1, 2, 2.5, 5, 10], min_n_ticks=2))
    # Start from configured point sizes; fit them to solved physical panel
    # geometry below, without multiplying by the number of variables.
    typography_scale = 1.
    label_font = FontProperties(size=plt.rcParams['axes.labelsize']).get_size_in_points() * typography_scale
    x_tick_font = FontProperties(size=plt.rcParams['xtick.labelsize']).get_size_in_points() * typography_scale
    y_tick_font = FontProperties(size=plt.rcParams['ytick.labelsize']).get_size_in_points() * typography_scale
    for ax in axes.flat:
        if not ax.get_visible():
            continue
        ax.xaxis.label.set_fontsize(label_font)
        ax.yaxis.label.set_fontsize(label_font)
        ax.tick_params(axis='x', labelsize=x_tick_font)
        ax.tick_params(axis='y', labelsize=y_tick_font)
    legend_font = FontProperties(size=plt.rcParams['legend.fontsize']).get_size_in_points()
    if hue is not None:
        handles = [Line2D([], [], linestyle='none', marker=markers[i % len(markers)],
                          markerfacecolor=colour_values[i % len(colour_values)],
                          markeredgecolor='black', alpha=alpha, label=str(key)) for i, key in enumerate(order)]
        legend_options = dict(handles=handles, title=str(hue), loc='center left',
                              fontsize=legend_font,
                              title_fontsize=legend_font, borderaxespad=0)
        legend = fig.legend(**legend_options)
        renderer = fig._get_renderer()
        bounds = legend.get_window_extent(renderer)
        columns = max(1, ceil(bounds.height / (fig.bbox.height * .8)))
        if columns > 1:
            legend.remove()
            legend = fig.legend(**legend_options, ncol=columns)
            bounds = legend.get_window_extent(renderer)
        gap_inches = .12
        outer_inches = .08
        legend_width = bounds.width / fig.dpi
        if figsize is None:
            fig.set_size_inches(2.24 * n + legend_width + gap_inches + outer_inches,
                                fig.get_figheight())
        reserved = (legend_width + gap_inches + outer_inches) / fig.get_figwidth()
        right = max(.2, 1 - reserved)
        fig.get_layout_engine().set(rect=(0, 0, right, 1))
        # Use the actual grid edge rather than the canvas edge. Measure the
        # solved layout once; the anchor then follows its rightmost panel.
        fig.draw_without_rendering()
        bottom = min(ax.get_position().y0 for ax in axes.flat if ax.get_visible())
        top = max(ax.get_position().y1 for ax in axes.flat if ax.get_visible())
        panel = axes[-1, -1]
        position = panel.get_position()
        legend.set_bbox_to_anchor(
            (1 + gap_inches / (position.width * fig.get_figwidth()),
             ((bottom + top) / 2 - position.y0) / position.height),
            transform=panel.transAxes,
        )
    # Layout and typography interact: measure the panel after solving layout,
    # then settle its proportional text sizes without accumulating scaling.
    for _ in range(4):
        fig.draw_without_rendering()
        factor = max(1., min(panel_scale(ax) for ax in axes.flat if ax.get_visible()))
        for ax in axes.flat:
            if not ax.get_visible():
                continue
            ax.xaxis.label.set_fontsize(label_font * factor)
            ax.yaxis.label.set_fontsize(label_font * factor)
            ax.tick_params(axis='x', labelsize=x_tick_font * factor)
            ax.tick_params(axis='y', labelsize=y_tick_font * factor)
            for spine in ax.spines.values():
                spine.set_linewidth(plt.rcParams['axes.linewidth'] * factor)
            for collection in ax.collections:
                collection.set_sizes([plt.rcParams['lines.markersize'] ** 2 * factor ** 2])
                collection.set_linewidths([plt.rcParams['lines.markeredgewidth'] * factor])
            for child in ax.child_axes:
                for line in child.lines:
                    line.set_linewidth(plt.rcParams['lines.linewidth'] * factor)
                for patch in child.patches:
                    patch.set_linewidth(plt.rcParams['lines.linewidth'] * factor)
        if hue is not None:
            for text in legend.get_texts():
                text.set_fontsize(legend_font * factor)
            legend.get_title().set_fontsize(legend_font * factor)
            legend._fontsize = legend_font * factor
            legend_handles = getattr(legend, 'legend_handles', None)
            if legend_handles is None:
                legend_handles = legend.legendHandles
            for handle in legend_handles:
                handle.set_markersize(plt.rcParams['lines.markersize'] * plt.rcParams['legend.markerscale'] * factor)
                handle.set_markeredgewidth(plt.rcParams['lines.markeredgewidth'] * factor)
            legend_width = legend.get_window_extent(fig._get_renderer()).width / fig.dpi
            if figsize is None:
                fig.set_size_inches(2.24 * n + legend_width + gap_inches + outer_inches,
                                    fig.get_figheight())
            right = max(.2, 1 - (legend_width + gap_inches + outer_inches) / fig.get_figwidth())
            fig.get_layout_engine().set(rect=(0, 0, right, 1))
    fig.draw_without_rendering()
    if hue is not None:
        bottom = min(ax.get_position().y0 for ax in axes.flat if ax.get_visible())
        top = max(ax.get_position().y1 for ax in axes.flat if ax.get_visible())
        position = axes[-1, -1].get_position()
        legend.set_bbox_to_anchor(
            (1 + gap_inches / (position.width * fig.get_figwidth()),
             ((bottom + top) / 2 - position.y0) / position.height),
            transform=axes[-1, -1].transAxes,
        )
    return fig, axes
