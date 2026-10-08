"""Measured Matplotlib rendering of fitted single-output decision trees."""

from dataclasses import dataclass
from collections.abc import Sequence
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.layout_engine import PlaceHolderLayoutEngine
from matplotlib.font_manager import FontProperties
from matplotlib.patches import FancyBboxPatch
from matplotlib.colors import to_rgb
from matplotlib.text import Annotation, Text
from math import isclose, isfinite

from ..core.palette import get_palette
from .style import _FONT_SERIF
from . import style


@dataclass
class _Node:
    index: int
    title: str
    detail: str
    colour: Any
    width: float
    height: float
    title_height: float = 0
    children: tuple['_Node', ...] = ()
    span: float = 0
    x: float = 0
    depth: int = 0


def tree(
    decision_tree: Any,
    *,
    max_depth: int | None = None,
    feature_names: Sequence[str] | None = None,
    class_names: Sequence[str] | None = None,
    label: str = 'all',
    impurity: bool = True,
    node_ids: bool = False,
    proportion: bool = False,
    precision: int = 3,
    ax: Axes | None = None,
    fontsize: float | None = None,
) -> list[Annotation]:
    """Draw a fitted single-output sklearn tree without Graphviz.

    Follow sklearn.tree.plot_tree's presentation options, except filled and
    rounded: Hedgehogs owns node colours and corners. Use current axes when
    available; otherwise create a measured canvas. Return annotation artists.
    """
    estimator = decision_tree
    tree = getattr(estimator, 'tree_', None)
    if tree is None:
        raise ValueError('estimator must be a fitted decision tree with tree_.')
    if getattr(estimator, 'n_outputs_', 1) != 1:
        raise ValueError('Only single-output decision trees are supported.')
    if max_depth is not None and (isinstance(max_depth, bool) or not isinstance(max_depth, int) or max_depth < 0):
        raise ValueError('max_depth must be a non-negative integer or None.')
    if feature_names is not None and len(feature_names) != estimator.n_features_in_:
        raise ValueError('feature_names must match the number of input features.')
    classes = getattr(estimator, 'classes_', None)
    if class_names is not None and (classes is None or len(class_names) != len(classes)):
        raise ValueError('class_names must match the classifier classes.')
    if label not in ('all', 'root', 'none'):
        raise ValueError("label must be 'all', 'root', or 'none'.")
    if isinstance(precision, bool) or not isinstance(precision, int) or precision < 0:
        raise ValueError('precision must be a non-negative integer.')
    if fontsize is not None and (not isfinite(fontsize) or fontsize <= 0):
        raise ValueError('fontsize must be a positive finite number or None.')
    implicit_axes = ax is None
    created = ax is None and not plt.get_fignums()
    if ax is None and not created:
        ax = plt.gca()
    if created:
        _, ax = plt.subplots()
    assert ax is not None
    ax.clear()
    fig: Any = ax.figure
    renderer = fig._get_renderer()
    font = float(plt.rcParams['font.size'] if fontsize is None else fontsize)
    title_font = FontProperties(family=_FONT_SERIF, size=font, weight='bold')
    detail_ratio = FontProperties(size=plt.rcParams['xtick.labelsize']).get_size_in_points() / float(plt.rcParams['font.size'])
    detail_font = FontProperties(family=_FONT_SERIF, size=font * detail_ratio)
    palette = style._active_palette if style._active_palette is not None else get_palette()
    colour_names = ('orange', 'blue', 'green', 'purple', 'red')
    colours = ([palette[name] for name in colour_names] if all(name in palette for name in colour_names)
               else list(palette))
    gap = font * 1.5
    row_gap = font * 3

    def measure(text: str, properties: FontProperties) -> tuple[float, float]:
        if not text:
            return 0., 0.
        artist = Text(0, 0, text, fontproperties=properties, linespacing=1.2)
        artist.set_figure(fig)
        bounds = artist.get_window_extent(renderer)
        return bounds.width * 72 / fig.dpi, bounds.height * 72 / fig.dpi

    def number(value: float) -> str:
        return f'{value:.{precision}f}'.rstrip('0').rstrip('.') if precision else f'{value:.0f}'

    def field(name: str, value: str, labelled: bool) -> str:
        return f'{name} = {value}' if labelled else value

    def build(index: int, depth: int) -> _Node:
        left, right = int(tree.children_left[index]), int(tree.children_right[index])
        leaf = left < 0
        truncated = not leaf and max_depth is not None and depth >= max_depth
        colour: tuple[float, ...] = (1., 1., 1.)
        if classes is not None:
            values = tree.value[index][0]
            total = float(sum(values))
            winner = max(range(len(values)), key=lambda i: values[i])
            prediction = str(class_names[winner] if class_names is not None else classes[winner])
            fractions = [float(value) / total if total else 0 for value in values]
            # Equal class shares are almost white; pure nodes retain a pale
            # class colour. Normalise against the number of classes so a
            # balanced binary split is as neutral as a balanced multiclass split.
            baseline = 1 / len(values)
            dominance = ((fractions[winner] - baseline) / (1 - baseline)
                         if len(values) > 1 else 1.)
            strength = .04 + .42 * max(0., min(1., dominance))
            colour = tuple(1 - strength * (1 - component) for component in to_rgb(colours[winner % len(colours)]))
            weighted_samples = getattr(tree, 'weighted_n_node_samples', tree.n_node_samples)[index]
            counts = [float(value) * weighted_samples if isclose(total, 1.) else float(value)
                      for value in values]
            display_values = fractions if proportion else counts
            value_text = '[' + ', '.join(number(value) for value in display_values) + ']'
        else:
            prediction = ''
            value_text = number(float(tree.value[index][0][0]))
        title = ''
        if not leaf:
            feature = int(tree.feature[index])
            name = str(feature_names[feature]) if feature_names is not None else f'x[{feature}]'
            title = f'{name} ≤ {number(float(tree.threshold[index]))}'
        labelled = label == 'all' or (label == 'root' and depth == 0)
        lines = []
        if node_ids:
            lines.append(f'node #{index}')
        if impurity:
            lines.append(field(str(estimator.criterion), number(float(tree.impurity[index])), labelled))
        samples = (f'{100 * tree.n_node_samples[index] / tree.n_node_samples[0]:.{precision}f}%'
                   if proportion else str(int(tree.n_node_samples[index])))
        lines.append(field('samples', samples, labelled))
        lines.append(field('value', value_text, labelled))
        if classes is not None and class_names is not None:
            lines.append(field('class', prediction, labelled))
        detail = '\n'.join(lines)
        if truncated:
            detail += '\n… subtree omitted'
        title_width, title_height = measure(title, title_font)
        detail_width, detail_height = measure(detail, detail_font)
        width = max(title_width, detail_width) + font * 2
        height = title_height + detail_height + font * 1.7 + (font * .35 if title else 0)
        node = _Node(index, title, detail, colour, width, height,
                     title_height=title_height, depth=depth)
        if not leaf and not truncated:
            node.children = (build(left, depth + 1), build(right, depth + 1))
        return node

    root = build(0, 0)
    nodes: list[_Node] = []
    widths: dict[int, float] = {}

    def collect(node: _Node) -> None:
        nodes.append(node)
        widths[node.depth] = max(widths.get(node.depth, 0), node.width)
        for child in node.children:
            collect(child)

    collect(root)

    def align_widths(node: _Node) -> None:
        node.width = widths[node.depth]
        for child in node.children:
            align_widths(child)
        node.span = max(node.width, sum(child.span for child in node.children)
                        + (gap if node.children else 0))

    align_widths(root)

    def position(node: _Node, start: float) -> None:
        node.x = start + node.span / 2
        if node.children:
            children_width = sum(child.span for child in node.children) + gap
            cursor = start + (node.span - children_width) / 2
            for child in node.children:
                position(child, cursor)
                cursor += child.span + gap
            midpoint = sum(child.x for child in node.children) / 2
            node.x = max(start + node.width / 2, min(start + node.span - node.width / 2, midpoint))

    position(root, 0)
    row_height = max(node.height for node in nodes) + row_gap
    height = max(node.depth * row_height + node.height for node in nodes)
    padding = font * .6
    if created:
        fig.set_size_inches((root.span + 2 * padding) / 72, (height + 2 * padding) / 72)
        fig.subplots_adjust(left=padding / (root.span + 2 * padding),
                            right=1 - padding / (root.span + 2 * padding),
                            bottom=padding / (height + 2 * padding),
                            top=1 - padding / (height + 2 * padding))
    elif implicit_axes and len(fig.axes) == 1:
        engine = fig.get_layout_engine()
        if engine is None or (isinstance(engine, PlaceHolderLayoutEngine) and engine.adjust_compatible):
            # A standalone tree has no axis labels: ordinary plot margins
            # waste space and shift the diagram away from the canvas centre.
            fig.subplots_adjust(left=.04, right=.96, bottom=.04, top=.96)
    # Keep border strokes inside the axes clip rectangle on every side.
    border_margin = font * .5
    ax.set(xlim=(-border_margin, root.span + border_margin),
           ylim=(height + border_margin, -border_margin))
    ax.set_aspect("equal", adjustable="box")
    ax.apply_aspect()
    scale = min(ax.bbox.width * 72 / fig.dpi / (root.span + 2 * border_margin),
                ax.bbox.height * 72 / fig.dpi / (height + 2 * border_margin))
    ax.set_axis_off()

    def fixed(artist: Any) -> None:
        # The renderer already fits point sizes to the measured tree canvas.
        artist._hedgehogs_fixed_size = True

    def centre(node: _Node) -> float:
        # Align box tops at each depth, including shorter terminal nodes.
        return node.depth * row_height + node.height / 2

    annotations: list[Annotation] = []
    for node in nodes:
        y = centre(node)
        for branch, child in zip(('True', 'False'), node.children):
            child_y = centre(child)
            arrow = ax.annotate(
                '', (child.x, child_y - child.height / 2),
                xytext=(node.x, y + node.height / 2),
                arrowprops=dict(arrowstyle='-|>', color='black', linewidth=plt.rcParams['lines.linewidth'] * scale,
                                mutation_scale=font * .8 * scale, shrinkA=0, shrinkB=2 * scale),
                fontfamily=_FONT_SERIF, zorder=1,
            )
            fixed(arrow)
            fixed(arrow.arrow_patch)
            label_artist = ax.annotate(branch,
                            ((node.x + child.x) / 2, (y + node.height / 2 + child_y - child.height / 2) / 2), ha='center', va='center', fontsize=font * .85 * scale, fontfamily=_FONT_SERIF,
                            bbox=dict(facecolor='white', edgecolor='none', pad=1), zorder=2)
            fixed(label_artist)
            annotations.append(label_artist)
        patch = FancyBboxPatch((node.x - node.width / 2, y - node.height / 2),
                               node.width, node.height, boxstyle='square,pad=0',
                               facecolor=node.colour, edgecolor='black', linewidth=plt.rcParams['axes.linewidth'] * scale, zorder=3)
        ax.add_patch(patch)
        fixed(patch)
        if node.title:
            title = ax.annotate(node.title, (node.x, y - node.height / 2 + font * .85),
                                ha='center', va='top', fontsize=font * scale, fontfamily=_FONT_SERIF, weight='bold', zorder=4)
            fixed(title)
            annotations.append(title)
        detail_y = y - node.height / 2 + font * .85
        if node.title:
            detail_y += node.title_height + font * .35
        detail = ax.annotate(node.detail, (node.x, detail_y),
                             ha='center', va='top', fontsize=font * detail_ratio * scale, fontfamily=_FONT_SERIF, linespacing=1.2, zorder=4)
        fixed(detail)
        annotations.append(detail)
    return annotations
