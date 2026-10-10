"""Experimental continuous legend placement; never enabled by default.

An occupancy grid proposes one location using every visible scatter point and
cell-spaced line segments. Summed-area tables evaluate rectangular free space
without rebuilding figures. This is an approximation, not a global optimum.
"""
from contextlib import contextmanager

import numpy as np
from matplotlib.collections import PathCollection

from hedgehogs.plots import presentation

FIXED = presentation._place_legend


def windows(grid, height, width):
    integral = np.pad(grid, ((1, 0), (1, 0))).cumsum(0).cumsum(1)
    return (integral[height:, width:] - integral[:-height, width:]
            - integral[height:, :-width] + integral[:-height, :-width])


def bin_points(points, bounds, resolution):
    points = np.ma.filled(points, np.nan)
    coordinates = (points - [bounds.xmin, bounds.ymin]) / [bounds.width, bounds.height]
    valid = np.isfinite(coordinates).all(axis=1) & (coordinates >= 0).all(axis=1) & (coordinates <= 1).all(axis=1)
    indices = np.minimum((coordinates[valid] * resolution).astype(np.intp), resolution - 1)
    return np.bincount(indices[:, 1] * resolution + indices[:, 0], minlength=resolution**2).reshape(resolution, resolution)


def clearance(mask):
    distance = mask.astype(np.int64)
    interior = mask.copy()
    while interior.any():
        padded = np.pad(interior, 1)
        interior = np.logical_and.reduce([padded[dy:dy + mask.shape[0], dx:dx + mask.shape[1]]
                                         for dy in range(3) for dx in range(3)])
        distance += interior
    return distance


def propose(fig, ax, renderer, resolution=128, *, offsets=None, texts=None):
    legend = ax.get_legend()
    if legend is None or not legend.get_visible() or legend._loc != 0 or legend._bbox_to_anchor is not None:
        return None
    if ax.name != 'rectilinear' or ax.patches or ax.images or any(not isinstance(item, PathCollection) for item in ax.collections):
        return None
    presentation._legend_location(legend, 1)
    box = legend.get_window_extent(renderer)
    pad = renderer.points_to_pixels(legend.borderaxespad * legend._fontsize)
    bounds = ax.bbox.padded(-pad)
    if min(bounds.width, bounds.height) <= 0:
        presentation._legend_location(legend, 0)
        return None
    width = int(np.ceil(box.width / bounds.width * resolution))
    height = int(np.ceil(box.height / bounds.height * resolution))
    if width >= resolution or height >= resolution:
        presentation._legend_location(legend, 0)
        return None
    edges = [np.linspace(bounds.ymin, bounds.ymax, resolution + 1),
             np.linspace(bounds.xmin, bounds.xmax, resolution + 1)]
    grid = np.zeros((resolution, resolution), dtype=np.int64)
    for collection in ax.collections:
        if not collection.get_visible():
            continue
        points = (offsets[collection] if offsets is not None else
                  collection.get_offset_transform().transform(collection.get_offsets()))
        points = np.ma.filled(points, np.nan)
        grid += bin_points(points, bounds, resolution)
    cost = windows(grid, height, width)
    for line in ax.lines:
        if not line.get_visible():
            continue
        vertices = line.get_path().transformed(line.get_transform()).vertices
        if len(vertices) > 4096:
            presentation._legend_location(legend, 0)
            return None
        segments = []
        for first, last in zip(vertices[:-1], vertices[1:]):
            if not np.isfinite([first, last]).all():
                continue
            scale = np.array([bounds.width, bounds.height])
            steps = int(np.ceil(np.max(np.abs((last - first) / scale)) * resolution)) + 1
            # Bound work for extreme off-axis segments; fall back rather than truncate.
            if steps > resolution * 4:
                presentation._legend_location(legend, 0)
                return None
            points = np.linspace(first, last, max(steps, 2))
            segments.append(points)
        occupied = bin_points(np.concatenate(segments) if segments else vertices, bounds, resolution)
        cost += 10 * (windows(occupied, height, width) > 0)
    text = np.zeros_like(grid)
    excluded = set(legend.findobj())
    visible_texts = presentation._visible_texts(fig, renderer, excluded) if texts is None else texts
    for box_text in visible_texts:
        x0, x1 = np.searchsorted(edges[1], [box_text.xmin, box_text.xmax])
        y0, y1 = np.searchsorted(edges[0], [box_text.ymin, box_text.ymax])
        text[max(0, y0 - 1):min(resolution, y1), max(0, x0 - 1):min(resolution, x1)] = 1
    text_cost = windows(text, height, width)
    y, x = np.indices(cost.shape)
    x_gap = np.minimum(x, cost.shape[1] - 1 - x)
    y_gap = np.minimum(y, cost.shape[0] - 1 - y)
    alignment = x_gap + y_gap
    # Deterministic ties favour aligned corners, then the upper-right side.
    eligible = (text_cost == text_cost.min())
    eligible &= cost == cost[eligible].min()
    edge_free = eligible[0].any() or eligible[-1].any() or eligible[:, 0].any() or eligible[:, -1].any()
    space = np.zeros_like(cost) if edge_free else clearance(eligible)
    order = np.lexsort((-x.ravel(), -y.ravel(), alignment.ravel(), -space.ravel(), cost.ravel(), text_cost.ravel()))
    row, column = np.unravel_index(order[0], cost.shape)
    left, bottom = edges[1][column], edges[0][row]
    if column == cost.shape[1] - 1:
        left = bounds.xmax - box.width
    if row == cost.shape[0] - 1:
        bottom = bounds.ymax - box.height
    return ((left - ax.bbox.xmin) / ax.bbox.width, (bottom - ax.bbox.ymin) / ax.bbox.height)


