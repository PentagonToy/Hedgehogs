# Implementation ownership

Keep style configuration in `hedgehogs`, explicit artist helpers in `hedgehogs.figures` and specialised drawings and output in `hedgehogs.plots`. Matplotlib owns figures and artists; Hedgehogs supplies style, layout, and portable output.

| Module | Responsibility |
| --- | --- |
| `plots/style.py` | Defaults, journal presets, and style lifecycle |
| `plots/typography.py` | Reference dimensions, default text roles and physical tick spacing |
| `plots/presentation.py` | Finishing, collision checks, and bounded legend search |
| `plots/rendering.py` | Matplotlib hooks, proportional sizing, and layout corrections |
| `plots/tree.py` | Decision-tree labels, node layout, and drawing |
| `plots/pairplot.py` | Numeric-column selection, density estimates, and scatter matrices |
| `plots/output.py` | Current-figure selection and multi-format saving |
| `figures.py` | Explicit panel, colour-bar, grid and minor-tick adjustments |
| `core/palette.py` | Palette definitions and series styles |
| `tables/table.py` | Formatted tables and exports |
| `terminal/progress.py`, `terminal/output.py` | Progress and status output |
| `core/environment.py` | Shared notebook detection |

## Repository structure

The project builds one distribution from `src/hedgehogs`. Group implementation and tests by responsibility; keep shared support in `core` and public imports in the package facade. `docs` contains user guides and developer references, `tutorials` contains runnable notebooks, and `tools` contains reproducible rendering scripts. Generated outputs belong outside the source tree.

```text
Hedgehogs/
├── src/hedgehogs/
│   ├── core/
│   ├── plots/
│   ├── tables/
│   └── terminal/
├── tests/{core,plots,tables,terminal}/
├── docs/
├── tutorials/
├── tools/
└── pyproject.toml
```

Keep the dependency direction explicit: presentation modules may import `core`; shared support must avoid importing presentation modules. Each module owns its implementation, while the root package exposes the existing user interface. Add a package boundary only for a distinct responsibility.

## Rendering lifecycle

`set_style()` configures `rcParams` and installs rendering hooks. Figures retain their reference size; `reset_style()` restores Matplotlib methods and defaults. Option wrappers distinguish explicit font and stroke choices from omitted defaults. Hooks avoid duplicate installation and preserve subsequent third-party replacements. Retired wrappers delegate without applying Hedgehogs changes, including after style is enabled again.

During ordinary styled draws, a local cache reuses native automatic legend searches with matching dimensions, renderer, axes bounds, limits and transform matrix. Remove temporary wrappers and cached results after each draw, including setup and rendering failures. A temporary wrapper retained by another library delegates to native search after its draw ends. Explicit anchors and instance search overrides bypass the cache.

## Figure finishing

`plots.show()` and `plots.save()` share `presentation.prepare()`:

1. Retain author edits and restore point-sized bases.
2. Measure geometry and refine default typography with `draw_without_rendering()`, falling back to a canvas draw when unavailable.
3. Select automatic legend positions and separate supported bar-value labels.
4. Freeze layout and render the complete figure.

During measurement, automatic internal legends use a temporary upper-right position and do not reserve layout space. Restore their automatic request and layout flag on exit. Explicit locations and anchors keep their normal layout participation.

Evaluate the ten named internal legend locations once, ranking clipping, text overlap and data overlap, then named-location order. Exclude the legend's own children from overlap checks. Transform visible point collections once and count containment with inclusive NumPy bounds, ignoring masked and non-finite coordinates. Retain every valid point. Patch bounds, line intersections and collection offsets approximate occupancy. Finishing avoids native `best` searches, automatic rasterisation and point reduction.

Bar-value labels move outward along their bars while retaining endpoint anchors and category rows. Warn about unresolved label collisions or a legend that cannot fit inside its axes. Data overlap ranks legend candidates without generating a warning.

Unchanged repeated output retains geometry. Changing the internal legend policy re-evaluates placement without reopening axes layout. Input changes reopen measurement and automatic selection. Data digests detect supported edits without retaining full data copies between calls; producing the digest still reads data and allocates temporary bytes. Keep caches local to their measurement stage and restore temporary state on failure.

Matplotlib remains the behavioural reference; Hedgehogs owns its documented finishing priorities. See [Reference behaviour and reproducibility](presentation.md#reference-behaviour-and-reproducibility) for placement guarantees, and [Validation rules](../../tests/README.md) for regression checks.

## Specialised drawings

Tree nodes share widths by depth and align at their top edges. The renderer measures text before drawing square boxes and arrowed branches. It fits the complete diagram to the destination canvas and exempts its artists from a second rendering multiplier.

Classifier `value` arrays can contain counts or normalised shares. Recover weighted counts before formatting; `samples` reports unweighted observations. Node colour follows the majority class, while shading represents its share relative to equal class shares. Named palette roles use orange, blue, green, purple, and red when available; other palettes retain their own order.

Pairplots share outer x axes by column and y axes by row. Diagonal inset axes retain independent density scales. Gaussian KDE uses Scott bandwidth on a 256-point grid and counts duplicate observations at full weight. Singleton and constant groups fall back to histograms. Display limits can truncate KDE tails.

Pairplot layout measures legend dimensions, reserves its space, and settles panel sizes with typography in bounded passes. See [Presentation proportions](presentation.md) for the scale calculation. Fitting runs during construction; later artist edits remain available, while arbitrary canvas resizing does not repeat this calculation.

## Verification

When built-in colours change, update the [palette table](../api/palettes.md) and regenerate previews with `python tools/docs/render_palette_swatches.py others/palettes`.

Choose the smallest relevant selection using [Validation rules](../../tests/README.md). Run the full suite once when functional changes have settled or before release. The following scripts render PNG, PDF, and SVG examples into a supplied output directory.

| Script | Coverage | Additional example dependency |
| --- | --- | --- |
| `tools/render_figures.py` | Regression, scatter, colour bars, and explicit diagrams | NumPy |
| `tools/render_trees.py` | Decision trees at depths 2 and 5 | scikit-learn |
| `tools/render_presentation.py` | Bar charts before and after finishing | None |
| `tools/render_pairplots.py` | Full and lower-triangle Iris matrices | scikit-learn |

```bash
python tools/render_pairplots.py /path/to/output
```

Check package discovery and imports from a built wheel after moving modules. Run figure tests with DejaVu Serif and the local serif font because glyph metrics affect legend fitting and label margins. Test point-size scaling separately from adaptive fitting.

Re-measure fitted titles with the active renderer. Keep Matplotlib private-field access inside rendering adapters.
