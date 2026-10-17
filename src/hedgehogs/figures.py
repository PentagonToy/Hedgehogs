"""Cross-figure alignment and compatibility imports for plotting helpers."""

from collections.abc import Iterable
from typing import Any

import numpy as np
from matplotlib.figure import Figure

from .plots.presentation import prepare
from .plots.helpers import (
    annotate_panels, style_colorbar, apply_grid, enable_minor_ticks, square,
)

__all__ = ["align", 'annotate_panels', 'style_colorbar', 'apply_grid', 'enable_minor_ticks', 'square']


def __dir__() -> list[str]:
    return sorted(__all__)


def _align_axis_labels(figures: list[Any]) -> None:
    # Keep native automatic positioning: adjust physical padding, not coordinates.
    for name, coordinate, sides in [('xaxis', 1, ('bottom', 'top')),
                                     ('yaxis', 0, ('left', 'right'))]:
        for side in sides:
            labels = []
            for fig in figures:
                axis = getattr(fig.axes[0], name)
                if (axis._autolabelpos and axis.get_label_position() == side
                        and axis.label.get_visible() and axis.label.get_text()):
                    anchor = axis.label.get_transform().transform(axis.label.get_position())
                    labels.append((fig, axis, anchor[coordinate] / fig.dpi))
            if len(labels) < 2:
                continue
            outward = -1 if side in ('bottom', 'left') else 1
            target = max(outward * position for _, _, position in labels)
            for _, axis, position in labels:
                axis.labelpad += max(0., target - outward * position) * 72


def align(figures: Iterable[Figure]) -> None:
    """Align plotting boxes and automatic axis labels before saving.

    Colourbars, fixed aspect ratios and figure-level decorations are excluded.
    Reapply after changing labels, data, layout or canvas size.
    """
    selected: list[Any] = list(figures)
    if len(selected) < 2:
        raise ValueError('align requires at least two figures.')
    if any(not isinstance(fig, Figure) for fig in selected):
        raise TypeError('figures must contain Matplotlib Figure objects.')
    if len({id(fig) for fig in selected}) != len(selected):
        raise ValueError('Each figure must appear only once.')
    size = selected[0].get_size_inches()
    for fig in selected:
        if not np.allclose(fig.get_size_inches(), size, rtol=0, atol=1e-9):
            raise ValueError('Aligned figures must have the same figsize.')
        if (len(fig.axes) != 1 or fig.axes[0].name != 'rectilinear'
                or fig.axes[0].child_axes or hasattr(fig.axes[0], '_colorbar')
                or fig.axes[0].get_box_aspect() is not None
                or fig.axes[0].get_aspect() != 'auto' or fig.texts or fig.legends):
            raise ValueError('align supports one rectilinear panel per figure, without fixed aspect, colourbars or figure decorations.')
    previous = [(fig.axes[0].get_position().frozen(),
                 getattr(fig, '_hedgehogs_aligned_layout', None),
                 fig.axes[0].xaxis.labelpad, fig.axes[0].yaxis.labelpad) for fig in selected]
    try:
        for fig in selected:
            fig.__dict__.pop('_hedgehogs_aligned_layout', None)
            prepare(fig)
        positions = [fig.axes[0].get_position() for fig in selected]
        edges = np.array([max(p.x0 for p in positions), max(p.y0 for p in positions),
                          min(p.x1 for p in positions), min(p.y1 for p in positions)])
        for _ in range(8):
            if edges[2] <= edges[0] or edges[3] <= edges[1]:
                raise ValueError('Labels leave no shared plotting area; increase figsize.')
            bounds = (edges[0], edges[1], edges[2] - edges[0], edges[3] - edges[1])
            overflow = np.zeros(4)
            for fig in selected:
                fig.set_layout_engine('none')
                fig._hedgehogs_finish_engine = None
                fig.axes[0].set_position(bounds)
                fig._hedgehogs_aligned_layout = (tuple(fig.get_size_inches()), bounds)
                fig.canvas.draw()
            _align_axis_labels(selected)
            for fig in selected:
                fig.canvas.draw()
                box = fig.axes[0].get_tightbbox(fig.canvas.get_renderer())
                if box is not None:
                    pad = fig.dpi / 24  # Three points of outer clearance.
                    overflow = np.maximum(overflow, [
                        (pad - box.x0) / fig.bbox.width, (pad - box.y0) / fig.bbox.height,
                        (box.x1 + pad - fig.bbox.width) / fig.bbox.width,
                        (box.y1 + pad - fig.bbox.height) / fig.bbox.height])
            if np.max(overflow) < 1e-6:
                for fig in selected:
                    prepare(fig)
                return
            edges += overflow * np.array([1, 1, -1, -1])
        raise ValueError('Shared layout did not converge; increase figsize or simplify labels.')
    except Exception:
        for fig, (position, marker, xpad, ypad) in zip(selected, previous):
            fig.axes[0].set_position(position)
            fig.axes[0].xaxis.labelpad = xpad
            fig.axes[0].yaxis.labelpad = ypad
            if marker is None:
                fig.__dict__.pop('_hedgehogs_aligned_layout', None)
            else:
                fig._hedgehogs_aligned_layout = marker
        raise
