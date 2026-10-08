"""Specialised Matplotlib plots with Hedgehogs presentation defaults."""

from .tree import tree
from .pairplot import pairplot
from .presentation import show
from .output import save

__all__ = ["tree", "pairplot", "show", "save"]


def __dir__() -> list[str]:
    """List the public plotting functions rather than implementation modules."""
    return sorted(__all__)
