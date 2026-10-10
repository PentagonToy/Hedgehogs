"""Keep point-based presentation proportional to each figure's reference size."""

from functools import wraps
from contextlib import contextmanager
from math import isfinite
from numbers import Real
from typing import Any, Callable, cast
from weakref import WeakKeyDictionary

import matplotlib.pyplot as plt

from ..core.environment import _is_jupyter

from matplotlib.axes import Axes
from matplotlib.collections import Collection
from matplotlib.container import Container
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties
from matplotlib.legend import Legend
from matplotlib.layout_engine import TightLayoutEngine, PlaceHolderLayoutEngine
from matplotlib.lines import Line2D
from matplotlib.markers import MarkerStyle
from matplotlib.offsetbox import DrawingArea, PackerBase
from matplotlib.patches import Patch, Rectangle
from matplotlib.text import Text


@contextmanager
def _cached_legend_search(figure):
    """Reuse identical native placement measurements within one draw only."""
    installed = []
    active = True
    try:
        for ax in figure.axes:
            legend = ax.get_legend()
            if (legend is None or legend._loc != 0 or legend._bbox_to_anchor is not None
                    or '_find_best_position' in legend.__dict__):
                continue
            original = legend._find_best_position
            cache: dict[tuple[Any, ...], Any] = {}

            def find(width, height, renderer, *args, _original=original, _ax=ax, _cache=cache, **kwargs):
                if not active or args or kwargs:
                    return _original(width, height, renderer, *args, **kwargs)
                key = (width, height, id(renderer), tuple(_ax.bbox.bounds),
                       tuple(_ax.get_xlim()), tuple(_ax.get_ylim()),
                       tuple(_ax.transData.get_matrix().flat))
                if key not in _cache:
                    _cache[key] = _original(width, height, renderer)
                return _cache[key]

            legend._find_best_position = find
            installed.append((legend, find, cache))
        yield
    finally:
        active = False
        for legend, find, cache in installed:
            cache.clear()
            if legend.__dict__.get('_find_best_position') is find:
                del legend._find_best_position


