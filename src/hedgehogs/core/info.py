"""Package information utilities."""

import matplotlib.pyplot as plt

from .version import __version__, __date__


def info():
    """Print version and dependency info."""
    text = (
        f"Hedgehogs  v{__version__}  ({__date__})\n"
        f"  matplotlib  {plt.matplotlib.__version__}"
    )
    print(text)
    return text
