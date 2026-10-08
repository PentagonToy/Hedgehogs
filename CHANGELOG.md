# Changelog

## 0.0.1 — 8 October 2026

Initial Hedgehogs development release, adapted from Onsaemiro. Includes figure styling and finishing, native tree and pair plots, notebook and terminal tables, palettes and progress reporting.

`plots.save()` accepts a complete filename such as `figure.pdf`, or an extensionless path with `formats` for multiple outputs. Conflicting format selections raise `ValueError`.

Figure finishing refines default typography and numeric tick density while preserving explicit font options, custom ticks and plotted values.

Progress iteration uses `Progress(iterable, ...)`; delays use the standard `time.sleep()`. API references are grouped under `docs/api`.

Figure saving uses `plots.save(filename, fig=None, ...)`; the former top-level `export_figure()` is removed. `Table.to_dataframe()` exports formatted rows to an optional pandas or Polars backend.

Default outlines use bounded panel-area scaling independently of typography, retaining their weight across aspect ratios and preserving small marker faces.

Default data lines follow the same stroke scaling. Automatic legend placement searches inside the axes; explicit positions and external anchors are retained.
