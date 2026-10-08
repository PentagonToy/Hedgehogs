# Release preparation

Build each release from a clean, tested commit. `core/version.py` supplies the distribution version; `CHANGELOG.md` records its changes. Keep the source commit, built metadata, Git tag and GitHub release consistent.

## Build and verify

Install `build` and `twine` in the development environment, then build from an isolated source copy with output outside the working tree:

```bash
python -m build /path/to/source-copy --outdir /path/to/release/dist
python -m twine check --strict /path/to/release/dist/*
```

Inspect both the wheel and source archive. The wheel contains the package and `py.typed`; the source archive also includes documentation, tests, tutorials and rendering tools. Install the wheel outside the source checkout and verify its version, public imports and figure export. Build a wheel from the source archive to verify that it is self-contained.

The GitHub Tests workflow runs Python 3.10, 3.12 and 3.13 tests, then builds and checks distribution files. Markdown-only pushes skip runtime CI; dispatch the workflow manually before release when those are the only changes. Its `hedgehogs-distributions` artifact retains the release candidates. A successful local run alone does not establish that the remote workflow passed.

## Publish

Confirm project-name ownership and authentication on PyPI before uploading. A missing project page does not guarantee that its name can be registered. The repository contains no automatic publication workflow or stored credentials.

After approving the tested files, upload them through an authenticated environment:

```bash
python -m twine upload /path/to/release/dist/*
```

PyPI can also authenticate a dedicated GitHub publication workflow through [Trusted Publishing](https://docs.pypi.org/trusted-publishers/). Configure that workflow and its PyPI publisher together before enabling automatic uploads. [PyPA packaging guidance](https://packaging.python.org/en/latest/tutorials/packaging-projects/) describes building and uploading distributions.

After publication, verify the installed version from PyPI, create the matching `v<version>` Git tag and GitHub release, and update the README installation instructions. Preserve published release tags and version files.
