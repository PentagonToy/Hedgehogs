"""Colour palettes and colour mapping utilities."""

import json
from collections.abc import Iterable, Mapping
from os import PathLike
from pathlib import Path
from numbers import Integral
from typing import Any
import warnings

from matplotlib.colors import is_color_like


_PALETTES = {
    "tableau10": {
        "colors": [
            "#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f",
            "#edc948", "#b07aa1", "#ff9da7", "#9c755f", "#bab0ac",
        ],
        "names": [
            "blue", "orange", "red", "teal", "green",
            "yellow", "purple", "pink", "brown", "grey",
        ],
    },
    "okabe-ito": {
        "colors": [
            "#0072B2", "#E69F00", "#D55E00", "#009E73",
            "#56B4E9", "#F0E442", "#CC79A7", "#000000",
        ],
        "names": [
            "blue", "orange", "red", "green",
            "cyan", "yellow", "purple", "black",
        ],
    },
    "paul-tol-vibrant": {
        "colors": [
            "#0077BB", "#33BBEE", "#009988", "#EE7733",
            "#CC3311", "#EE3377", "#BBBBBB",
        ],
        "names": [
            "blue", "cyan", "teal", "orange",
            "red", "magenta", "grey",
        ],
    },
    "paul-tol-bright": {
        "colors": [
            "#4477AA", "#EE6677", "#228833", "#CCBB44",
            "#66CCEE", "#AA3377", "#BBBBBB",
        ],
        "names": [
            "blue", "red", "green", "yellow",
            "cyan", "purple", "grey",
        ],
    },
    "paul-tol-muted": {
        "colors": [
            "#332288", "#88CCEE", "#44AA99", "#117733",
            "#999933", "#DDCC77", "#CC6677", "#882255", "#AA4499",
        ],
        "names": [
            "indigo", "cyan", "teal", "green",
            "olive", "sand", "rose", "wine", "purple",
        ],
    },
    "ibm": {
        "colors": ["#648FFF", "#785EF0", "#DC267F", "#FE6100", "#FFB000"],
        "names": ["blue", "indigo", "magenta", "orange", "gold"],
    },
}


class Palette:
    """Colour palette with both name-based and index-based access."""

    def __init__(self, names: Iterable[str], colors: Iterable[str]) -> None:
        self._names = list(names)
        self._colors = list(colors)
        self._map = dict(zip(self._names, self._colors))

    def __repr__(self) -> str:
        pairs = ", ".join(f"{n}={c}" for n, c in zip(self._names, self._colors))
        return f"Palette({pairs})"

    def __getitem__(self, key: int | slice | str):
        if isinstance(key, Integral) and not isinstance(key, bool):
            index = int(key)
            return self._colors[index % len(self._colors)]
        if isinstance(key, slice):
            return self._colors[key]
        if isinstance(key, str):
            return self._map[key.lower()]
        raise KeyError(key)

    def __contains__(self, key: object) -> bool:
        if isinstance(key, str):
            return key.lower() in self._map
        if isinstance(key, Integral) and not isinstance(key, bool):
            index = int(key)
            return -len(self._colors) <= index < len(self._colors)
        return False

    def __iter__(self):
        return iter(self._colors)

    def __len__(self) -> int:
        return len(self._colors)

    def keys(self):
        return self._map.keys()

    def values(self):
        return self._map.values()

    def items(self):
        return self._map.items()


def _resolve_palette(name: object) -> str:
    p = str(name).lower()
    if p in _PALETTES:                  return p
    if "vibrant" in p:                return "paul-tol-vibrant"
    if "bright" in p:                 return "paul-tol-bright"
    if "muted" in p:                  return "paul-tol-muted"
    if "tol" in p or "paul" in p:     return "paul-tol-vibrant"
    if "tab" in p or "tableau" in p:  return "tableau10"
    if "ibm" in p:                    return "ibm"
    if "okabe" in p or "ito" in p:    return "okabe-ito"
    warnings.warn(
        f"Unrecognised palette name {name!r}; falling back to 'okabe-ito'. "
        f"Known palettes: {sorted(_PALETTES)}",
        UserWarning,
        stacklevel=3,
    )
    return "okabe-ito"


