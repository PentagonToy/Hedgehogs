"""Runtime environment helpers."""

import sys


def _is_jupyter():
    """Detect whether code is running inside a Jupyter / IPython kernel."""
    return "ipykernel" in sys.modules