class _FigureStyle:
    def __init__(self, reference_size: tuple[float, float], manage_margins: bool = True) -> None:
        self.reference_size = reference_size
        self.manage_margins = manage_margins
        self.values: WeakKeyDictionary[Any, dict[str, Any]] = WeakKeyDictionary()

    def __getstate__(self) -> dict[str, Any]:
        # Matplotlib figures support pickling; weak references themselves do not.
        return {"reference_size": self.reference_size, "manage_margins": self.manage_margins,
                "values": dict(self.values)}

    def __setstate__(self, state: dict[str, Any]) -> None:
        self.reference_size = state["reference_size"]
        self.manage_margins = state["manage_margins"]
        self.values = WeakKeyDictionary(state["values"])

    @staticmethod
    def _values(value: Any) -> tuple[float, ...]:
        return (float(value),) if isinstance(value, Real) else tuple(float(item) for item in value)

    def _scaled(self, owner: Any, name: str, value: Any, factor: float) -> Any:
        """Retain a base value; incorporate edits made since the previous draw."""
        properties = self.values.setdefault(owner, {})
        previous = properties.get(name)
        current = self._values(value)
        if previous is None:
            base = current
        else:
            base, last, last_factor = previous
            if current != last:
                base = tuple(item / last_factor for item in current)
        scaled = tuple(item * factor for item in base)
        properties[name] = (base, scaled, factor)
        return scaled[0] if isinstance(value, Real) else list(scaled)

    def _property(self, owner: Any, name: str, getter: Callable, setter: Callable, factor: float) -> None:
        current = getter()
        value = self._scaled(owner, name, current, factor)
        if self._values(current) != self._values(value):
            setter(value)

    def _legend_handles(self, figure: Any) -> None:
        # Legends can copy already-scaled line or scatter styles after a draw.
        # Seed those copied properties from their source rather than scaling twice.
        for legend in figure.findobj(match=Legend):
            properties = self.values.setdefault(legend, {})
            if 'handles_seeded' in properties:
                continue
            properties['handles_seeded'] = True
            sources: dict[str, Any] = {}
            for axes in figure.axes:
                handles, labels = axes.get_legend_handles_labels()
                sources.update(zip(labels, handles))
            handles = getattr(legend, 'legend_handles', None)
            if handles is None:
                handles = legend.legendHandles
            for handle, text in zip(handles, legend.get_texts()):
                source = sources.get(text.get_text())
                # Containers are tuple-like and cannot be weak-referenced.
                # Seed copied legend styles from the matching child artist.
                if isinstance(source, Container):
                    kind = (Line2D if isinstance(handle, Line2D) else
                            Collection if isinstance(handle, Collection) else Patch)
                    source = next((child for child in source.get_children()
                                   if isinstance(child, kind)), None)
                previous = (self.values.get(source, {})
                            if isinstance(source, (Line2D, Collection, Patch)) else {})
                names: tuple[str, ...]
                if isinstance(handle, Line2D):
                    names = ("linewidth", "markersize", "markeredgewidth")
                elif isinstance(handle, Collection):
                    names = ("linewidths", "sizes")
                elif isinstance(handle, Patch):
                    names = ("linewidth",)
                else:
                    names = ()
                for name in names:
                    if name in previous:
                        current = self._values(getattr(handle, 'get_' + name)())
                        _, _, old_factor = previous[name]
                        self.values.setdefault(handle, {})[name] = (
                            tuple(item / old_factor for item in current), current, old_factor,
                        )

    def _panel_factors(self, figure: Any, width: float, height: float) -> dict:
        axes = figure.findobj(match=Axes)
        factors = {}
        for axis in axes:
            spec = getattr(axis, "get_subplotspec", lambda: None)()
            multiple_panels = False
            if spec is not None:
                spec = spec.get_topmost_subplotspec()
                grid = spec.get_gridspec()
                rows, columns = grid.get_geometry()
                multiple_panels = rows * columns > 1
            # Panel count must not reduce publication point sizes. Single-panel
            # figures retain proportional sizing when the canvas is resized.
            factors[axis] = (1.0 if multiple_panels else
                             min(width / self.reference_size[0],
                                 height / self.reference_size[1]))
        for axis in axes:
            if getattr(figure, "_hedgehogs_finished", False) or getattr(axis, "_hedgehogs_fixed_scale", False):
                factors[axis] = 1.0
            if hasattr(axis, "_colorbar"):
                source = getattr(axis._colorbar.mappable, "axes", None)
                factors[axis] = factors.get(source, min(factors.values(), default=1.0))
            for child in axis.child_axes:
                factors[child] = factors[axis]
            axis.apply_aspect()
        return factors

    def apply(self, figure: Any, renderer=None) -> None:
        # Tight export temporarily crops bbox_inches. transFigure retains the
        # original canvas scale, so cropping must not trigger another resize.
        transform = figure.transFigure.get_matrix()
        width, height = transform[0, 0] / figure.dpi, transform[1, 1] / figure.dpi
        figure_factor = min(width / self.reference_size[0], height / self.reference_size[1])
        if not isfinite(figure_factor) or figure_factor <= 0:
            return
        factors = self._panel_factors(figure, width, height)
        fallback = min(factors.values(), default=1. if getattr(figure, "_hedgehogs_finished", False) else figure_factor)
        artist_factors = {}
        for axis, factor in factors.items():
            for artist in axis.findobj():
                artist_factors[artist] = factor
        for legend in figure.legends:
            for artist in legend.findobj():
                artist_factors[artist] = fallback

        self._legend_handles(figure)
        tick_artists = set()
        for axes, factor in factors.items():
            for axis in (axes.xaxis, axes.yaxis):
                self._property(axis, 'labelpad', lambda: axis.labelpad,
                               lambda value: setattr(axis, 'labelpad', value), factor)
                for which, ticks, options in (
                    ('major', axis.majorTicks, axis._major_tick_kw),
                    ('minor', axis.minorTicks, axis._minor_tick_kw),
                ):
                    if not ticks:
                        continue
                    tick = ticks[0]
                    defaults = {
                        'size': tick._size,
                        'width': tick._width,
                        'pad': tick._base_pad,
                        'labelsize': tick.label1.get_fontsize(),
                        'grid_linewidth': tick.gridline.get_linewidth(),
                    }
                    if isinstance(options.get("labelsize"), str):
                        options["labelsize"] = FontProperties(size=options["labelsize"]).get_size_in_points()
                    scaled = {
                        name: self._scaled(axis, f'{which}.{name}',
                                           options.get(name, value), factor)
                        for name, value in defaults.items()
                    }
                    # Cache these values on the Axis too: ticks created during drawing
                    # must inherit the same sizes as existing ticks.
                    axis.set_tick_params(which=which, **scaled)
                    for item in ticks:
                        tick_artists.update(item.findobj())

            pad = axes.titleOffsetTrans.get_matrix()[1, 2] * 72 / figure.dpi
            axes._set_title_offset_trans(self._scaled(axes, 'titlepad', pad, factor))

        for artist in figure.findobj():
            if artist not in tick_artists:
                self._artist(artist, artist_factors.get(artist, fallback))
        if renderer is not None:
            fitted_titles = self._fit_titles(figure, renderer)
            self._fit_layout(figure, renderer)
            engine = figure.get_layout_engine()
            if (fitted_titles and engine is not None
                    and not isinstance(engine, PlaceHolderLayoutEngine)
                    and figure.transFigure._boxout is figure.bbox):
                # Native engines run inside Figure.draw, after our style pass.
                # Settle their panel widths before fitting titles for this draw.
                for _ in range(3):
                    engine.execute(figure)
                    self._fit_titles(figure, renderer)
            else:
                self._fit_titles(figure, renderer)
            self._fit_legends(figure, renderer, factors, fallback)
            self._align_legends(figure, renderer)

    def _fit_titles(self, figure: Any, renderer) -> bool:
        """Fit axes titles without changing their text or the physical canvas."""
        if figure.transFigure._boxout is not figure.bbox:
            return False
        fitted = False
        margin = renderer.points_to_pixels(3)
        for axes in figure.findobj(match=Axes):
            if not axes.get_visible():
                continue
            spec = getattr(axes, "get_subplotspec", lambda: None)()
            grid = False
            if spec is not None:
                rows, columns = spec.get_topmost_subplotspec().get_gridspec().get_geometry()
                grid = rows * columns > 1
            left = axes.bbox.x0 + margin if grid else figure.bbox.x0 + margin
            right = axes.bbox.x1 - margin if grid else figure.bbox.x1 - margin
            for title in (axes.title, axes._left_title, axes._right_title):
                if not title.get_visible() or not title.get_text():
                    continue
                properties = self.values[title]
                base, _, factor = properties["fontsize"]
                role = 'finish_role.fontsize'
                if getattr(figure, '_hedgehogs_finished', False):
                    explicit = (getattr(title, '_hedgehogs_font_explicit', False)
                                or (role in properties and properties[role] is None))
                    automatic = role in properties and properties[role] is not None
                    if explicit or (not automatic and base[0] != FontProperties(size=plt.rcParams['axes.titlesize']).get_size_in_points()):
                        continue
                configured_size = base[0] * factor
                title.set_fontsize(configured_size)
                properties["fontsize"] = (base, (configured_size,), factor)
                bounds = title.get_window_extent(renderer)
                anchor = title.get_transform().transform(title.get_position())[0]
                alignment = title.get_horizontalalignment()
                if alignment == "left":
                    available = right - anchor
                elif alignment == "right":
                    available = anchor - left
                else:
                    available = 2 * min(anchor - left, right - anchor)
                if 0 < available < bounds.width:
                    fitted = True
                    # Preserve the configured size in the existing scaling cache;
                    # each draw restores it before fitting the current canvas.
                    size = title.get_fontsize() * available / bounds.width
                    title.set_fontsize(size)
                    # Raster hinting changes glyph metrics non-linearly with
                    # point size. Re-measure instead of trusting one ratio.
                    for _ in range(3):
                        measured = title.get_window_extent(renderer).width
                        if measured <= available:
                            break
                        size *= available / measured * .99
                        title.set_fontsize(size)
                    properties = self.values[title]
                    base, _, factor = properties["fontsize"]
                    properties["fontsize"] = (base, (size,), factor)
                    if properties.get('finish_role.fontsize') is not None:
                        properties['finish_role.fontsize'] = size
        return fitted

    def _fit_layout(self, figure: Any, renderer) -> None:
        if getattr(figure, "_hedgehogs_finish_layout_locked", False):
            return
        # Measure labels at their final point sizes. Tight export temporarily
        # replaces the canvas bbox and must never change the layout again.
        if figure.transFigure._boxout is not figure.bbox:
            return
        engine = figure.get_layout_engine()
        if engine is not None:
            if not isinstance(engine, PlaceHolderLayoutEngine) or not engine.adjust_compatible:
                return
        properties = self.values.setdefault(figure, {})
        keys = ("left", "right", "bottom", "top", "wspace", "hspace")
        current = {key: getattr(figure.subplotpars, key) for key in keys}
        if "layout_last" in properties:
            if current != properties["layout_last"]:
                properties["layout_base"] = current
            figure.subplots_adjust(**properties["layout_base"])
        boxes = [axis.get_tightbbox(renderer) for axis in figure.axes if axis.get_visible()]
        boxes = [box for box in boxes if box is not None]
        margin = renderer.points_to_pixels(3)
        clipped = any(box.x0 < figure.bbox.x0 + margin or
                      box.y0 < figure.bbox.y0 + margin or
                      box.x1 > figure.bbox.x1 - margin or
                      box.y1 > figure.bbox.y1 - margin for box in boxes)
        colourbar = any(hasattr(axis, "_colorbar") for axis in figure.axes)
        main_axes = [axis for axis in figure.axes if not hasattr(axis, "_colorbar")]
        grid = len(main_axes) > 1
        automatic = self.manage_margins and engine is None and (colourbar or grid)
        if clipped or "layout_base" in properties or automatic:
            # Use Matplotlib's label-aware layout instead of shrinking the axes
            # and typography repeatedly by an estimated colourbar allowance.
            properties.setdefault("layout_base", current)
            bottom, top = 0.0, 1.0
            for legend in figure.legends:
                if not legend.get_visible() or not legend.get_in_layout():
                    continue
                bounds = legend.get_window_extent(renderer)
                if bounds.y1 <= figure.bbox.height * 0.25:
                    bottom = max(bottom, (bounds.y1 + margin) / figure.bbox.height)
                elif bounds.y0 >= figure.bbox.height * 0.75:
                    top = min(top, (bounds.y0 - margin) / figure.bbox.height)
            layout = TightLayoutEngine(pad=0.6, rect=(0, bottom, 1, top))
            # Box-aspect and colourbar locators can leave label positions stale
            # after the first layout pass. Re-measure before the final render.
            for _ in range(3):
                layout.execute(figure)
                for axis in figure.axes:
                    axis.get_tightbbox(renderer)
            # Compact grids with fixed-width labels can retain a small edge
            # overflow. Move the panel centres inward without asking the
            # tight solver to re-expand the same labels on the next pass.
            if grid:
                for _ in range(3):
                    bounds = [axis.get_tightbbox(renderer) for axis in figure.axes if axis.get_visible()]
                    bounds = [box for box in bounds if box is not None]
                    if not bounds:
                        break
                    overflow_left = max(0., margin - min(box.x0 for box in bounds))
                    overflow_right = max(0., max(box.x1 for box in bounds) + margin - figure.bbox.width)
                    overlap = 0.
                    panel_widths = []
                    for first in main_axes:
                        if not first.get_visible():
                            continue
                        first_spec = getattr(first, 'get_subplotspec', lambda: None)()
                        if first_spec is None:
                            continue
                        panel_widths.append(first.bbox.width)
                        for second in main_axes:
                            if not second.get_visible():
                                continue
                            second_spec = getattr(second, 'get_subplotspec', lambda: None)()
                            if (second_spec is None or first_spec.get_gridspec() is not second_spec.get_gridspec()
                                    or first_spec.rowspan != second_spec.rowspan
                                    or first_spec.colspan.stop != second_spec.colspan.start):
                                continue
                            overlap = max(overlap, first.get_tightbbox(renderer).x1
                                          + margin - second.get_tightbbox(renderer).x0)
                    if not overflow_left and not overflow_right and overlap <= 0:
                        break
                    left = figure.subplotpars.left + 2 * overflow_left / figure.bbox.width
                    right = figure.subplotpars.right - 2 * overflow_right / figure.bbox.width
                    if left >= right:
                        break
                    spacing = figure.subplotpars.wspace
                    if overlap > 0 and panel_widths:
                        spacing += 2 * overlap / (sum(panel_widths) / len(panel_widths))
                    figure.subplots_adjust(left=left, right=right, wspace=spacing)
            properties["layout_last"] = {key: getattr(figure.subplotpars, key) for key in keys}

    def _fit_legends(self, figure: Any, renderer, factors: dict, fallback: float) -> None:
        if getattr(figure, "_hedgehogs_finished", False):
            return
        for legend in figure.findobj(match=Legend):
            if legend.axes is not None and legend._bbox_to_anchor is not None:
                continue  # Explicit external anchors retain the author's layout.
            container = legend.axes.bbox if legend.axes is not None else figure.bbox
            bounds = legend._legend_box.get_window_extent(renderer)
            if bounds.width <= 0 or bounds.height <= 0:
                continue
            factor = factors.get(legend.axes, fallback)
            width_fraction = 0.6 if legend.axes is not None else 0.9
            fit = min(1.0, container.width * width_fraction / bounds.width,
                      container.height * 0.4 / bounds.height)
            # Compact ordinary legends without making text smaller than 6 pt
            # at reference size. Exceptionally long labels remain explicit choices.
            fit = min(1.0, max(fit, 6.0 * factor / legend._fontsize))
            if fit < 1.0:
                for artist in legend.findobj():
                    self._artist(artist, factor * fit)

    def _align_legends(self, figure: Any, renderer) -> None:
        for legend in figure.findobj(match=Legend):
            areas = {child: area for area in legend.findobj(match=DrawingArea)
                     for child in area.get_children()}
            handles = getattr(legend, "legend_handles", None)
            if handles is None:
                handles = legend.legendHandles
            for handle, text in zip(handles, legend.get_texts()):
                if handle not in areas or "\n" in text.get_text():
                    continue
                label, ismath = text._preprocess_math(text.get_text())
                _, height, descent = renderer.get_text_width_height_descent(
                    label, text.get_fontproperties(), ismath)
                centre = (height / 2 - descent) / renderer.points_to_pixels(1)
                if isinstance(handle, Line2D):
                    handle.set_ydata([centre] * len(cast(Any, handle.get_ydata())))
                elif isinstance(handle, Collection):
                    cast(Any, handle).set_offsets([(point[0], centre) for point in cast(Any, handle.get_offsets())])

    def _artist(self, artist, factor: float) -> None:
        # Matplotlib exposes runtime aliases and private legend fields that
        # differ from its static stubs across supported releases.
        dynamic: Any = artist
        names: tuple[str, ...]
        if getattr(artist, "_hedgehogs_fixed_size", False):
            return
        if isinstance(artist, Text):
            self._property(artist, 'fontsize', dynamic.get_fontsize,
                           dynamic.set_fontsize, factor)
        if isinstance(artist, (Line2D, Patch)):
            self._property(artist, 'linewidth', dynamic.get_linewidth,
                           dynamic.set_linewidth, factor)
        if isinstance(artist, Line2D):
            self._property(artist, 'markersize', dynamic.get_markersize,
                           dynamic.set_markersize, factor)
            self._property(artist, 'markeredgewidth', dynamic.get_markeredgewidth,
                           dynamic.set_markeredgewidth, factor)
        if isinstance(artist, Collection):
            self._property(artist, 'linewidths', dynamic.get_linewidths,
                           dynamic.set_linewidths, factor)
            if hasattr(artist, 'get_sizes'):
                self._property(artist, 'sizes', dynamic.get_sizes,
                               dynamic.set_sizes, factor ** 2)
        if isinstance(artist, Legend):
            self._property(artist, 'legend_fontsize', lambda: dynamic._fontsize,
                           lambda value: setattr(artist, '_fontsize', value), factor)
        if isinstance(artist, (DrawingArea, PackerBase)):
            if isinstance(artist, DrawingArea):
                names = ("width", "height", "xdescent", "ydescent")
            else:
                names = ("pad", "sep")
            for name in names:
                if getattr(artist, name) is not None:
                    self._property(artist, name, lambda name=name: getattr(artist, name),
                                   lambda value, name=name: setattr(artist, name, value), factor)
            if isinstance(artist, DrawingArea):
                for handle in dynamic.get_children():
                    if isinstance(handle, Line2D):
                        self._property(handle, 'legend_x', handle.get_xdata,
                                       handle.set_xdata, factor)
                        self._property(handle, 'legend_y', handle.get_ydata,
                                       handle.set_ydata, factor)
                    elif isinstance(handle, Collection):
                        offsets = cast(Any, handle.get_offsets())
                        points = [float(value) for point in offsets for value in point]
                        if "legend_offsets" not in self.values.get(handle, {}):
                            # Use the same vertical centre as native line handles.
                            centre = (dynamic.height - dynamic.ydescent) / (2 * factor)
                            points[1::2] = [centre] * len(offsets)
                        points = self._scaled(handle, "legend_offsets", points, factor)
                        handle.set_offsets(list(zip(points[::2], points[1::2])))
                    elif isinstance(handle, Rectangle):
                        bounds = (handle.get_x(), handle.get_y(), handle.get_width(), handle.get_height())
                        handle.set_bounds(*self._scaled(handle, 'legend_bounds', bounds, factor))

