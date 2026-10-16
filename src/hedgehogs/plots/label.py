"""Panel labels with optional contrasting text outlines."""

from collections.abc import Sequence
from math import isfinite
from numbers import Real
from typing import Any

import matplotlib.pyplot as plt
import matplotlib.patheffects as effects
from matplotlib.axes import Axes
from matplotlib.colors import to_rgba
from matplotlib.text import Text
import numpy as np


_LOCATIONS = {
    'upper left': (.04, .96, 'left', 'top'),
    'upper center': (.5, .96, 'center', 'top'),
    'upper right': (.96, .96, 'right', 'top'),
    'center left': (.04, .5, 'left', 'center'),
    'center': (.5, .5, 'center', 'center'),
    'center right': (.96, .5, 'right', 'center'),
    'lower left': (.04, .04, 'left', 'bottom'),
    'lower center': (.5, .04, 'center', 'bottom'),
    'lower right': (.96, .04, 'right', 'bottom'),
}


def _alphabet(index: int) -> str:
    result = ''
    while index:
        index, digit = divmod(index - 1, 26)
        result = chr(97 + digit) + result
    return result


class _PanelLabel(Text):
    _hedgehogs_panel_label = True
    _auto_colour = True
    _halo = True
    _hedgehogs_font_explicit = False
    _background_colour: Any = None

    def set_color(self, color):
        self._auto_colour = False
        super().set_color(color)

    def _background(self):
        axes = self.axes
        assert axes is not None
        # Transparent export temporarily replaces axes face colours with none.
        # Retain the displayed background so saving does not invert the text.
        if self._background_colour is None or not axes.figure.canvas.is_saving():
            self._background_colour = axes.get_facecolor()[:3]
        colour = np.asarray(self._background_colour)
        point = self.get_transform().transform(self.get_position())
        for image in sorted(axes.images, key=lambda item: item.get_zorder()):
            if not image.get_visible():
                continue
            data = image.get_array()
            if data is None or data.size == 0:
                continue
            x, y = image.get_transform().inverted().transform(point)
            left, right, bottom, top = image.get_extent()
            u, v = (x - left) / (right - left), (y - bottom) / (top - bottom)
            if not (0 <= u <= 1 and 0 <= v <= 1):
                continue
            if image.origin == 'upper':
                v = 1 - v
            row = min(int(v * data.shape[0]), data.shape[0] - 1)
            column = min(int(u * data.shape[1]), data.shape[1] - 1)
            value = data[row, column]
            if np.ma.is_masked(value) or not np.isfinite(value).all():
                continue
            rgba = np.asarray(image.cmap(image.norm(value)) if data.ndim == 2 else value, dtype=float)
            if data.ndim == 3 and np.issubdtype(data.dtype, np.integer):
                rgba /= 255.
            alpha = rgba[3] if len(rgba) == 4 else 1.
            opacity = image.get_alpha()
            if opacity is not None:
                opacity_values = np.asarray(opacity)
                alpha *= float(opacity_values[row, column] if opacity_values.ndim else opacity_values)
            colour = rgba[:3] * alpha + colour * (1 - alpha)
        background = self.get_bbox_patch()
        if background is not None:
            red, green, blue, alpha = to_rgba(background.get_facecolor())
            colour = np.asarray([red, green, blue]) * alpha + colour * (1 - alpha)
        return colour

    def draw(self, renderer):
        if self._auto_colour:
            rgb = self._background()
            linear = np.where(rgb <= .04045, rgb / 12.92, ((rgb + .055) / 1.055) ** 2.4)
            super().set_color('black' if np.dot(linear, [.2126, .7152, .0722]) > .179 else 'white')
        if self._halo:
            rgb = np.asarray(to_rgba(self.get_color())[:3])
            outline = 'white' if np.dot(rgb, [.2126, .7152, .0722]) < .5 else 'black'
            self.set_path_effects([effects.withStroke(linewidth=float(self.get_fontsize()) * .12,
                                                      foreground=outline, joinstyle='round')])
        else:
            self.set_path_effects([])
        super().draw(renderer)


