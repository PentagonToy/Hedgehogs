"""Reference panel geometry for proportional scientific typography.

The Science canvas is 2.24 × 2.20 inches; its default subplot occupies
72% of the width and 66% of the height. Use the shorter physical panel side
rather than panel count or the complete canvas including legends.
"""

REFERENCE_CANVAS_INCHES = (2.24, 2.20)
REFERENCE_LABEL_POINTS = 10.5
REFERENCE_TICK_POINTS = 9.5
REFERENCE_LEGEND_POINTS = 9.5
REFERENCE_AXES_WIDTH = .9
REFERENCE_LINE_WIDTH = 1.1
REFERENCE_MARKER_AREA = 16.
REFERENCE_MARKER_EDGE_WIDTH = .5
FINISH_MAX_PANEL_SCALE = 1.35
FINISH_MAX_SPARSE_SCALE = 2.2
FINISH_MAX_ANNOTATION_SCALE = 1.1
REFERENCE_PANEL_INCHES = min(REFERENCE_CANVAS_INCHES[0] * .72,
                             REFERENCE_CANVAS_INCHES[1] * .66)


def panel_scale(axes) -> float:
    """Return the panel's physical short-side ratio to the reference panel."""
    return min(axes.bbox.width, axes.bbox.height) / axes.figure.dpi / REFERENCE_PANEL_INCHES



def outline_scale(width: float, height: float, reference: tuple[float, float]) -> float:
    """Keep physical outline weight stable across panel aspect ratios."""
    from math import log2, sqrt
    reference_area = reference[0] * .72 * reference[1] * .66
    relative_length = sqrt(max(width * height / reference_area, 1e-12))
    return min(2.2, max(1.6, 1.6 + .4 * log2(relative_length)))

