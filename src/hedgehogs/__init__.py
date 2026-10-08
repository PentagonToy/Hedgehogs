"""Hedgehogs — publication-quality scientific visualisation and reporting utilities."""

from .core.version import __version__, __date__
from .core.constants import EPS
from .core.palette import (
    Palette,
    get_palette,
    build_color_map,
    build_style_map,
    register_palette,
    save_palette,
    load_palette,
)
from .plots.style import (
    set_style,
    reset_style,
    journal_preset,
    set_journal_style,
    figsize,
    subplots,
)
from .plots.helpers import (
    finalize,
    style_colorbar,
    annotate_panels,
    enable_minor_ticks,
    apply_grid,
)
from . import plots
from .tables import Table
from .terminal import Progress
from .terminal import echo, rule
from .core.info import info

__all__ = [
    "EPS",
    "Palette",
    "get_palette",
    "build_color_map",
    "build_style_map",
    "register_palette",
    "save_palette",
    "load_palette",
    "set_style",
    "reset_style",
    "journal_preset",
    "set_journal_style",
    "figsize",
    "subplots",
    "finalize",
    "style_colorbar",
    "annotate_panels",
    "enable_minor_ticks",
    "apply_grid",
    "plots",
    "Table",
    "Progress",
    "echo",
    "rule",
    "info",
]


def __dir__() -> list[str]:
    """List the supported public interface and package metadata."""
    return sorted([*__all__, "__version__", "__date__"])