# A third-party wrapper may retain an old hook after reset_style().
# Its installation must stay inactive when a later style is enabled.
_hook_generation: object | None = None
_reference_size: tuple[float, float] | None = None
_original_init: Callable | None = None
_original_draw: Callable | None = None
_original_tight_layout: Callable | None = None
_original_savefig: Callable | None = None
_original_scatter: Callable | None = None
_original_colorbar: Callable | None = None
_installed_init: Callable | None = None
_installed_draw: Callable | None = None
_installed_tight_layout: Callable | None = None
_installed_savefig: Callable | None = None
_installed_scatter: Callable | None = None
_installed_colorbar: Callable | None = None
_manage_margins = True
_inline_configuration: tuple[Any, dict[str, Any]] | None = None


def _configure_inline() -> None:
    global _inline_configuration
    if not _is_jupyter() or "backend_inline" not in str(plt.get_backend()):
        return
    try:
        from matplotlib_inline.backend_inline import InlineBackend
    except ImportError:
        return
    configuration: Any = InlineBackend.instance()
    if _inline_configuration is None:
        _inline_configuration = (configuration, dict(configuration.print_figure_kwargs))
    # Assigning the trait also updates IPython's registered figure formatters.
    configuration.print_figure_kwargs = {**configuration.print_figure_kwargs, "bbox_inches": None}