def refine_presentation(figure, state, annotations) -> None:
    """Refine default roles on ordinary axes without replacing author settings."""
    from math import sqrt
    import matplotlib.pyplot as plt
    from matplotlib.ticker import AutoLocator, MaxNLocator, FixedLocator
    from matplotlib.category import StrCategoryLocator
    from matplotlib.font_manager import FontProperties
    from matplotlib.lines import Line2D

    axes = [ax for ax in figure.axes
            if getattr(ax, 'get_subplotspec', lambda: None)() is not None
            and not hasattr(ax, '_colorbar')
            and not getattr(ax, '_hedgehogs_fixed_scale', False)
            and not any(getattr(item, '_hedgehogs_fixed_size', False) for item in ax.findobj())]
    reference = min(state.reference_size[0] * .72, state.reference_size[1] * .66)
    stamp = (tuple(figure.get_size_inches()), state.reference_size, len(axes))

    def points(value):
        return FontProperties(size=value).get_size_in_points()

    def managed(owner, key, current, expected, target):
        properties = state.values.setdefault(owner, {})
        previous = properties.get('finish_role.' + key)
        if previous is None:
            if abs(current - expected) > 1e-6:
                properties['finish_role.' + key] = None
                return False
        elif abs(current - previous) > 1e-6:
            properties['finish_role.' + key] = None
            return False
        properties['finish_role.' + key] = target
        return True

    def font(text, expected, target):
        if getattr(text, '_hedgehogs_font_explicit', False):
            return
        properties = state.values.setdefault(text, {})
        if 'finish_role.fontsize' in properties and properties['finish_role.fontsize'] is None:
            return
        current = text.get_fontsize()
        # A fitted default title retains its configured base in the renderer cache.
        if 'finish_role.fontsize' not in properties and 'fontsize' in properties:
            base = properties['fontsize'][0][0]
            if abs(base - expected) < 1e-6:
                current = base
        if managed(text, 'fontsize', current, expected, target):
            text.set_fontsize(target)
            properties['fontsize'] = ((target,), (target,), 1.)

    colourbars = [ax for ax in figure.axes if hasattr(ax, '_colorbar')]
    def stroke(owner, name, expected, factor, limit=None):
        explicit = '_hedgehogs_line_explicit' if name == 'linewidth' and isinstance(owner, Line2D) else '_hedgehogs_stroke_explicit'
        if getattr(owner, explicit, False):
            return
        properties = state.values.setdefault(owner, {})
        key = 'finish_role.' + name
        if key in properties and properties[key] is None:
            return
        value = getattr(owner, 'get_' + name)()
        current = state._values(value)
        previous = properties.get(key, expected)
        if not current or any(abs(item - previous) > 1e-6 for item in current):
            properties[key] = None
            return
        target = expected * factor
        if limit is not None:
            target = min(target, limit)
        if managed(owner, name, current[0], expected, target):
            scaled = tuple(target for _ in current)
            getattr(owner, 'set_' + name)(scaled if name == 'linewidths' else target)
            properties[name] = (scaled, scaled, 1.)

    for ax in [*axes, *colourbars]:
        properties = state.values.setdefault(ax, {})
        value_labels = annotations(ax)
        legend = ax.get_legend()
        dense = (len(value_labels) >= 6
                 or (legend is not None and len(legend.get_texts()) > 4)
                 or any(isinstance(axis.get_major_locator(), (FixedLocator, StrCategoryLocator))
                        and len(axis.get_major_ticks()) > 4 for axis in (ax.xaxis, ax.yaxis)))
        panel_stamp = (stamp, dense)
        previous_scale = properties.get('finish_panel_scale')
        if hasattr(ax, '_colorbar'):
            parent = getattr(ax._colorbar.mappable, 'axes', None)
            factor = state.values[parent]['finish_panel_scale'][1] if parent in axes else 1.
        elif previous_scale is not None and previous_scale[0] == panel_stamp:
            factor = previous_scale[1]
        else:
            short_side = min(ax.bbox.width, ax.bbox.height) / figure.dpi
            larger = min(figure.get_size_inches()[i] / state.reference_size[i] for i in (0, 1)) > 1.
            ratio = short_side / reference
            preferred = min(FINISH_MAX_PANEL_SCALE, max(1., sqrt(ratio))) if dense else min(FINISH_MAX_SPARSE_SCALE, max(1., ratio))
            factor = preferred if len(axes) == 1 and larger else 1.
            properties['finish_panel_scale'] = (panel_stamp, factor)
        previous_outline = properties.get('finish_outline_scale')
        if hasattr(ax, '_colorbar'):
            outline = state.values[parent]['finish_outline_scale'][1] if parent in axes else 1.6
        elif previous_outline is not None and previous_outline[0] == stamp:
            outline = previous_outline[1]
        else:
            outline = outline_scale(ax.bbox.width / figure.dpi, ax.bbox.height / figure.dpi,
                                    state.reference_size)
        properties['finish_outline_scale'] = (stamp, outline)
        for axis, name in ((ax.xaxis, 'x'), (ax.yaxis, 'y')):
            font(axis.label, points(plt.rcParams['axes.labelsize']),
                 points(plt.rcParams['axes.labelsize']) * factor)
            expected = points(plt.rcParams['xtick.labelsize'] if name == 'x' else plt.rcParams['ytick.labelsize'])
            target = expected * factor
            tick_properties = state.values.setdefault(axis, {})
            role = 'finish_role.labelsize'
            previous = tick_properties.get(role, expected)
            labels = [label for tick in axis.get_major_ticks() for label in (tick.label1, tick.label2)]
            if (labels and not getattr(axis, '_hedgehogs_font_explicit', False)
                    and not any(getattr(label, '_hedgehogs_font_explicit', False) for label in labels)
                    and previous is not None
                    and all(abs(label.get_fontsize() - previous) < 1e-6 for label in labels)):
                if managed(axis, 'labelsize', labels[0].get_fontsize(), expected, target):
                    axis.set_tick_params(which='major', labelsize=target)
                    tick_properties['major.labelsize'] = ((target,), (target,), 1.)
            else:
                tick_properties[role] = None
            locator = axis.get_major_locator()
            owned = tick_properties.get('finish_locator')
            automatic = (type(locator) is AutoLocator and getattr(locator, '_nbins', 'auto') == 'auto')
            unchanged = (owned is not None and locator is owned[0]
                         and getattr(locator, '_nbins', None) == owned[1])
            if owned is not None and locator is owned[0] and not unchanged:
                tick_properties['finish_locator'] = None
            if not hasattr(ax, '_colorbar') and axis.get_scale() == 'linear' and (automatic or unchanged):
                length = (ax.bbox.width if name == 'x' else ax.bbox.height) / figure.dpi * 72
                size = axis.get_major_ticks()[0].label1.get_fontsize()
                budget = min(6, max(3, round(length / (size * (4.5 if name == 'x' else 2.5)))))
                if not unchanged or budget != owned[1]:
                    locator = MaxNLocator(nbins=budget, steps=[1, 2, 2.5, 5, 10])
                    axis.set_major_locator(locator)
                    tick_properties['finish_locator'] = (locator, budget)
        for title in (ax.title, ax._left_title, ax._right_title):
            font(title, points(plt.rcParams['axes.titlesize']),
                 points(plt.rcParams['axes.titlesize']) * factor)
        value_factor = min(factor, FINISH_MAX_ANNOTATION_SCALE) if dense else max(1., factor * .9)
        for text in value_labels:
            font(text, points(plt.rcParams['font.size']),
                 points(plt.rcParams['xtick.labelsize']) * value_factor)
        for spine in ax.spines.values():
            properties = state.values.setdefault(spine, {})
            key = 'finish_role.linewidth'
            if key in properties and properties[key] is None:
                continue
            width = float(plt.rcParams['axes.linewidth']) * outline
            if managed(spine, 'linewidth', spine.get_linewidth(), float(plt.rcParams['axes.linewidth']), width):
                spine.set_linewidth(width)
                properties['linewidth'] = ((width,), (width,), 1.)
        for patch in ax.patches:
            stroke(patch, 'linewidth', float(plt.rcParams['patch.linewidth']), outline)
        for collection in ax.collections:
            sizes = collection.get_sizes() if hasattr(collection, 'get_sizes') else []
            positive = [float(size) for size in sizes if size > 0]
            limit = min(positive) ** .5 * .25 if positive else None
            stroke(collection, 'linewidths', float(plt.rcParams['patch.linewidth']), outline, limit)
        for line in ax.lines:
            stroke(line, 'linewidth', float(plt.rcParams['lines.linewidth']), outline)
            if line.get_marker() not in (None, 'None', 'none', '', ' '):
                stroke(line, 'markeredgewidth', float(plt.rcParams['lines.markeredgewidth']), outline, line.get_markersize() * .25)
        legend = ax.get_legend()
        if legend is not None:
            source_handles, source_labels = ax.get_legend_handles_labels()
            sources = dict(zip(source_labels, source_handles))
            handles = getattr(legend, 'legend_handles', None)
            if handles is None:
                handles = legend.legendHandles
            for handle, text in zip(handles, legend.get_texts()):
                source = sources.get(text.get_text())
                if isinstance(source, Line2D) and isinstance(handle, Line2D):
                    if state.values.get(source, {}).get('finish_role.linewidth') is not None:
                        stroke(handle, 'linewidth', float(plt.rcParams['lines.linewidth']), outline)
            stroke(legend.get_frame(), 'linewidth', float(plt.rcParams['patch.linewidth']), outline)
            expected = points(plt.rcParams['legend.fontsize'])
            for text in legend.get_texts():
                font(text, expected, expected * factor)
            title_size = plt.rcParams['legend.title_fontsize']
            title_size = expected if title_size is None else points(title_size)
            font(legend.get_title(), title_size, title_size * factor)
            properties = state.values.setdefault(legend, {})
            key = 'finish_role.legend_fontsize'
            if (not getattr(legend, '_hedgehogs_font_explicit', False)
                    and not (key in properties and properties[key] is None)):
                if managed(legend, 'legend_fontsize', legend._fontsize, expected, expected * factor):
                    legend._fontsize = expected * factor
                    properties['legend_fontsize'] = ((expected * factor,), (expected * factor,), 1.)
