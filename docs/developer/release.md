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

## TestPyPI

TestPyPI is separate from production PyPI. Use the selected package version unchanged, and keep the exact wheel and source archive for promotion after validation. Verify the downloaded TestPyPI files against the recorded SHA-256 checksums.

```console
python -m twine upload --repository testpypi /path/to/release/dist/*
```

Use a TestPyPI API token through the upload prompt or a configured credential store. Do not put tokens in source files or command arguments. TestPyPI versions cannot be overwritten; changed files require a new version. A Git tag records source identity, not publication status.

## Publish

The repository contains no automatic publication workflow or stored credentials. Authenticate to the existing PyPI project before uploading.

After approving the tested files, upload them through an authenticated environment:

```bash
python -m twine upload /path/to/release/dist/*
```

[Trusted Publishing](https://docs.pypi.org/trusted-publishers/) supports a dedicated GitHub upload workflow. Configure both the workflow and PyPI publisher before enabling uploads.

After publication, verify the installed version from PyPI, create the matching `v<version>` Git tag and GitHub release, and confirm that installation instructions remain current. Preserve published release tags and version files.