_font_methods: dict[str, tuple[Callable, Callable]] = {}


def _font_option(args: tuple[Any, ...], kwargs: dict[str, Any]) -> bool:
    from collections.abc import Mapping
    if any(kwargs.get(key) is not None for key in ('fontsize', 'size', 'labelsize', 'fontproperties')):
        return True
    for value in (*args[1:], kwargs.get('fontdict'), kwargs.get('prop')):
        if isinstance(value, Mapping) and any(value.get(key) is not None for key in ('fontsize', 'size')):
            return True
        if isinstance(value, FontProperties):
            return True
    return False


def _font_method(name: str, original: Callable, generation: object) -> Callable:
    @wraps(original)
    def method(axes, *args, **kwargs):
        result = original(axes, *args, **kwargs)
        if generation is not _hook_generation:
            return result
        if _font_option(args, kwargs):
            if name == 'tick_params':
                if kwargs.get('which', 'major') != 'minor':
                    for direction in ('x', 'y'):
                        if kwargs.get('axis', args[0] if args else 'both') in (direction, 'both'):
                            setattr(getattr(axes, direction + 'axis'), '_hedgehogs_font_explicit', True)
            elif isinstance(result, Legend):
                setattr(result, '_hedgehogs_font_explicit', True)
                for text in [*result.get_texts(), result.get_title()]:
                    setattr(text, '_hedgehogs_font_explicit', True)
            else:
                for text in result if isinstance(result, list) else (result,):
                    if isinstance(text, Text):
                        setattr(text, '_hedgehogs_font_explicit', True)
        if name == 'plot' and any(kwargs.get(key) is not None for key in ('linewidth', 'lw')):
            for line in result:
                setattr(line, '_hedgehogs_line_explicit', True)
        if name == 'plot' and any(kwargs.get(key) is not None for key in ('markeredgewidth', 'mew')):
            for line in result:
                setattr(line, '_hedgehogs_stroke_explicit', True)
        if name == 'bar' and any(kwargs.get(key) is not None for key in ('linewidth', 'lw')):
            for patch in result.patches:
                setattr(patch, '_hedgehogs_stroke_explicit', True)
        if name == 'legend' and isinstance(result, Legend):
            if kwargs.get('title_fontsize') is not None or kwargs.get('title_fontproperties') is not None:
                setattr(result.get_title(), '_hedgehogs_font_explicit', True)
        return result
    return method


