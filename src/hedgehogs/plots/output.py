"""Finish and save Matplotlib figures."""

from collections.abc import Iterable, Mapping
from os import PathLike
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.figure import Figure


def save(
    filename: str | PathLike[str],
    *,
    fig: Figure | None = None,
    formats: Iterable[str] | None = None,
    dpi: float = 300,
    transparent: bool = False,
    bbox_inches: str | None = "tight",
    metadata: Mapping[str, Any] | None = None,
    close: bool = False,
    **savefig_kw: Any,
) -> tuple[Path, ...]:
    """Finish and save the current pyplot figure or an explicit ``fig``.

    A filename extension selects one format. Without an extension, ``formats``
    selects outputs and defaults to PDF and PNG. Return a tuple of written Paths.
    An extension combined with formats raises ValueError; an absent current
    figure also raises ValueError without creating an empty figure.

    Examples: ``save("figure.pdf")`` or ``save("figure", fig=fig,
    formats=("pdf", "png"))``. Explicit Matplotlib save options remain available.
    """
    base = Path(filename).expanduser()
    requested: tuple[str, ...]
    destinations: tuple[Path, ...]
    if "format" in savefig_kw:
        raise ValueError("Select the format with the filename extension or formats, not format.")
    if base.suffix:
        if formats is not None:
            raise ValueError("A filename extension and formats cannot be supplied together.")
        requested = (base.suffix[1:].lower(),)
        destinations = (base,)
    else:
        selected = ("pdf", "png") if formats is None else formats
        if isinstance(selected, str):
            selected = (selected,)
        requested = tuple(str(value).lower().lstrip(".") for value in selected)
        if not requested or any(not value for value in requested):
            raise ValueError("formats must contain at least one file format.")
        destinations = tuple(base.with_suffix(f".{suffix}") for suffix in requested)
    if fig is None:
        if not plt.get_fignums():
            raise ValueError("No current figure to save; create one or supply fig.")
        fig = plt.gcf()
    from .presentation import prepare
    prepare(fig)
    base.parent.mkdir(parents=True, exist_ok=True)

    options = {
        "dpi": dpi,
        "transparent": transparent,
        "bbox_inches": bbox_inches,
        "metadata": metadata,
        **savefig_kw,
    }

    with plt.rc_context({"pdf.fonttype": 42, "ps.fonttype": 42, "savefig.bbox": None}):
        for destination, file_format in zip(destinations, requested):
            fig.savefig(destination, format=file_format, **options)

    if close:
        plt.close(fig)

    return destinations