def get_palette(palette: str | Palette = "okabe-ito", n: int | None = None) -> Palette:
    """Return a Palette object. Supports fuzzy name matching."""
    if isinstance(palette, Palette):
        if n is None:
            return palette
        source = palette
        if not isinstance(n, int) or isinstance(n, bool) or n < 1:
            raise ValueError("n must be a positive integer or None.")
        return Palette(list(source.keys())[:n], list(source.values())[:n])

    if n is not None and (
        not isinstance(n, int)
        or isinstance(n, bool)
        or n < 1
    ):
        raise ValueError("n must be a positive integer or None.")

    key = _resolve_palette(palette)
    entry = _PALETTES[key]
    limit = len(entry["colors"]) if n is None else min(n, len(entry["colors"]))
    return Palette(entry["names"][:limit], entry["colors"][:limit])


def build_color_map(
    labels: Iterable[Any],
    palette: str | Palette = "okabe-ito",
) -> dict[Any, str]:
    """Map unique labels to palette colours."""
    pal = get_palette(palette=palette)
    unique_labels = dict.fromkeys(labels)
    return {
        label: pal[index]
        for index, label in enumerate(unique_labels)
    }


def build_style_map(
    labels: Iterable[Any],
    palette: str | Palette = "okabe-ito",
) -> dict[Any, dict[str, str]]:
    """Map labels to distinct colour, line-style, and marker combinations."""
    colours = get_palette(palette=palette)
    line_styles = ("-", "--", "-.", ":")
    markers = ("o", "s", "^", "D", "v", "P", "X")
    return {
        label: {
            "color": colours[index],
            "linestyle": line_styles[index % len(line_styles)],
            "marker": markers[index % len(markers)],
        }
        for index, label in enumerate(dict.fromkeys(labels))
    }


def register_palette(
    name: str,
    colors: Mapping[str, str] | Iterable[str],
    names: Iterable[str] | None = None,
    *,
    overwrite: bool = False,
) -> Palette:
    """Register a custom palette for use by :func:`get_palette`."""
    key = str(name).strip().lower()
    if not key:
        raise ValueError("Palette name must not be empty.")
    if key in _PALETTES and not overwrite:
        raise ValueError(f"Palette {key!r} is already registered.")

    if isinstance(colors, Mapping):
        if names is not None:
            raise ValueError("names must be omitted when colors is a mapping.")
        palette_names = [str(value) for value in colors]
        palette_colors = list(colors.values())
    else:
        palette_colors = list(colors)
        palette_names = (
            [f"color-{index + 1}" for index in range(len(palette_colors))]
            if names is None
            else [str(value) for value in names]
        )

    if not palette_colors:
        raise ValueError("A palette must contain at least one colour.")
    if len(palette_names) != len(palette_colors):
        raise ValueError("Palette names and colors must have the same length.")
    if len(set(palette_names)) != len(palette_names):
        raise ValueError("Palette colour names must be unique.")

    invalid = [value for value in palette_colors if not is_color_like(value)]
    if invalid:
        raise ValueError(f"Invalid Matplotlib colour values: {invalid!r}.")

    _PALETTES[key] = {
        "names": palette_names,
        "colors": [str(value) for value in palette_colors],
    }
    return get_palette(key)


def save_palette(name: str, path: str | PathLike[str]) -> Path:
    """Save a registered palette as portable JSON."""
    key = _resolve_palette(name)
    destination = Path(path).expanduser()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps({"name": key, **_PALETTES[key]}, indent=2) + "\n",
        encoding="utf-8",
    )
    return destination


def load_palette(
    path: str | PathLike[str],
    *,
    name: str | None = None,
    overwrite: bool = False,
) -> Palette:
    """Load and register a palette saved by :func:`save_palette`."""
    source = Path(path).expanduser()
    payload = json.loads(source.read_text(encoding="utf-8"))
    palette_name = name or payload.get("name") or source.stem
    return register_palette(
        palette_name,
        payload["colors"],
        names=payload.get("names"),
        overwrite=overwrite,
    )
