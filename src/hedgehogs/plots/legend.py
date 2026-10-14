"""Inside or outside legends for the current Matplotlib axes."""

from numbers import Integral
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.legend import Legend
from matplotlib.transforms import IdentityTransform


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


class _OutsideLegend(Legend):
    def __init__(self, axes, handles, labels, placement, ncol):
        location, self._domain_side, self._domain_alignment = placement
        self._follow_domain = True
        self._placing = True
        super().__init__(axes, handles, labels, loc=location, ncol=ncol,
                         bbox_to_anchor=(0., 0.), bbox_transform=IdentityTransform())
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


def legend(loc: Any = 'best', domain: str = 'inside', ncol: int = 1) -> Legend:
    """Return a styled legend for the current axes, inside or outside the plot.

    Inside locations follow Matplotlib. Outside locations name the plot side:
    upper/lower locations sit above/below labels and titles, and center left/right
    sit beside them. Outside best selects the right side. ncol sets column count.
    """
    aliases = {'inside': 'inside', 'in': 'inside', 'i': 'inside',
               'outside': 'outside', 'out': 'outside', 'o': 'outside'}
    if not isinstance(domain, str) or domain not in aliases:
        raise ValueError("domain must be 'inside' ('in', 'i') or 'outside' ('out', 'o').")
    domain = aliases[domain]
    if isinstance(ncol, bool) or not isinstance(ncol, Integral) or ncol < 1:
        raise ValueError('ncol must be a positive integer.')
    if domain == 'inside':
        return plt.legend(loc=loc, ncol=int(ncol))
    if isinstance(loc, Integral):
        loc = next((name for name, code in Legend.codes.items() if code == loc), None)
    if not isinstance(loc, str) or loc not in _OUTSIDE:
        raise ValueError('Outside legends require an upper, lower, left or right location.')
    axes = plt.gca()
    handles, labels = axes.get_legend_handles_labels()
    result = _OutsideLegend(axes, handles, labels, _OUTSIDE[loc], int(ncol))
    axes.legend_ = result
    result._remove_method = axes._remove_legend
    return result