def place(fig, ax, renderer):
    legend = ax.get_legend()
    location = propose(fig, ax, renderer)
    if location is None:
        if legend is not None and legend._loc == 0:
            FIXED(fig, ax, renderer)
        return
    presentation._legend_location(legend, location)
    legend._hedgehogs_finish_last_loc = location
    legend._hedgehogs_finish_requested_loc = 0
    legend._hedgehogs_finish_anchor = None


def hybrid(fig, ax, renderer, min_relative_gain=.1):
    """Keep the classic result unless an exact audit prefers the grid proposal."""
    legend = ax.get_legend()
    if legend is None or not legend.get_visible() or legend._loc != 0 or legend._bbox_to_anchor is not None:
        return
    texts = presentation._visible_texts(fig, renderer, set(legend.findobj()))
    offsets = {item: item.get_offset_transform().transform(item.get_offsets())
               for item in ax.collections if item.get_visible() and hasattr(item, 'get_offsets')}

    def audit():
        box = legend.get_window_extent(renderer)
        area = max(presentation._area(box), 1.)
        return (max(0., area - presentation._overlap(box, ax.bbox)) / area,
                sum(presentation._overlap(box, text) for text in texts) / area,
                presentation._data_overlap(ax, box, renderer, offsets) / area)

    def apply(location):
        presentation._legend_location(legend, location)
        legend._hedgehogs_finish_last_loc = location
        legend._hedgehogs_finish_requested_loc = 0
        legend._hedgehogs_finish_anchor = None

    best_location, best_score = 1, None
    for location in range(1, 11):
        presentation._legend_location(legend, location)
        candidate = audit()
        if best_score is None or candidate < best_score:
            best_location, best_score = location, candidate
        if candidate == (0., 0., 0.):
            apply(location)
            return
    if best_score[0] > 1e-6:
        presentation._legend_location(legend, 0)
        FIXED(fig, ax, renderer)
        return
    presentation._legend_location(legend, 0)
    proposal = propose(fig, ax, renderer, offsets=offsets, texts=texts)
    if proposal is not None:
        presentation._legend_location(legend, proposal)
        candidate = audit()
        # Ignore floating-point noise and keep the classic placement on ties.
        for component, (proposed, existing) in enumerate(zip(candidate, best_score)):
            if np.isclose(proposed, existing, rtol=1e-10, atol=1e-12):
                continue
            if proposed < existing:
                gain = (existing - proposed) / existing if existing > 0 else 0.
                if component != 2 or gain >= min_relative_gain or np.isclose(gain, min_relative_gain, rtol=1e-10, atol=1e-12):
                    best_location = proposal
            break
    apply(best_location)


@contextmanager
def experimental_placement(policy=hybrid):
    original = presentation._place_legend
    presentation._place_legend = policy
    try:
        yield
    finally:
        presentation._place_legend = original
