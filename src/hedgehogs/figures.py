"""Compatibility imports; use hedgehogs.plots for figure helpers."""

from .plots.helpers import (
    annotate_panels, style_colorbar, apply_grid, enable_minor_ticks, square,
)

__all__ = ['annotate_panels', 'style_colorbar', 'apply_grid', 'enable_minor_ticks', 'square']


def __dir__() -> list[str]:
    return sorted(__all__)
