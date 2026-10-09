# Installation

Hedgehogs requires Python 3.10 or newer. Install the PyPI release in the Python environment used for the project.

<!-- tabs -->
### pip

```console
pip install hedgehogs
```

### uv

```console
uv pip install hedgehogs
```

<!-- /tabs -->

uv requires a virtual environment; an existing one is sufficient.

<details>
<summary>Create a virtual environment if needed</summary>

Create and activate an environment before running the install command above.

<!-- tabs -->
### pip

```console
python3 -m venv .venv
source .venv/bin/activate
```

### uv

```console
uv venv
source .venv/bin/activate
```

<!-- /tabs -->

See the [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/) if uv is unavailable.

</details>

## Check the environment

```console
python -c "import sys, hedgehogs; print(sys.executable); print(hedgehogs.__file__)"
```

For notebooks, select a kernel from the same Python environment. Hedgehogs installs Matplotlib, IPython and Rich. DataFrame and statistical examples may need pandas, Polars, SciPy or scikit-learn for the selected workflow; see each [API reference](api/README.md) for its requirements.

The style requests Times New Roman. If it is unavailable, Matplotlib selects a fallback font. Install the intended font in the rendering environment for matching typography; Python package installation does not supply it. TeX rendering is optional and requires a working TeX installation when `use_tex=True`.

Continue with the [first figure](quick-start.md). A PyPI release can differ from the site's [source revision](versions.md).

## Install from main

<!-- tabs -->
### pip

```console
pip install "git+https://github.com/PentagonToy/Hedgehogs.git@main"
```

### uv

```console
uv pip install "git+https://github.com/PentagonToy/Hedgehogs.git@main"
```

<!-- /tabs -->

Replace `main` with a tag or commit for reproducible work.

## Editable installation

```console
git clone https://github.com/PentagonToy/Hedgehogs.git
cd Hedgehogs
```

<!-- tabs -->
### pip

```console
pip install -e .
```

### uv

```console
uv pip install -e .
```

<!-- /tabs -->

Use editable installation when modifying the source. See the [development overview](README.md) for implementation and verification references.
