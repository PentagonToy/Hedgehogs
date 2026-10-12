# Changelog

## Unreleased

Use audited hybrid placement for automatic legends in `plots.show()` and `plots.save()`. Keep conventional locations when they have no overlap or a free-position proposal does not improve the score. Data-only changes require at least 10% relative improvement. Explicit locations and anchors remain fixed; plotted data is neither sampled nor automatically rasterised.

Verify representative Seaborn, scikit-learn, pandas and statsmodels plots through `plots.show()`. Give implicit categorical matrices and long axis titles space, and reserve side strips for figure legends. Preserve external canvas choices, explicit sizes and numerical content.

Improve external importance plots by expanding untouched default canvases for dense horizontal categories and compacting long raw endpoint values. Preserve explicit canvas sizes, formatted labels and font choices. Document SHAP's `show=False` finishing sequence and the separate HTML renderer.

Stabilise rendering-hook lifetimes and temporary caches across reset, third-party wrappers and failed draws. Verify axes consistency across equivalent presentation requirements, repeated finishing and edits.

Move panel, colour-bar, grid and minor-tick helpers to `hdg.figures`. Remove the former top-level aliases, `subplots`, `journal_preset`, `set_journal_style` and `finalize`. Create axes with `plt.subplots()`, configure styles with `set_style(figure_size=figsize(...))`, and finish figures with `plots.show()` or `plots.save()`. Custom tick formatting remains with Matplotlib.

## 0.0.1 — 8 October 2026

Initial Hedgehogs development release, adapted from Onsaemiro. Includes figure styling and finishing, native tree and pair plots, notebook and terminal tables, palettes and progress reporting.

`plots.save()` accepts a complete filename such as `figure.pdf`, or an extensionless path with `formats` for multiple outputs. Conflicting format selections raise `ValueError`.

Figure finishing refines default typography and numeric tick density while preserving explicit font options, custom ticks and plotted values.

Progress iteration uses `Progress(iterable, ...)`; delays use the standard `time.sleep()`. API references are grouped under `docs/api`.

Figure saving uses `plots.save(filename, fig=None, ...)`; the former top-level `export_figure()` is removed. `Table.to_dataframe()` exports formatted rows to an optional pandas or Polars backend.

Default outlines use bounded panel-area scaling independently of typography, retaining their weight across aspect ratios and preserving small marker faces.

Default data lines follow the same stroke scaling. Automatic legend placement searches inside the axes; explicit positions and external anchors are retained.
