"""Publication-quality Matplotlib style configuration."""

from collections.abc import Mapping

import matplotlib.pyplot as plt

from ..core.palette import Palette, get_palette
from . import rendering
from .typography import (REFERENCE_CANVAS_INCHES, REFERENCE_LABEL_POINTS,
                         REFERENCE_AXES_WIDTH, REFERENCE_LINE_WIDTH,
                         REFERENCE_MARKER_AREA, REFERENCE_MARKER_EDGE_WIDTH,
                         REFERENCE_TICK_POINTS, REFERENCE_LEGEND_POINTS)


_active_palette: Palette | None = None


_FONT_SERIF = ("Times New Roman", "Times", "DejaVu Serif")


_REF_WIDTH = 6.0


_SCALE_EXPONENT = 0.5


_DATA_MARGIN = 0.05


_MARKER_TO_FONT_RATIO = REFERENCE_MARKER_AREA ** .5 / REFERENCE_LABEL_POINTS


_MIN_MARKERSIZE = 2.5


_DEFAULT_SUBPLOT = {
    "left":   0.24,
    "bottom": 0.22,
    "right":  0.96,
    "top":    0.88,
}


_JOURNAL_PRESETS = {
    "nature": {
        "single": (3.50, 2.65),
        "double": (7.20, 4.80),
    },
    "science": {
        "single": REFERENCE_CANVAS_INCHES,
        "double": (4.76, 3.40),
    },
    "ieee": {
        "single": (3.50, 2.55),
        "double": (7.16, 4.80),
    },
    "aps": {
        "single": (3.40, 2.60),
        "double": (7.00, 4.80),
    },
}


def _compute_scale(fig_width: float, exponent: float = _SCALE_EXPONENT) -> float:
    raw = (fig_width / _REF_WIDTH) ** exponent
    return max(0.55, min(2.2, raw))


