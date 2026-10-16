"""Draw, adjust, finish and save scientific Matplotlib plots."""

from .tree import tree
from .pairplot import pairplot
from .decision_regions import decision_regions
from .legend import legend
from .attributions import force_plot, summary_plot, waterfall_plot, dependence_plot, decision_plot
from .presentation import show
from .output import save
from .helpers import annotate_panels, style_colorbar, apply_grid, enable_minor_ticks, square
from .label import label

__all__ = ["tree", "pairplot", "decision_regions", "legend", "force_plot", "summary_plot", "waterfall_plot", "dependence_plot", "decision_plot", "show", "save", "annotate_panels", "style_colorbar", "apply_grid", "enable_minor_ticks", "square", "label"]


def __dir__() -> list[str]:
    """List the public plotting functions rather than implementation modules."""
    return sorted(__all__)
