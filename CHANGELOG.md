# Changelog

## Unreleased

- Include documentation configuration, styles, scripts and reference data in source distributions, and support site builds without Git metadata.

- Apply consistent, bounded typography to all three axes, separate automatic ticks at shared corners and fit 3D axis labels inside the canvas while preserving explicit settings.

- Use the configured serif fallback for decision-tree text without repeated missing-Times font warnings.

- Default inside legends use bounded text and spacing during figure finishing, including shared legends. Axis typography, panel geometry and explicit font choices remain fixed; marker and patch outlines match their plotted sources.

## 0.0.4 — 18 October 2026

- Recognise the registered `inline` backend name as well as its module path for selected notebook display.

- Consume the current inline figure batch when selecting `plots.show(fig=...)`: display only that figure and remove all open figures from pyplot registration by default. Retain Figure objects for explicit saving or display and respect an explicit keep-open setting.

## 0.0.3 — 18 October 2026

- Avoid entering a GUI event loop when `plots.show(fig=...)` runs with a non-GUI backend, including headless Linux. The TestPyPI 0.0.2 candidate was not promoted to production because of this blocking path.

## 0.0.2 — 18 October 2026

- Make `plots.show(fig=...)` display only the selected figure, preserving other figures and suppressing the pending Jupyter inline flush.

- Add `figures.align(figures)` to match plotting boxes and automatic axis-label anchors across same-sized single-panel figures before export.

- Add centred titles to `plots.legend()` for panel and shared legends, with any column count.

- Add `plots.label()` for panel names, alphabetic or numeric bullets, optional halos and translucent label boxes. Accept axes grids directly and update labels on repeated calls.

- Add `plots.legend(shared=True)` for deduplicated common legends aligned with the panel grid. Preserve plotted marker outlines and reserve space for outside placement.

- Unify drawing, figure adjustments and output under `plots`. Retain former `figures` helper paths as compatibility imports.

- Apply `plots.square()` to all panels in the current figure by default, excluding colour bars. Retain `ax` for explicit panel selection.

- Preserve fitted title sizes during tight exports to prevent clipped text. Increase the default title padding from 6 to 7 pt.

- Align default single-panel vertical colour bars with the resolved plotting-box height.

- Add native attribution waterfall, dependence and decision plots with explicit ordering and preserved additive endpoints.

- Leave transparent gaps in tree connectors around branch labels, replacing opaque white label backgrounds.

- Add native Matplotlib `plots.force_plot()` and `plots.summary_plot()` for supplied single-output SHAP attributions, without JavaScript or a SHAP dependency.

- Add `categories` to `plots.decision_regions()` for legend display names mapped from original class labels.

- Keep panel typography independent of legend entry count. Adding example labels preserves axis, tick and title sizes.

- Match legend marker outlines to their plotted sources after figure finishing, including explicit edge widths.

- Let decision-region limits expand with added samples and refresh the vector background. Preserve explicit limits. Add `plots.legend(loc, domain, ncol)` for current-axes legends with inside or outside placement that clears labels and titles.

- Add `plots.decision_regions(X, y, classifier, markers=None, palette=None)` for two-feature classifiers. Accept arrays, lists, DataFrames and mappings of columns, retain model class order and draw on the current Matplotlib axes without adding a classifier-library dependency.

- Use audited hybrid placement for automatic legends in `plots.show()` and `plots.save()`. Keep conventional locations when they have no overlap or a free-position proposal does not improve the score. Data-only changes require at least 10% relative improvement. Explicit locations and anchors remain fixed; plotted data is neither sampled nor automatically rasterised.

- Verify representative Seaborn, scikit-learn, pandas and statsmodels plots through `plots.show()`. Give implicit categorical matrices and long axis titles space, and reserve side strips for figure legends. Preserve external canvas choices, explicit sizes and numerical content.

- Improve external importance plots by expanding untouched default canvases for dense horizontal categories and compacting long raw endpoint values. Preserve explicit canvas sizes, formatted labels and font choices. Document SHAP's `show=False` finishing sequence and the separate HTML renderer.

- Stabilise rendering-hook lifetimes and temporary caches across reset, third-party wrappers and failed draws. Verify axes consistency across equivalent presentation requirements, repeated finishing and edits.

- Remove the former top-level helper aliases, `subplots`, `journal_preset`, `set_journal_style` and `finalize`. Create axes with `plt.subplots()`, configure styles with `set_style(figure_size=figsize(...))`, and finish figures with `plots.show()` or `plots.save()`. Custom tick formatting remains with Matplotlib.

## 0.0.1 — 8 October 2026

- Initial Hedgehogs development release, adapted from Onsaemiro. Includes figure styling and finishing, native tree and pair plots, notebook and terminal tables, palettes and progress reporting.

- `plots.save()` accepts a complete filename such as `figure.pdf`, or an extensionless path with `formats` for multiple outputs. Conflicting format selections raise `ValueError`.

- Figure finishing refines default typography and numeric tick density while preserving explicit font options, custom ticks and plotted values.

- Progress iteration uses `Progress(iterable, ...)`; delays use the standard `time.sleep()`. API references are grouped under `docs/api`.

- Figure saving uses `plots.save(filename, fig=None, ...)`; the former top-level `export_figure()` is removed. `Table.to_dataframe()` exports formatted rows to an optional pandas or Polars backend.

- Default outlines use bounded panel-area scaling independently of typography, retaining their weight across aspect ratios and preserving small marker faces.

- Default data lines follow the same stroke scaling. Automatic legend placement searches inside the axes; explicit positions and external anchors are retained.
