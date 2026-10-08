"""Write documentation colour swatches from the package palette definitions."""
from pathlib import Path
import argparse

from hedgehogs.core.palette import _PALETTES


def render(destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for palette_name, entry in _PALETTES.items():
        for colour in entry["colors"]:
            hexadecimal = colour.upper()
            name = hexadecimal[1:].lower()
            svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="48" height="24" viewBox="0 0 48 24">'
                   f'<title>{hexadecimal}</title><rect x="1" y="1" width="46" height="22" '
                   f'fill="{hexadecimal}" stroke="#777777" stroke-width="1"/></svg>\n')
            (destination / f"{name}.svg").write_text(svg)
        width = 28 * len(entry["colors"])
        blocks = "".join(
            f'<rect x="{i * 28 + 1}" y="1" width="26" height="22" '
            f'fill="{colour}" stroke="#777777" stroke-width="1"/>'
            for i, colour in enumerate(entry["colors"])
        )
        strip = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="24" '
                 f'viewBox="0 0 {width} 24"><title>{palette_name}</title>{blocks}</svg>\n')
        (destination / f"{palette_name}.svg").write_text(strip)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path, nargs="?", default=Path("others/palettes"))
    render(parser.parse_args().destination)
