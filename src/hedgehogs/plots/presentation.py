"""Finish complete figures before display or export.

Use Matplotlib's renderer for measurement and a bounded candidate search for
legend placement. Keep author sizes and scientific coordinates unchanged.
"""

from itertools import combinations
from hashlib import blake2b
from typing import Any
import warnings

import matplotlib.pyplot as plt
from matplotlib.container import BarContainer
from matplotlib.axes import Axes
from matplotlib.collections import LineCollection, QuadMesh
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties
from matplotlib.text import Annotation, Text
from matplotlib.transforms import Bbox


def _area(box: Any) -> float:
    return max(0., box.width) * max(0., box.height)


def _overlap(first: Any, second: Any) -> float:
    intersection = Bbox.intersection(first, second)
    return 0. if intersection is None else _area(intersection)


def _visible_texts(fig: Any, renderer: Any, excluded: set[Any]) -> list[Any]:
    ordered = fig.findobj(match=Text)
    texts = set(ordered) - excluded
    for ax in fig.findobj(match=Axes):
        if not ax.get_visible():
            texts.difference_update(ax.findobj(match=Text))
            continue
        for axis in (ax.xaxis, ax.yaxis):
            active = set(axis._update_ticks()) if ax.axison else set()
            for tick in (*axis.majorTicks, *axis.minorTicks):
                if tick not in active:
                    texts.discard(tick.label1)
                    texts.discard(tick.label2)
            if not ax.axison:
                texts.discard(axis.label)
    return [text.get_window_extent(renderer) for text in ordered
            if text in texts and text.get_visible() and text.get_text()]


def _legend_location(legend: Any, location: Any) -> None:
    setter = getattr(legend, 'set_loc', None)
    if setter is None:
        setter = legend._set_loc
    setter(location)


def _data_overlap(ax: Any, box: Any, renderer: Any) -> float:
    score = sum(_overlap(box, patch.get_window_extent(renderer))
                for patch in ax.patches if patch.get_visible())
    score += sum(_overlap(box, image.get_window_extent(renderer))
                 for image in ax.images if image.get_visible())
    for line in ax.lines:
        if line.get_visible() and line.get_path().transformed(line.get_transform()).intersects_bbox(box, filled=False):
            score += _area(box) * .1
    for collection in ax.collections:
        if not collection.get_visible() or not hasattr(collection, 'get_offsets'):
            continue
        if isinstance(collection, LineCollection):
            score += sum(path.transformed(collection.get_transform()).intersects_bbox(box, filled=False)
                         for path in collection.get_paths()) * _area(box) * .1
            continue
        if isinstance(collection, QuadMesh):
            mesh = ax.transData.transform_bbox(collection.get_datalim(ax.transData))
            score += _overlap(box, mesh)
            continue
        points = collection.get_offset_transform().transform(collection.get_offsets())
        score += sum(box.contains(*point) for point in points) * _area(box) * .01
    return score


def _place_legend(fig: Any, ax: Any, renderer: Any) -> None:
    legend = ax.get_legend()
    if (legend is None or not legend.get_visible() or legend._bbox_to_anchor is not None
            or legend._loc != 0):
        return  # Only loc="best" requests automatic placement.
    excluded = set(legend.findobj())
    texts = _visible_texts(fig, renderer, excluded)
    best_location, best_score = 0, None
    for location in range(11):
        _legend_location(legend, location)
        box = legend.get_window_extent(renderer)
        area = max(_area(box), 1.)
        score = (max(0., area - _overlap(box, ax.bbox)) / area,
                 sum(_overlap(box, text) for text in texts) / area,
                 _data_overlap(ax, box, renderer) / area,
                 0 if location == 0 else 1)
        if best_score is None or score < best_score:
            best_location, best_score = location, score
    _legend_location(legend, best_location)
    legend._hedgehogs_finish_last_loc = best_location
    legend._hedgehogs_finish_requested_loc = 0
    legend._hedgehogs_finish_anchor = None
    # Data overlap is a placement preference, not a warning condition.
    if best_score is not None and best_score[0] > 1e-6:
        warnings.warn('Legend does not fit inside the axes; choose an explicit external anchor or a larger canvas.',
                      UserWarning, stacklevel=3)


