# Documentation site

The independent [Hedgehogs site](https://pentagontoy.github.io/Hedgehogs/) publishes this repository's guides and API references through GitHub Pages. Nordic documentation remains separate.

## Source ownership

Edit the original documents under `docs/`. The site hook maps `home.md` to the homepage, preserves the repository documentation index as `overview.md`, and serves the existing SVG artwork locally. SVG links include a content revision so artwork changes invalidate cached previews. Source and notebook links point to GitHub. The [Sources page](https://pentagontoy.github.io/Hedgehogs/versions/) records the build commit.

`others/assets/icon.svg` contains the full logo and wordmark; `icon-symbol.svg` contains the symbol for the header and favicon. Update both after artwork changes and check light and dark backgrounds.

## Build and publish

Use a documentation environment containing `requirements-docs.txt`:

```console
python -m mkdocs build --strict --site-dir /path/to/output/site
```

The Documentation workflow builds and deploys relevant pushes to `main`. Builds render Markdown and serve committed gallery SVGs; they do not execute notebooks or scientific examples.

## Gallery updates

`tools/docs/gallery.py` renders the synthetic examples from the checked-out package into `docs/assets/gallery/`. Run it explicitly in a development environment after a relevant presentation change, inspect the SVGs, then commit the results alongside the source. Keep the gallery code and examples aligned. Gallery generation is separate from the documentation build and ordinary tests.

Check generated links, artwork, installation tabs and light/dark presentation before publishing. Existing API pages remain the canonical references; keep introductory guides short.

## Notebook examples

Selected notebook cells are imported as copyable code during the documentation build without execution. Edit the original notebook to update its page. Pages include saved PNG and table/text outputs, labelled as historical previews. Saved outputs are previews, not new validation results.

## Portable Markdown

Repository pages use standard Markdown and HTML details. Installation option groups use hidden `tabs` comments; the site hook converts them to MkDocs tabs. Check both ordinary Markdown and the built site after editing shared pages.
