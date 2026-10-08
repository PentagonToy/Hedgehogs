# Implementation ownership

Keep public configuration in `hedgehogs` and specialised drawings in `hedgehogs.plots`. Matplotlib owns figures and artists; Hedgehogs supplies style, layout, and portable output.

| Module | Responsibility |
| --- | --- |
| `plots/style.py` | Defaults, journal presets, and style lifecycle |
| `plots/typography.py` | Reference dimensions, default text roles and physical tick spacing |
| `plots/presentation.py` | Finishing, collision checks, and bounded legend search |
| `plots/rendering.py` | Matplotlib hooks, proportional sizing, and layout corrections |
| `plots/tree.py` | Decision-tree labels, node layout, and drawing |
| `plots/pairplot.py` | Numeric-column selection, density estimates, and scatter matrices |
| `plots/output.py` | Current-figure selection and multi-format saving |
| `plots/helpers.py` | Adjustments to existing figures |
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

`set_style()` configures `rcParams` and installs rendering hooks. New figures retain their reference size. Hooks apply sizing and layout before drawing or export; `reset_style()` restores Matplotlib methods and defaults.

Option wrappers record explicit font and stroke choices on labels, titles, legends, bar labels and tick methods. This distinguishes an explicit default-sized choice from an omitted option. Keep original methods and installed wrappers distinct. Repeated activation must avoid duplicate wrappers, and restoration must preserve later third-party replacements. Explicit artist values remain editable; proportional resizing may scale them, but must avoid cumulative changes or size caps.

## Figure finishing

`plots.show()` and `plots.save()` share `presentation.prepare()`. Ordinary rendering hooks remain active for existing callers. Finishing marks the selected figure, restores cached point-sized bases, and avoids a second canvas multiplier. Changes made after a previous draw are retained where the cache records them. `typography.refine_presentation()` applies bounded default role sizes and physical tick spacing before collision fitting.

Measure legend candidates with the current renderer. Rank them by clipping, text overlap, data overlap and distance from the requested placement, in that order. Exclude the legend’s own children from overlap checks. Patch bounds, line intersections and collection offsets approximate data occupancy.

Search only internal candidates for `loc="best"`. Named locations and anchors remain fixed. Never shrink axes to make room for an automatically external legend. Data overlap ranks candidates but does not itself generate a warning; an oversized legend can warn that an explicit anchor or larger canvas is needed.

Bar-label candidates move outward along their bars, preserving endpoint anchors and category rows. The search uses a bounded set of offsets and warns about remaining label collisions. It does not change values, axis limits, or plot orientation. Golden-ratio preferences and general-purpose numerical optimisers are excluded from this stage.

Solve layout before output, then freeze its geometry across renderers. Later finishing calls compare geometry and style inputs; unchanged figures retain their layout. Data digests avoid copying arrays. Changed inputs reactivate the saved engine and repeat measurement.

Test repeated calls, author edits, outside legends and consistent PNG/PDF/SVG output. Extend collision handling in `presentation.py`.

## Specialised drawings

Tree nodes share widths by depth and align at their top edges. The renderer measures text before drawing square boxes and arrowed branches. It fits the complete diagram to the destination canvas and exempts its artists from a second rendering multiplier.

Classifier `value` arrays can contain counts or normalised shares. Recover weighted counts before formatting; `samples` reports unweighted observations. Node colour follows the majority class, while shading represents its share relative to equal class shares. Named palette roles use orange, blue, green, purple, and red when available; other palettes retain their own order.

Pairplots share outer x axes by column and y axes by row. Diagonal inset axes retain independent density scales. Gaussian KDE uses Scott bandwidth on a 256-point grid and counts duplicate observations at full weight. Singleton and constant groups fall back to histograms. Display limits can truncate KDE tails.

Pairplot layout measures legend dimensions, reserves its space, and settles panel sizes with typography in bounded passes. See [Presentation proportions](presentation.md) for the scale calculation. Fitting runs during construction; later artist edits remain available, while arbitrary canvas resizing does not repeat this calculation.

## Verification

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

The renderer re-measures fitted titles to account for raster hinting. Adapter types isolate dynamic Matplotlib hooks and private fields from differences between supported type stubs.