def label(
    labels: Sequence[str] | str | None = None,
    *,
    bullets: str | None = 'a',
    axes: Any = None,
    loc: str = 'upper left',
    halo: bool = True,
    box: bool = False,
    color: Any = None,
    fontsize: float | None = None,
    fontweight: str = 'bold',
) -> list[Text]:
    """Label selected panels, defaulting to the current figure's visible axes.

    Use bullets='a' for a), b), ...; '1' for numbers; None for literal labels.
    Accept a single axes, nested axes or a NumPy grid without flattening.
    halo adds a contrasting outline; box adds a translucent white background.
    Automatic colour uses the axes background
    and images at the label anchor. Repeated calls update existing labels.
    Return editable Text artists. Explicit color and fontsize remain available.
    """
    aliases = {'a': 'a', 'alphabet': 'a', 'alpha': 'a',
               '1': '1', 'n': '1', 'number': '1', 'numbers': '1'}
    if bullets is not None and (not isinstance(bullets, str) or bullets not in aliases):
        raise ValueError("bullets must be 'a', '1' or None.")
    if not isinstance(loc, str) or loc not in _LOCATIONS:
        raise ValueError('loc must name an upper, centre or lower panel position.')
    if not isinstance(halo, bool):
        raise TypeError('halo must be True or False.')
    if not isinstance(box, bool):
        raise TypeError('box must be True or False.')
    if fontsize is not None and (isinstance(fontsize, bool) or not isinstance(fontsize, Real)
                                 or not isfinite(fontsize) or fontsize <= 0):
        raise ValueError('fontsize must be positive and finite.')
    if color is not None:
        to_rgba(color)

    def flatten(value):
        if isinstance(value, Axes):
            return [value]
        if isinstance(value, (str, bytes)):
            raise TypeError('axes must contain Matplotlib axes.')
        try:
            return [ax for group in value for ax in flatten(group)]
        except TypeError as error:
            raise TypeError('axes must contain Matplotlib axes.') from error

    selected = ((plt.gcf().axes if plt.get_fignums() else []) if axes is None else flatten(axes))
    panels = list(dict.fromkeys(ax for ax in selected if ax.get_visible() and not hasattr(ax, '_colorbar')))
    names = [''] * len(panels) if labels is None else ([labels] if isinstance(labels, str) else list(labels))
    if len(names) != len(panels) or any(not isinstance(name, str) for name in names):
        raise ValueError('Supply one string label per selected panel.')
    x, y, horizontal, vertical = _LOCATIONS[loc]
    size = plt.rcParams['font.size'] if fontsize is None else fontsize
    # Validate text styling before changing any existing panel labels.
    Text(fontsize=size, fontweight=fontweight)
    result: list[Text] = []
    for index, (ax, name) in enumerate(zip(panels, names), 1):
        prefix = '' if bullets is None else ((_alphabet(index) if aliases[bullets] == 'a' else str(index)) + ')')
        content = ' '.join(part for part in (prefix, name) if part)
        artist = next((text for text in ax.texts if isinstance(text, _PanelLabel)), None)
        if artist is None:
            artist = _PanelLabel(transform=ax.transAxes, clip_on=False, zorder=10)
            artist.set_in_layout(False)
            ax.add_artist(artist)
        artist.set(text=content, x=x, y=y, ha=horizontal, va=vertical,
                   fontsize=size, fontweight=fontweight, color='black' if color is None else color)
        artist._auto_colour = color is None
        artist._halo = halo
        artist.set_bbox({'boxstyle': 'square,pad=0.2', 'facecolor': 'white',
                         'edgecolor': 'none', 'alpha': .8, 'linewidth': 0} if box else None)
        artist._hedgehogs_font_explicit = fontsize is not None
        state = getattr(ax.figure, '_hedgehogs_style', None)
        if state is not None:
            state.values.pop(artist, None)
        result.append(artist)
    return result