def set_style(
    base_fontsize: float = REFERENCE_LABEL_POINTS,
    linewidth: float = REFERENCE_LINE_WIDTH,
    figure_size: tuple[float, float] = REFERENCE_CANVAS_INCHES,
    subplot: Mapping[str, float] | None = None,
    use_tex: bool = False,
    auto_scale: bool = False,
    scale_exponent: float = _SCALE_EXPONENT,
    palette: str = "okabe-ito",
) -> None:
    """
    Apply presentation defaults and enable proportional sizing for new figures.

    figure_size defines the reference canvas. At drawing time, point-based
    sizes follow the smaller width/height ratio for a single panel.
    Subplot grids retain configured point sizes regardless of panel count.
    auto_scale retains its optional initial width-based calculation.
    Native axes geometry is preserved; exports retain the configured canvas.
    Explicit geometry, layout engines and tight cropping remain available.
    """
    global _active_palette
    sp = {**_DEFAULT_SUBPLOT, **(subplot or {})}
    s = _compute_scale(figure_size[0], scale_exponent) if auto_scale else 1.0

    fs    = base_fontsize * s
    tick_fs = fs - (REFERENCE_LABEL_POINTS - REFERENCE_TICK_POINTS) * s
    legend_fs = fs - (REFERENCE_LABEL_POINTS - REFERENCE_LEGEND_POINTS) * s
    lw    = linewidth * s
    axis_lw = lw * REFERENCE_AXES_WIDTH / REFERENCE_LINE_WIDTH
    elw   = lw * REFERENCE_MARKER_EDGE_WIDTH / REFERENCE_LINE_WIDTH
    ms    = max(_MIN_MARKERSIZE, _MARKER_TO_FONT_RATIO * fs)
    major = 4.0 * s
    minor = 3.0 * s

    plt.rcParams.update({
        # ── Font ──
        "font.family":           "serif",
        "font.serif":            list(_FONT_SERIF),
        "text.latex.preamble":   r"\usepackage{newtxtext,newtxmath}",
        "font.size":             fs,
        "axes.titlesize":        fs + 1 * s,
        "axes.labelsize":        fs,
        "xtick.labelsize":       tick_fs,
        "ytick.labelsize":       tick_fs,

        # ── Figure ──
        "figure.figsize":        figure_size,
        "figure.dpi":            150,
        "figure.autolayout":     False,
        "savefig.dpi":           300,
        "savefig.bbox":          None,
        "pdf.fonttype":          42,
        "ps.fonttype":           42,

        # ── Subplot position (fixed fractions) ──
        "figure.subplot.left":   sp["left"],
        "figure.subplot.bottom": sp["bottom"],
        "figure.subplot.right":  sp["right"],
        "figure.subplot.top":    sp["top"],

        # ── Axes ──
        "axes.linewidth":        axis_lw,
        "axes.spines.top":       True,
        "axes.spines.right":     True,
        "axes.labelpad":         6.0 * s,
        "axes.xmargin":          _DATA_MARGIN,
        "axes.ymargin":          _DATA_MARGIN,
        "axes.titlepad":         6.0 * s,
        "axes.formatter.useoffset":    False,
        "axes.formatter.use_mathtext": True,
        "axes.formatter.limits":       [-4, 5],

        # ── Ticks ──
        "xtick.direction":       "out",
        "ytick.direction":       "out",
        "xtick.major.size":      major,
        "ytick.major.size":      major,
        "xtick.minor.size":      minor,
        "ytick.minor.size":      minor,
        "xtick.major.width":     axis_lw * 0.8,
        "ytick.major.width":     axis_lw * 0.8,
        "xtick.minor.visible":   False,
        "ytick.minor.visible":   False,
        "xtick.major.pad":       4.0 * s,
        "ytick.major.pad":       4.0 * s,

        # ── Lines & Markers ──
        "lines.linewidth":       lw,
        "lines.markersize":      ms,
        "lines.markeredgewidth": elw,
        "lines.markeredgecolor": "black",

        # ── Patches & Scatter ──
        "scatter.edgecolors":    "black",
        "patch.edgecolor":       "black",
        "patch.linewidth":       elw,
        "patch.force_edgecolor": True,

        # ── Legend ──
        "legend.fontsize":       legend_fs,
        "legend.frameon":        True,
        "legend.framealpha":     1.0,
        "legend.facecolor":      "white",
        "legend.edgecolor":      "black",
        "legend.fancybox":       False,
        "legend.handlelength":   1.5,
        "legend.handletextpad":  0.5,
        "legend.borderpad":      0.35,
        "legend.borderaxespad":  0.4,
        "legend.labelspacing":   0.35,
        "legend.columnspacing":  0.8,
        "legend.markerscale":    0.85,

        # ── Text & Math ──
        "text.usetex":           use_tex,
        "mathtext.fontset":      "stix",

        # ── Grid ──
        "axes.grid":             False,
        "grid.linestyle":        "--",
        "grid.color":            "black",
        "grid.alpha":            0.8,
        "grid.linewidth":        lw * 0.67,
        "axes.axisbelow":        True,
    })

    plt.rcParams["axes.prop_cycle"] = plt.cycler(
        color=list(get_palette(palette))
    )
    _active_palette = get_palette(palette)
    rendering.enable(figure_size, manage_margins=subplot is None)


def reset_style() -> None:
    """Restore matplotlib defaults."""
    global _active_palette
    rendering.disable()
    plt.rcdefaults()
    _active_palette = None


def figsize(name: str = "science", column: str = "single") -> tuple[float, float]:
    """Return journal starting dimensions in inches for single/double columns."""
    key = str(name).lower()
    column_key = str(column).lower()
    if key not in _JOURNAL_PRESETS:
        raise ValueError(f"Unknown journal {name!r}; expected one of {tuple(_JOURNAL_PRESETS)}.")
    if column_key not in {"single", "double"}:
        raise ValueError("column must be 'single' or 'double'.")
    return _JOURNAL_PRESETS[key][column_key]
