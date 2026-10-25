"""Inside or outside legends for the current Matplotlib axes."""

from numbers import Integral
from typing import Any
import warnings

import matplotlib.pyplot as plt
from matplotlib.legend import Legend
from matplotlib.transforms import Bbox, IdentityTransform


_OUTSIDE = {
    'upper left': ('lower left', 'top', 0.),
    'upper center': ('lower center', 'top', .5),
    'upper right': ('lower right', 'top', 1.),
    'lower left': ('upper left', 'bottom', 0.),
    'lower center': ('upper center', 'bottom', .5),
    'lower right': ('upper right', 'bottom', 1.),
    'center left': ('center right', 'left', .5),
    'center right': ('center left', 'right', .5),
    'right': ('center left', 'right', .5),
    'best': ('center left', 'right', .5),
}


def _outside_placement(legend) -> tuple[str, float] | None:
    """Return managed placement; explicit anchors keep author ownership."""
    if getattr(legend, '_follow_domain', False):
        return legend._domain_side, legend._domain_alignment
    placement = getattr(legend, '_shared_placement', None)
    if placement is not None and legend._bbox_to_anchor is None:
        return placement[1], placement[2]
    return None


class _OutsideLegend(Legend):
    def __init__(self, axes, handles, labels, placement, ncol, title):
        location, self._domain_side, self._domain_alignment = placement
        self._follow_domain = True
        self._placing = True
        super().__init__(axes, handles, labels, loc=location, ncol=ncol,
                         title=title, alignment='center',
                         bbox_to_anchor=(0., 0.), bbox_transform=IdentityTransform())
        self.get_title().set_multialignment('center')
        self._placing = False

    def set_bbox_to_anchor(self, bbox, transform=None):
        if not self._placing:
            self._follow_domain = False
        return super().set_bbox_to_anchor(bbox, transform)

    def _place(self, renderer):
        if not self._follow_domain:
            return
        axes = self.axes
        box = axes.get_window_extent(renderer)
        content = axes.get_tightbbox(renderer, bbox_extra_artists=[])
        if content is None:
            content = box
        gap = renderer.points_to_pixels(4.)
        if self._domain_side == 'top':
            anchor = (box.x0 + self._domain_alignment * box.width, content.y1 + gap)
        elif self._domain_side == 'bottom':
            anchor = (box.x0 + self._domain_alignment * box.width, content.y0 - gap)
        elif self._domain_side == 'left':
            anchor = (content.x0 - gap, box.y0 + .5 * box.height)
        else:
            anchor = (content.x1 + gap, box.y0 + .5 * box.height)
        super().set_bbox_to_anchor(anchor, IdentityTransform())

    def get_window_extent(self, renderer=None):
        figure: Any = self.get_figure()
        renderer = renderer if renderer is not None else figure._get_renderer()
        self._place(renderer)
        return super().get_window_extent(renderer)

    def get_tightbbox(self, renderer=None):
        return self.get_window_extent(renderer)

    def draw(self, renderer):
        self._place(renderer)
        return super().draw(renderer)


class _SharedLegend(Legend):
    def __init__(self, figure, panels, handles, labels, loc, domain, ncol, title):
        self._panels = panels
        self._shared_domain = domain
        self._shared_placement = _OUTSIDE[loc] if domain == 'outside' else None
        best = domain == 'inside' and loc in ('best', 0)
        location: Any = self._shared_placement[0] if self._shared_placement else ('upper right' if best else loc)
        super().__init__(figure, handles, labels, loc=location, ncol=ncol,
                         title=title, alignment='center')
        self.get_title().set_multialignment('center')
        self._hedgehogs_sources = handles
        if best:
            self._loc = 0
        if self._shared_placement:
            side = self._shared_placement[1]
            self._outside_loc = {'top': 'upper', 'bottom': 'lower'}.get(side, side)

    def get_bbox_to_anchor(self):
        current: Any = self
        if current._bbox_to_anchor is not None:
            return super().get_bbox_to_anchor()
        figure: Any = self.get_figure()
        renderer = figure._get_renderer()
        panels = [ax for ax in self._panels if ax.get_visible() and ax in figure.axes]
        if not panels:
            return figure.bbox
        box = Bbox.union([ax.get_window_extent(renderer) for ax in panels])
        if self._shared_placement is None:
            return box
        content = Bbox.union([ax.get_tightbbox(renderer, bbox_extra_artists=[])
                              for ax in panels])
        _, side, alignment = self._shared_placement
        gap = renderer.points_to_pixels(4.)
        if side == 'top':
            anchor = (box.x0 + alignment * box.width, content.y1 + gap)
        elif side == 'bottom':
            anchor = (box.x0 + alignment * box.width, content.y0 - gap)
        elif side == 'left':
            anchor = (content.x0 - gap, box.y0 + .5 * box.height)
        else:
            anchor = (content.x1 + gap, box.y0 + .5 * box.height)
        return Bbox.from_bounds(*anchor, 0, 0)

    def _find_best_position(self, width, height, renderer, consider=None):
        from .presentation import _data_overlap
        box = Bbox.from_bounds(0, 0, width, height)
        container = self.get_bbox_to_anchor()
        current: Any = self
        candidates = [current._get_anchored_bbox(code, box, container, renderer)
                      for code in range(1, 11)]
        def score(point):
            bounds = Bbox.from_bounds(point[0], point[1], width, height)
            return sum(_data_overlap(ax, bounds, renderer) for ax in self._panels if ax.get_visible())
        return min(candidates, key=score)


