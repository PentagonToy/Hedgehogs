"""Run the plotting notebook and refresh its saved previews and gallery."""

import argparse
import base64
from io import BytesIO
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import matplotlib
matplotlib.use("module://matplotlib_inline.backend_inline")

from matplotlib.figure import Figure


def refresh(workspace: Path) -> None:
    source = ROOT / "tutorials/plots.ipynb"
    notebook = json.loads(source.read_text())
    destination = ROOT / "docs/assets/gallery"
    figures: list[bytes] = []

    def capture(figure: Figure) -> None:
        buffer = BytesIO()
        figure.savefig(buffer, format="png", dpi=150, bbox_inches="tight",
                       transparent=False, facecolor="white")
        figures.append(buffer.getvalue())

    original_directory = Path.cwd()
    with TemporaryDirectory(prefix="plots-", dir=workspace) as workdir:
        os.chdir(workdir)
        try:
            namespace = {"__name__": "__main__"}
            with patch("IPython.display.display", capture):
                count = 0
                for cell in notebook["cells"]:
                    if cell["cell_type"] != "code":
                        continue
                    count += 1
                    first = len(figures)
                    code = "".join(cell["source"])
                    exec(compile(code, f"{source.name}:{count}", "exec"), namespace)
                    cell["execution_count"] = count
                    cell["outputs"] = [
                        {"data": {"image/png": base64.b64encode(png).decode("ascii")},
                         "metadata": {}, "output_type": "display_data"}
                        for png in figures[first:]
                    ]
        finally:
            os.chdir(original_directory)

    if not figures:
        raise RuntimeError("The plotting notebook did not display any figures.")

    destination.mkdir(parents=True, exist_ok=True)
    for index, png in enumerate(figures, 1):
        (destination / f"plots-{index}.png").write_bytes(png)
    source.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True,
                        help="Existing directory for temporary notebook outputs")
    refresh(parser.parse_args().workspace.resolve())
