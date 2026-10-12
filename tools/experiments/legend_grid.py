"""Development comparisons for classic, grid-only and default hybrid policies."""
from contextlib import contextmanager
from hedgehogs.plots import presentation
from hedgehogs.plots._legend import FIXED, windows, bin_points, clearance, propose, place, hybrid


@contextmanager
def experimental_placement(policy=hybrid):
    original = presentation._place_legend
    presentation._place_legend = policy
    try:
        yield
    finally:
        presentation._place_legend = original