def enable(reference_size: tuple[float, float], *, manage_margins: bool = True) -> None:
    """Attach a frozen reference size to figures created after set_style()."""
    global _hook_generation, _reference_size, _original_init, _original_draw, _installed_init, _installed_draw
    global _original_tight_layout, _installed_tight_layout, _manage_margins
    global _original_savefig, _installed_savefig
    global _original_colorbar, _installed_colorbar
    global _original_scatter, _installed_scatter
    _reference_size = (reference_size[0], reference_size[1])
    _manage_margins = manage_margins
    _configure_inline()
    if _original_init is not None:
        return
    generation = _hook_generation = object()
    _original_init = Figure.__init__
    _original_draw = Figure.draw
    _original_tight_layout = Figure.tight_layout
    _original_savefig = Figure.savefig
    _original_scatter = Axes.scatter
    _original_colorbar = Figure.colorbar
    for name in ('set_xlabel', 'set_ylabel', 'set_title', 'set_xticklabels',
                 'set_yticklabels', 'bar_label', 'legend', 'tick_params', 'plot', 'bar'):
        original = getattr(Axes, name)
        installed = _font_method(name, original, generation)
        _font_methods[name] = (original, installed)
        setattr(Axes, name, installed)
    original_init = _original_init
    original_draw = _original_draw
    original_tight_layout = _original_tight_layout
    original_savefig = _original_savefig
    original_scatter = _original_scatter
    original_colorbar = _original_colorbar

    @wraps(original_scatter)
    def scatter(axes, *args, **kwargs):
        if generation is not _hook_generation:
            return original_scatter(axes, *args, **kwargs)
        if (_reference_size is not None and kwargs.get('edgecolors') is None
                and 'edgecolor' not in kwargs):
            marker = kwargs.get('marker')
            marker = plt.rcParams['scatter.marker'] if marker is None else marker
            marker_style = marker if isinstance(marker, MarkerStyle) else MarkerStyle(marker)
            # Filled markers have distinct faces and outlines. Matplotlib
            # ignores outlines for unfilled markers such as lowercase x.
            if marker_style.is_filled():
                kwargs['edgecolors'] = 'black'
        result = original_scatter(axes, *args, **kwargs)
        if generation is not _hook_generation:
            return result
        if any(kwargs.get(key) is not None for key in ('linewidths', 'linewidth', 'lw')):
            setattr(result, '_hedgehogs_stroke_explicit', True)
        return result

    _installed_scatter = scatter
    setattr(Axes, "scatter", scatter)
    @wraps(original_init)
    def initialise(figure, *args, **kwargs):
        original_init(figure, *args, **kwargs)
        if generation is _hook_generation and _reference_size is not None:
            figure._hedgehogs_style = _FigureStyle(_reference_size, _manage_margins)

    @wraps(original_draw)
    def draw(figure, renderer):
        if generation is not _hook_generation:
            return original_draw(figure, renderer)
        style = getattr(figure, '_hedgehogs_style', None)
        if style is not None and _reference_size is not None:
            with _cached_legend_search(figure):
                style.apply(figure, renderer)
                return original_draw(figure, renderer)
        return original_draw(figure, renderer)

    @wraps(original_tight_layout)
    def tight_layout(figure, *args, **kwargs):
        if generation is not _hook_generation:
            return original_tight_layout(figure, *args, **kwargs)
        style = getattr(figure, "_hedgehogs_style", None)
        if style is not None and _reference_size is not None:
            style.apply(figure)
        return original_tight_layout(figure, *args, **kwargs)

    @wraps(original_savefig)
    def savefig(figure, *args, **kwargs):
        if generation is not _hook_generation:
            return original_savefig(figure, *args, **kwargs)
        style = getattr(figure, "_hedgehogs_style", None)
        if style is not None and _reference_size is not None:
            # An explicit Bbox export can skip the preliminary draw. Fit the
            # full canvas before Matplotlib enters its temporary crop context.
            style.apply(figure, figure._get_renderer())
        return original_savefig(figure, *args, **kwargs)

    @wraps(original_colorbar)
    def colorbar(figure, *args, **kwargs):
        if generation is not _hook_generation:
            return original_colorbar(figure, *args, **kwargs)
        style = getattr(figure, "_hedgehogs_style", None)
        cax = kwargs.get("cax", args[1] if len(args) > 1 else None)
        if (style is not None and style.manage_margins and _reference_size is not None
                and figure.get_layout_engine() is None and cax is None
                and len(figure.axes) > 1
                and all(getattr(axis, "get_subplotspec", lambda: None)() is not None
                        for axis in figure.axes)
                and not any(hasattr(axis, "_colorbar") for axis in figure.axes)):
            # Shared colourbars cannot be positioned by tight_layout. Select
            # the native constraint solver before colourbar creation, while
            # Matplotlib can still choose compatible colourbar ownership.
            figure.set_layout_engine("constrained")
        return original_colorbar(figure, *args, **kwargs)

    _installed_colorbar = colorbar
    setattr(Figure, "colorbar", colorbar)
    _installed_savefig = savefig
    setattr(Figure, "savefig", savefig)
    _installed_tight_layout = tight_layout
    setattr(Figure, "tight_layout", tight_layout)
    _installed_init, _installed_draw = initialise, draw
    setattr(Figure, "__init__", initialise)
    setattr(Figure, "draw", draw)


