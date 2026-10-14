"""Matplotlib drawings of supplied additive feature attributions."""

from collections.abc import Sequence
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.colors import Colormap, LinearSegmentedColormap, Normalize, to_rgb
from matplotlib import colormaps
from matplotlib.cm import ScalarMappable
from matplotlib.patches import Polygon
import numpy as np

from ..core.palette import get_palette
from . import style


def _colours() -> tuple[str, str]:
    palette = style._active_palette if style._active_palette is not None else get_palette()
    colours = list(palette)
    if len(colours) < 2:
        colours = list(get_palette())
    return colours[0], colours[1]


def _inputs(values: Any, features: Any, feature_names: Sequence[str] | None,
            ndim: int) -> tuple[np.ndarray, np.ndarray | None, list[str]]:
    values = np.asarray(values, dtype=float)
    if values.ndim != ndim or not values.size or not np.isfinite(values).all():
        raise ValueError(f'shap_values must be a non-empty finite {ndim}-dimensional array; select one model output first.')
    data = None if features is None else np.asarray(features)
    if data is not None and data.shape != values.shape:
        raise ValueError('features must have the same shape as shap_values.')
    if feature_names is None:
        columns = getattr(features, 'columns' if ndim == 2 else 'index', None)
        feature_names = list(columns) if columns is not None and not callable(columns) else None
    names = ([str(name) for name in feature_names] if feature_names is not None
             else [f'Feature {i + 1}' for i in range(values.shape[-1])])
    if len(names) != values.shape[-1]:
        raise ValueError('feature_names must contain one name per feature.')
    return values, data, names


def _display_limit(max_display: int) -> None:
    if isinstance(max_display, bool) or not isinstance(max_display, int) or max_display < 1:
        raise ValueError('max_display must be a positive integer.')


def force_plot(base_value: Any, shap_values: Any, features: Any = None, *,
               feature_names: Sequence[str] | None = None, max_display: int = 8) -> Axes:
    """Draw one additive explanation without SHAP or JavaScript.

    Contributions retain their supplied output units. The endpoint equals
    base_value + sum(shap_values); omitted features are grouped by sign.
    """
    values, data, names = _inputs(shap_values, features, feature_names, 1)
    base = np.asarray(base_value, dtype=float)
    if base.size != 1 or not np.isfinite(base).all():
        raise ValueError('base_value must contain one finite value; select one model output first.')
    _display_limit(max_display)
    baseline = float(base.reshape(-1)[0])
    output = baseline + float(values.sum())
    if not np.isfinite(output):
        raise ValueError('The additive model output must be finite.')
    order = np.argsort(-np.abs(values), kind='stable')
    selected = set(order[:max_display].tolist())
    groups: list[list[tuple[float, str]]] = [[], []]
    for sign, positive in enumerate((True, False)):
        remaining = []
        for i in order:
            value = float(values[i])
            if value == 0 or (value > 0) != positive:
                continue
            if i in selected:
                label = names[i]
                if data is not None:
                    item = data[i]
                    label += f'={item:.3g}' if isinstance(item, (float, int, np.number)) else f'={item}'
                groups[sign].append((value, label))
            else:
                remaining.append(value)
        if remaining:
            groups[sign].append((sum(remaining), f'{len(remaining)} other features'))
    span = max(float(np.abs(values).sum()), abs(output - baseline), 1e-6)
    ax = plt.gca()
    blue, orange = _colours()
    figure = ax.figure
    while not isinstance(figure, Figure):
        figure = figure.figure
    default_canvas = getattr(figure, '_hedgehogs_default_canvas', None)
    if len(figure.axes) == 1 and default_canvas is not None and np.allclose(figure.get_size_inches(), default_canvas):
        figure.set_size_inches(7.2, 2.6, forward=False)
    extent = [baseline, output, output - float(values[values > 0].sum()),
              output - float(values[values < 0].sum())]
    lower, upper = min(extent) - span * .08, max(extent) + span * .08
    ax.set_xlim(lower, upper)
    labels = []
    for positive, entries, colour in zip((True, False), groups, (orange, blue)):
        # Put the strongest contribution nearest the final output.
        entries = list(reversed(entries))
        cursor = output - sum(v for v, _ in entries)
        if entries:
            ax.add_patch(Polygon([(cursor, -.16), (output, -.16),
                                  (output, .16), (cursor, .16)],
                                 closed=True, facecolor=colour, edgecolor='none'))
        for index, (value, label) in enumerate(entries):
            end = cursor + value
            if index < len(entries) - 1:
                tip = min(abs(value) * .22, abs(entries[index + 1][0]) * .22, span * .012)
                direction = 1 if positive else -1
                ax.plot([end - direction * tip, end, end - direction * tip], [-.16, 0, .16],
                        color='white', alpha=.65, linewidth=1.1, solid_capstyle='butt')
            labels.append(((cursor + end) / 2, label, colour))
            cursor = end
    # Pack label intervals into rows in screen units; leaders retain their
    # original segment centres when labels move away from a narrow segment.
    fontsize = float(plt.rcParams['font.size'])
    width_points = figure.get_figwidth() * 72 * ax.get_position().width
    rows: list[list[tuple[float, float]]] = []
    for centre, label, colour in sorted(labels, key=lambda item: item[0]):
        label_width = min(.95 * (upper - lower),
                          max(map(len, label.splitlines())) * fontsize * .55 / width_points * (upper - lower))
        x = float(np.clip(centre, lower + label_width / 2, upper - label_width / 2))
        interval = (x - label_width / 2, x + label_width / 2)
        row = 0
        gap = (upper - lower) * .025
        while row < len(rows) and any(interval[0] < right + gap and interval[1] > left - gap
                                      for left, right in rows[row]):
            row += 1
        if row == len(rows):
            rows.append([])
        rows[row].append(interval)
        y = -.85 - row * .45
        ax.plot([centre, centre, x], [-.16, y + .12, y + .06], color=colour, alpha=.6, linewidth=.6)
        ax.text(x, y, label, ha='center', va='top', color=colour, fontsize=fontsize)
    ax.plot([output, output], [-.18, .65], color='black', linewidth=1)
    ax.plot([baseline, baseline], [-.16, -.45], color='0.4', linewidth=.7)
    ax.text(baseline, -.52, f'Base {baseline:.4g}', ha='center', va='top', fontsize=fontsize)
    ax.text(output, .7, f'Output {output:.4g}', ha='center', va='bottom', fontsize=fontsize)
    ax.text(.01, .98, 'Higher →', transform=ax.transAxes, color=orange, va='top', fontsize=fontsize)
    ax.text(.99, .98, '← Lower', transform=ax.transAxes, color=blue, ha='right', va='top', fontsize=fontsize)
    ax.set_ylim(-1 - max(1, len(rows)) * .45, 1.3)
    ax.set_yticks([])
    ax.set_xlabel('')
    ax.xaxis.tick_top()
    ax.spines['top'].set_position(('data', .22))
    for side in ('left', 'right', 'bottom'):
        ax.spines[side].set_visible(False)
    return ax