def _entry_style(handle):
    names = ('color', 'marker', 'linestyle', 'linewidth', 'markeredgewidth',
             'facecolor', 'edgecolor', 'hatch', 'sizes', 'alpha')
    values = [(name, repr(getattr(handle, 'get_' + name)()))
              for name in names if callable(getattr(handle, 'get_' + name, None))]
    if callable(getattr(handle, 'get_paths', None)):
        values.append(('paths', repr([(path.vertices.tolist(), path.codes)
                                      for path in handle.get_paths()])))
    return values


def legend(loc: Any = 'best', domain: str = 'inside', ncol: int = 1,
           *, shared: bool = False, title: str | None = None) -> Legend:
    """Return a styled legend for the current axes, inside or outside the plot.

    Inside locations follow Matplotlib. Outside locations name the plot side:
    upper/lower locations sit above/below labels and titles, and center left/right
    sit beside them. Outside best selects the right side. ncol sets column count.
    shared collects unique labels across the current figure, aligned to its panels.
    title is centred above the legend entries, independently of column count.
    """
    aliases = {'inside': 'inside', 'in': 'inside', 'i': 'inside',
               'outside': 'outside', 'out': 'outside', 'o': 'outside'}
    if not isinstance(domain, str) or domain not in aliases:
        raise ValueError("domain must be 'inside' ('in', 'i') or 'outside' ('out', 'o').")
    domain = aliases[domain]
    if isinstance(ncol, bool) or not isinstance(ncol, Integral) or ncol < 1:
        raise ValueError('ncol must be a positive integer.')
    if not isinstance(shared, bool):
        raise TypeError('shared must be True or False.')
    if title is not None and not isinstance(title, str):
        raise TypeError('title must be a string or None.')
    if domain == 'inside' and not shared:
        result = plt.legend(loc=loc, ncol=int(ncol), title=title, alignment='center')
        result.get_title().set_multialignment('center')
        return result
    if domain == 'outside' and isinstance(loc, Integral):
        loc = next((name for name, code in Legend.codes.items() if code == loc), None)
    if domain == 'outside' and (not isinstance(loc, str) or loc not in _OUTSIDE):
        raise ValueError('Outside legends require an upper, lower, left or right location.')
    if shared:
        figure = plt.gcf()
        panels = [ax for ax in figure.axes if ax.get_visible() and not hasattr(ax, '_colorbar')]
        entries: dict[str, Any] = {}
        for ax in panels:
            handles, labels = ax.get_legend_handles_labels()
            for handle, label in zip(handles, labels):
                if label in entries:
                    if _entry_style(handle) != _entry_style(entries[label]):
                        warnings.warn(f'Shared legend label {label!r} has different styles; using the first.',
                                      UserWarning, stacklevel=2)
                else:
                    entries[label] = handle
        result = _SharedLegend(figure, panels, list(entries.values()), list(entries), loc, domain, int(ncol), title)
        for previous in list(figure.legends):
            if isinstance(previous, _SharedLegend):
                previous.remove()
        figure.legends.append(result)
        result._remove_method = figure.legends.remove
        figure.stale = True
        return result
    axes = plt.gca()
    handles, labels = axes.get_legend_handles_labels()
    result = _OutsideLegend(axes, handles, labels, _OUTSIDE[loc], int(ncol), title)
    axes.legend_ = result
    result._remove_method = axes._remove_legend
    return result