def disable() -> None:
    """Stop automatic sizing and restore Matplotlib's figure methods."""
    global _hook_generation, _reference_size, _original_init, _original_draw, _installed_init, _installed_draw
    global _original_tight_layout, _installed_tight_layout, _manage_margins
    global _original_savefig, _installed_savefig
    global _original_colorbar, _installed_colorbar
    global _original_scatter, _installed_scatter
    global _inline_configuration
    _hook_generation = None
    _reference_size = None
    for name, (original, installed) in _font_methods.items():
        if getattr(Axes, name) is installed:
            setattr(Axes, name, original)
    _font_methods.clear()
    if _inline_configuration is not None:
        configuration, previous = _inline_configuration
        current = dict(configuration.print_figure_kwargs)
        if current.get("bbox_inches") is None:
            if "bbox_inches" in previous:
                current["bbox_inches"] = previous["bbox_inches"]
            else:
                current.pop("bbox_inches", None)
            configuration.print_figure_kwargs = current
        _inline_configuration = None
    if _original_init is not None:
        if Figure.__init__ is _installed_init:
            setattr(Figure, "__init__", _original_init)
        if Figure.draw is _installed_draw:
            setattr(Figure, "draw", _original_draw)
        if Figure.tight_layout is _installed_tight_layout:
            setattr(Figure, "tight_layout", _original_tight_layout)
        if Figure.savefig is _installed_savefig:
            setattr(Figure, "savefig", _original_savefig)
        if Figure.colorbar is _installed_colorbar:
            setattr(Figure, "colorbar", _original_colorbar)
        if Axes.scatter is _installed_scatter:
            setattr(Axes, "scatter", _original_scatter)
        _original_scatter = None
        _installed_scatter = None
        _original_colorbar = None
        _installed_colorbar = None
        _original_savefig = None
        _installed_savefig = None
        _original_tight_layout = None
        _installed_tight_layout = None
        _original_init = None
        _original_draw = None
        _installed_init = None
        _installed_draw = None