def _bar_annotations(ax: Any) -> list[Any]:
    endpoints = []
    for container in ax.containers:
        if not isinstance(container, BarContainer):
            continue
        horizontal = container.orientation == 'horizontal'
        for patch in container.patches:
            endpoints.append((patch.get_x() + patch.get_width(), patch.get_y() + patch.get_height() / 2)
                             if horizontal else (patch.get_x() + patch.get_width() / 2,
                                                 patch.get_y() + patch.get_height()))
    return [text for text in ax.texts if isinstance(text, Annotation)
            and text.get_visible() and text.xycoords == 'data' and text.anncoords == 'offset points'
            and any(abs(text.xy[0] - x) < 1e-9 and abs(text.xy[1] - y) < 1e-9 for x, y in endpoints)]


def _bar_collisions(fig: Any, renderer: Any) -> int:
    return sum(_overlap(first.get_window_extent(renderer), second.get_window_extent(renderer)) > 0
               for ax in fig.axes for first, second in combinations(_bar_annotations(ax), 2))


def _separate_bar_labels(fig: Any, renderer: Any) -> None:
    for ax in fig.axes:
        labels = _bar_annotations(ax)
        placed: list[Any] = []
        for label in labels:
            position = label.get_position()
            box = label.get_window_extent(renderer)
            if not any(_overlap(box, other) for other in placed):
                placed.append(box)
                continue
            direction = 1 if label.get_ha() != 'right' else -1
            horizontal = label.get_ha() in ('left', 'right')
            # Move outward along the bar, retaining its endpoint and row.
            step = (box.width if horizontal else box.height) * 72 / fig.dpi + 2
            best, best_score = position, None
            for offset in (0, .5, 1., 1.5, 2.):
                candidate = (position[0] + direction * offset * step, position[1]) if horizontal else (
                    position[0], position[1] + (1 if label.get_va() != 'top' else -1) * offset * step)
                label.set_position(candidate)
                measured = label.get_window_extent(renderer)
                score = (_area(measured) - _overlap(measured, fig.bbox),
                         sum(_overlap(measured, other) for other in placed), offset)
                if best_score is None or score < best_score:
                    best, best_score = candidate, score
            label.set_position(best)
            placed.append(label.get_window_extent(renderer))


def _retain_edits(fig: Any) -> None:
    state = getattr(fig, '_hedgehogs_style', None)
    if state is None:
        return
    names = {'fontsize', 'linewidth', 'linewidths', 'markersize', 'markeredgewidth', 'sizes'}
    for owner, properties in list(state.values.items()):
        for key in list(properties):
            if not key.startswith(('major.', 'minor.')):
                continue
            which, name = key.split('.', 1)
            options = getattr(owner, '_' + which + '_tick_kw', {})
            if name not in options:
                continue
            value = options[name]
            if name == 'labelsize' and isinstance(value, str):
                value = FontProperties(size=value).get_size_in_points()
            current = state._values(value)
            _, last, _ = properties[key]
            if current != last:
                properties[key] = (current, current, 1.)
                if name == 'labelsize' and 'finish_role.labelsize' in properties:
                    properties['finish_role.labelsize'] = None
        for name in names.intersection(properties):
            getter = getattr(owner, 'get_' + name, None)
            if getter is None:
                continue
            current = state._values(getter())
            _, last, _ = properties[name]
            if current != last:
                properties[name] = (current, current, 1.)
                role = 'finish_role.' + name
                if role in properties:
                    properties[role] = None


def _signature(fig: Any) -> tuple[Any, ...]:
    """Track supported geometry and author edits without retaining data copies."""
    def digest(value: Any) -> bytes:
        return blake2b(value.tobytes(), digest_size=16).digest()

    parts: list[Any] = [tuple(fig.get_size_inches()), fig.dpi, id(fig.get_layout_engine())]
    parts.extend((id(text), text.get_text(), str(text.get_fontproperties()), text.get_visible())
                 for text in fig.findobj(match=Text))
    parts.extend((id(text), repr(text.get_position())) for text in fig.texts)
    for ax in fig.axes:
        parts.append((id(ax), tuple(ax.get_xlim()), tuple(ax.get_ylim()),
                      tuple(round(float(value), 10) for value in ax.get_position().bounds),
                      ax.get_visible(), ax.xaxis.labelpad, ax.yaxis.labelpad))
        parts.extend((id(text), repr(text.get_position()), text.get_ha(), text.get_va()) for text in ax.texts)
        parts.extend((id(line), digest(line.get_xydata()), line.get_linewidth(),
                      line.get_markersize(), line.get_visible(), line.get_alpha()) for line in ax.lines)
        for collection in ax.collections:
            sizes = digest(collection.get_sizes()) if hasattr(collection, 'get_sizes') else None
            segments = tuple(digest(segment) for segment in collection.get_segments()) if isinstance(collection, LineCollection) else None
            parts.append((id(collection), digest(collection.get_offsets()), sizes, segments,
                          collection.get_visible(), repr(collection.get_alpha())))
        renderer = fig._get_renderer()
        parts.extend((id(patch), tuple(round(float(value), 8) for value in patch.get_window_extent(renderer).bounds),
                      patch.get_linewidth(), patch.get_visible(), patch.get_alpha()) for patch in ax.patches)
        legend = ax.get_legend()
        if legend is not None:
            parts.append((legend._loc, tuple(round(float(value), 8) for value in legend.get_bbox_to_anchor().bounds)))
    return tuple(parts)


