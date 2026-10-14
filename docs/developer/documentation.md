# Documentation site

The independent [Hedgehogs site](https://pentagontoy.github.io/Hedgehogs/) publishes this repository's guides and API references through GitHub Pages. Nordic documentation remains separate.

## Source ownership

Edit `docs/`. The hook maps `home.md` to the homepage and the documentation index to `overview.md`. It serves SVGs with content-hash revisions and points source links to GitHub. The [Sources page](https://pentagontoy.github.io/Hedgehogs/versions/) records the build commit.

`others/assets/icon.svg` is the canonical transparent symbol used by the README, homepage, header and favicon. Keep compact padding and check light and dark backgrounds after artwork changes. Header and favicon URLs are versioned automatically by content hash; update the README image revision when replacing the SVG.

## Build and publish

Use a documentation environment containing `requirements-docs.txt`:

```console
python -m mkdocs build --strict --site-dir /path/to/output/site
```

The Documentation workflow builds and deploys relevant pushes to `main`. Builds render Markdown and serve committed gallery SVGs; they do not execute notebooks or scientific examples.

## Gallery updates

`tools/docs/gallery.py` renders synthetic examples into `docs/assets/gallery/`. After a relevant presentation change, run it explicitly, inspect the SVGs and commit them with the source. Site builds and ordinary tests do not regenerate the gallery.

Check generated links, artwork, installation tabs and light/dark presentation before publishing. Existing API pages remain the canonical references; keep introductory guides short.

## Notebook examples

The site imports selected notebook code and saved outputs without execution. Edit the notebook to update its page. Saved outputs are historical previews, not new validation results.

## Portable Markdown

Repository pages use standard Markdown and HTML details. Installation option groups use hidden `tabs` comments; the site hook converts them to MkDocs tabs. Check both ordinary Markdown and the built site after editing shared pages.
