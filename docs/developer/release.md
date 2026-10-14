# Release preparation

Build each release from a clean, tested commit. `core/version.py` supplies the distribution version; `CHANGELOG.md` records its changes. Keep the source commit, built metadata, Git tag and GitHub release consistent.

## Build and verify

Install `build` and `twine` in the development environment, then build from an isolated source copy with output outside the working tree:

```bash
python -m build /path/to/source-copy --outdir /path/to/release/dist
python -m twine check --strict /path/to/release/dist/*
```

Verify the wheel contains the package and `py.typed`. The source archive also contains docs, tests, tutorials and rendering tools. Check imports and figure export from an installed wheel outside the checkout, then build a wheel from the source archive.

The Tests workflow checks Python 3.10, 3.12 and 3.13 and distribution files. Its `hedgehogs-distributions` artefact retains release candidates. Markdown-only pushes skip runtime CI; request a manual run before release if needed.

## Publish

Confirm project-name ownership and authentication on PyPI before uploading. A missing project page does not guarantee that its name can be registered. The repository contains no automatic publication workflow or stored credentials.

After approving the tested files, upload them through an authenticated environment:

```bash
python -m twine upload /path/to/release/dist/*
```

[Trusted Publishing](https://docs.pypi.org/trusted-publishers/) supports a dedicated GitHub upload workflow. Configure both the workflow and PyPI publisher before enabling uploads.

After publication, verify the installed version from PyPI, create the matching `v<version>` Git tag and GitHub release, and update the README installation instructions. Preserve published release tags and version files.