def prepare(fig: Figure) -> None:
    """Finish a figure in place; repeated calls do not rescale its artists."""
    if not isinstance(fig, Figure):
        raise TypeError('fig must be a Matplotlib Figure.')
    target: Any = fig
    # Restore point-sized bases from the existing style cache. This is an
    # explicit finishing choice; ordinary plt.show() retains legacy sizing.
    if (getattr(target, '_hedgehogs_finish_layout_locked', False)
            and getattr(target, '_hedgehogs_finish_signature', None) == _signature(target)):
        target.canvas.draw()
        if target._hedgehogs_finish_signature == _signature(target):
            return
    # Revisit automatically anchored legends, while retaining author anchors.
    for ax in target.axes:
        legend = ax.get_legend()
        if (legend is not None and legend._bbox_to_anchor is None
                and getattr(legend, '_hedgehogs_finish_requested_loc', None) == 0
                and legend._loc == getattr(legend, '_hedgehogs_finish_last_loc', None)):
            _legend_location(legend, 0)
        if (legend is not None and getattr(legend, '_hedgehogs_finish_anchor', None) is not None
                and legend._bbox_to_anchor is legend._hedgehogs_finish_anchor):
            legend.set_bbox_to_anchor(None)
            _legend_location(legend, legend._hedgehogs_finish_requested_loc)
    from matplotlib.layout_engine import PlaceHolderLayoutEngine
    engine = target.get_layout_engine()
    if (isinstance(engine, PlaceHolderLayoutEngine)
            and engine is getattr(target, '_hedgehogs_finish_frozen_engine', None)):
        engine = getattr(target, '_hedgehogs_finish_engine', engine)
    if engine is not None:
        target.set_layout_engine(engine)
    target._hedgehogs_finish_layout_locked = False
    _retain_edits(target)
    target._hedgehogs_finished = True
    state = getattr(target, '_hedgehogs_style', None)
    ordinary = all(getattr(ax, 'get_subplotspec', lambda: None)() is not None
                   and not any(getattr(artist, '_hedgehogs_fixed_size', False) for artist in ax.findobj())
                   for ax in target.axes)
    if (state is not None and state.manage_margins and ordinary
            and (engine is None or isinstance(engine, PlaceHolderLayoutEngine))):
        keys = ('left', 'right', 'bottom', 'top', 'wspace', 'hspace')
        state.values.setdefault(target, {}).setdefault(
            'layout_base', {key: getattr(target.subplotpars, key) for key in keys})
    target.canvas.draw()
    renderer = target._get_renderer()
    if state is not None:
        from .typography import refine_presentation
        refine_presentation(target, state, _bar_annotations)
        target.canvas.draw()
        renderer = target._get_renderer()
    _separate_bar_labels(target, renderer)
    for ax in target.axes:
        _place_legend(target, ax, renderer)
    target._hedgehogs_finish_engine = engine
    if engine is not None:
        target.set_layout_engine('none')
    target._hedgehogs_finish_frozen_engine = target.get_layout_engine()
    target._hedgehogs_finish_layout_locked = True
    target.canvas.draw()
    if _bar_collisions(target, target._get_renderer()):
        warnings.warn('Bar value labels still overlap; increase the canvas or adjust their positions.',
                      UserWarning, stacklevel=2)
    target._hedgehogs_finish_signature = _signature(target)


def show(fig: Figure | None = None, *, block: bool | None = None) -> None:
    """Finish the selected figure (or all open figures), then display them."""
    if fig is not None:
        prepare(fig)
    else:
        from matplotlib._pylab_helpers import Gcf
        for manager in Gcf.get_all_fig_managers():
            prepare(manager.canvas.figure)
    plt.show(block=block)