def summary_plot(shap_values: Any, features: Any = None, *,
                 feature_names: Sequence[str] | None = None, plot_type: str = 'dot',
                 max_display: int = 20, cmap: str | Colormap | None = None) -> Axes:
    """Draw mean absolute importance or a deterministic attribution swarm.

    Values have shape (observations, features) for one model output. No points
    are sampled or rasterised. Non-numeric/missing feature values are grey.
    """
    values, data, names = _inputs(shap_values, features, feature_names, 2)
    _display_limit(max_display)
    if plot_type not in ('bar', 'dot'):
        raise ValueError("plot_type must be 'bar' or 'dot'.")
    importance = np.mean(np.abs(values), axis=0)
    order = np.argsort(-importance, kind='stable')[:max_display]
    blue, orange = _colours()
    colour_map = (LinearSegmentedColormap.from_list('hedgehogs-feature-value', [blue, orange])
                  if cmap is None else colormaps.get_cmap(cmap))
    ax = plt.gca()
    coloured = False
    if plot_type == 'bar':
        ax.barh(np.arange(len(order)), importance[order], color=blue)
        ax.set_xlabel('Mean absolute SHAP value')
    else:
        ax.axvline(0, color='0.55', linewidth=.7, zorder=0)
        for row, index in enumerate(order):
            x = values[:, index]
            # Stable bins and alternating lanes make redraws independent of RNG.
            width = float(np.ptp(x))
            bins = np.floor((x - x.min()) / (width or 1) * 80).astype(int)
            positions = np.argsort(bins, kind='stable')
            sorted_bins = bins[positions]
            starts = np.maximum.accumulate(np.where(np.r_[True, np.diff(sorted_bins) != 0],
                                                    np.arange(len(x)), 0))
            rank = np.arange(len(x)) - starts
            lanes = np.where(rank % 2, (rank + 1) // 2, -(rank // 2))
            offsets = np.empty(len(x), dtype=float)
            offsets[positions] = lanes / max(1, int(np.abs(lanes).max())) * .32
            numeric = np.full(len(x), np.nan)
            if data is not None:
                for i, item in enumerate(data[:, index]):
                    try:
                        numeric[i] = float(item)
                    except (TypeError, ValueError):
                        pass
            valid = np.isfinite(numeric)
            if valid.any():
                low, high = np.percentile(numeric[valid], [5, 95])
                colours = np.clip((numeric[valid] - low) / (high - low or 1), 0, 1)
                ax.scatter(x[valid], row + offsets[valid], c=colours, cmap=colour_map,
                           vmin=0, vmax=1, s=12, alpha=.8, edgecolors='none')
                coloured = True
            if (~valid).any():
                ax.scatter(x[~valid], row + offsets[~valid], color='0.55', s=12,
                           alpha=.8, edgecolors='none')
        ax.set_xlabel('SHAP value (impact on model output)')
        if coloured:
            bar = ax.figure.colorbar(ScalarMappable(norm=Normalize(0, 1), cmap=colour_map), ax=ax, pad=.03)
            bar.set_ticks([0, 1], labels=['Low', 'High'])
            bar.set_label('Feature value (within each feature)')
    ax.set_yticks(np.arange(len(order)), labels=[names[i] for i in order])
    ax.set_ylim(len(order) - .5, -.5)
    return ax


def _baseline(base_value: Any) -> float:
    base = np.asarray(base_value, dtype=float)
    if base.size != 1 or not np.isfinite(base).all():
        raise ValueError('base_value must contain one finite value; select one model output first.')
    return float(base.reshape(-1)[0])


def _feature_index(feature: str | int, names: list[str]) -> int:
    if isinstance(feature, str):
        if names.count(feature) != 1:
            raise ValueError('The selected feature name must identify exactly one column.')
        return names.index(feature)
    if isinstance(feature, (int, np.integer)) and not isinstance(feature, bool) and 0 <= feature < len(names):
        return int(feature)
    raise ValueError('Select a feature by its name or a non-negative column index.')


def _fit_attribution_canvas(ax: Axes, rows: int) -> None:
    figure = ax.figure
    if not isinstance(figure, Figure) or len(figure.axes) != 1:
        return
    default = getattr(figure, '_hedgehogs_default_canvas', None)
    if default is not None and np.allclose(figure.get_size_inches(), default):
        figure.set_size_inches(6, max(3, .32 * rows + 1.2), forward=False)


def waterfall_plot(base_value: Any, shap_values: Any, features: Any = None, *,
                   feature_names: Sequence[str] | None = None, max_display: int = 10) -> Axes:
    """Draw one explanation as cumulative signed steps, retaining its full sum."""
    values, data, names = _inputs(shap_values, features, feature_names, 1)
    base = _baseline(base_value)
    _display_limit(max_display)
    order = np.argsort(-np.abs(values), kind='stable')
    count = len(values) if len(values) <= max_display else max_display - 1
    displayed = values[order[:count]].tolist()
    labels = [names[i] + (f'={data[i]:.3g}' if isinstance(data[i], (int, float, np.number))
                         else f'={data[i]}') if data is not None else names[i] for i in order[:count]]
    if count < len(values):
        displayed.append(float(values[order[count:]].sum()))
        labels.append(f'{len(values) - count} other features')
    # Start with the least prominent row; the largest individual effect is at the top.
    steps = np.asarray(displayed)[::-1]
    positions = np.r_[base, base + np.cumsum(steps)]
    if not np.isfinite(positions).all():
        raise ValueError('Cumulative model outputs must be finite.')
    ax = plt.gca()
    _fit_attribution_canvas(ax, len(steps))
    low, high = _colours()
    ax.barh(np.arange(len(steps)), np.abs(steps), left=np.minimum(positions[:-1], positions[1:]),
            color=[high if value >= 0 else low for value in steps], height=.6)
    extent = max(float(np.ptp(positions)), 1e-6)
    for row, value in enumerate(steps):
        colour = high if value >= 0 else low
        luminance = float(np.dot(to_rgb(colour), [.2126, .7152, .0722]))
        small = abs(value) < extent * .12
        x = max(positions[row], positions[row + 1]) + extent * .015 if small else (positions[row] + positions[row + 1]) / 2
        ax.text(x, row, f'{value:+.3g}', ha='left' if small else 'center', va='center',
                color='black' if small or luminance > .5 else 'white', fontsize=plt.rcParams['xtick.labelsize'])
        if row < len(steps) - 1:
            ax.plot([positions[row + 1]] * 2, [row + .3, row + .7], color='0.5', linewidth=.7)
    ax.set_yticks(np.arange(len(steps)), labels=labels[::-1])
    ax.set_ylim(-1.1, len(steps) + .5)
    ax.text(base, -.65, f'Base {base:.4g}', ha='center', va='top', fontsize=plt.rcParams['font.size'])
    ax.text(positions[-1], len(steps) - .25, f'Output {positions[-1]:.4g}', ha='center', va='bottom', fontsize=plt.rcParams['font.size'])
    ax.set_xlabel('Model output')
    ax.margins(x=.15)
    return ax


def dependence_plot(feature: str | int, shap_values: Any, features: Any, *,
                    feature_names: Sequence[str] | None = None,
                    color_by: str | int | None = None, cmap: str | Colormap | None = None) -> Axes:
    """Draw feature values against their attributions; colouring is explicit."""
    values, data, names = _inputs(shap_values, features, feature_names, 2)
    if data is None:
        raise ValueError('features is required for dependence_plot.')
    index = _feature_index(feature, names)
    colour_index = None if color_by is None else _feature_index(color_by, names)
    low, high = _colours()
    colour_map = (LinearSegmentedColormap.from_list('hedgehogs-feature-value', [low, high])
                  if cmap is None else colormaps.get_cmap(cmap))
    try:
        x = np.asarray(data[:, index], dtype=float)
        colours = None if colour_index is None else np.asarray(data[:, colour_index], dtype=float)
    except (TypeError, ValueError) as error:
        raise ValueError('Selected feature and colour columns must be numeric; encode categories explicitly.') from error
    valid = np.isfinite(x)
    if not valid.any():
        raise ValueError('The selected feature has no finite observations.')
    ax = plt.gca()
    if colours is None:
        ax.scatter(x[valid], values[valid, index], color=low, s=16, alpha=.8, edgecolors='none')
    else:
        coloured = valid & np.isfinite(colours)
        if coloured.any():
            points = ax.scatter(x[coloured], values[coloured, index], c=colours[coloured],
                                cmap=colour_map, s=16, alpha=.8, edgecolors='none')
            bar = ax.figure.colorbar(points, ax=ax, pad=.03)
            assert colour_index is not None
            bar.set_label(names[colour_index])
        missing = valid & ~np.isfinite(colours)
        if missing.any():
            ax.scatter(x[missing], values[missing, index], color='0.55', s=16, alpha=.8, edgecolors='none')
    ax.set(xlabel=names[index], ylabel=f'SHAP value for {names[index]}')
    return ax


def decision_plot(base_value: Any, shap_values: Any, features: Any = None, *,
                  feature_names: Sequence[str] | None = None,
                  feature_order: Sequence[str | int] | None = None, max_display: int = 20,
                  highlight: Sequence[int] | None = None, cmap: str | Colormap | None = None) -> Axes:
    """Compare cumulative attribution paths using one common feature order."""
    raw = np.asarray(shap_values, dtype=float)
    ndim = 1 if raw.ndim == 1 else 2
    values, data, names = _inputs(raw, features, feature_names, ndim)
    matrix = values[None, :] if ndim == 1 else values
    base = _baseline(base_value)
    _display_limit(max_display)
    if feature_order is None:
        order = np.argsort(-np.mean(np.abs(matrix), axis=0), kind='stable').tolist()
    else:
        order = [_feature_index(feature, names) for feature in feature_order]
        if sorted(order) != list(range(matrix.shape[1])):
            raise ValueError('feature_order must contain every feature exactly once.')
    selected = [] if highlight is None else list(highlight)
    if any(isinstance(i, bool) or not isinstance(i, (int, np.integer)) or not 0 <= i < len(matrix) for i in selected):
        raise ValueError('highlight must contain valid observation indices.')
    count = len(order) if len(order) <= max_display else max_display - 1
    contributions = matrix[:, order[:count]]
    labels = [names[i] for i in order[:count]]
    if ndim == 1 and data is not None:
        labels = [f'{name}={data[i]}' for name, i in zip(labels, order[:count])]
    if count < len(order):
        contributions = np.column_stack([contributions, matrix[:, order[count:]].sum(axis=1)])
        labels.append(f'{len(order) - count} other features')
    paths = np.column_stack([np.full(len(matrix), base), base + np.cumsum(contributions, axis=1)])
    if not np.isfinite(paths).all():
        raise ValueError('Cumulative model outputs must be finite.')
    low, high = _colours()
    colour_map = (LinearSegmentedColormap.from_list('hedgehogs-model-output', [low, high])
                  if cmap is None else colormaps.get_cmap(cmap))
    output = paths[:, -1]
    minimum, maximum = float(output.min()), float(output.max())
    if minimum == maximum:
        minimum, maximum = minimum - .5, maximum + .5
    norm = Normalize(minimum, maximum)
    ax = plt.gca()
    _fit_attribution_canvas(ax, len(labels) + 1)
    for row, path in enumerate(paths):
        ax.plot(path, np.arange(len(path)), color=colour_map(norm(output[row])),
                alpha=1 if row in selected else .7, linestyle='--' if row in selected else '-')
    ax.set_yticks(np.arange(len(labels) + 1), labels=['Base'] + labels)
    ax.set_ylim(len(labels) + .3, -.3)
    ax.set_xlabel('Cumulative model output (supplied units)')
    if len(paths) > 1:
        bar = ax.figure.colorbar(ScalarMappable(norm=norm, cmap=colour_map), ax=ax, pad=.03)
        bar.set_label('Final model output')
    return ax
