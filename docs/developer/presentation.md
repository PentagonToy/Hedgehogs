# Presentation rules

Prioritise readable labels, units, ticks, and legends. Allocate panel area after typography. Figures convey patterns and comparisons; tables or accompanying data provide precise values.

## Reference defaults

`set_style()` applies these values at the reference canvas size. Journal presets and user settings override them.

| Element | Size | Weight |
| --- | ---: | --- |
| Labels and body text | 10.5 pt | Normal |
| Tick and legend text | 9.5 pt | Normal |
| Titles | 11.5 pt | Normal |
| Axis and node borders | 0.8 pt | — |
| Data lines and tree branches | 1.1 pt | — |
| Marker diameter | 4 pt | — |
| Marker area | 16 pt² | — |
| Marker edges | 0.5 pt | — |

Reserve bold for decision conditions and panel identifiers. Font selection prefers Times New Roman, then Times, then DejaVu Serif. These manuscript defaults suit a 12 pt draft; journal requirements take precedence. [PLOS](https://journals.plos.org/plosbiology/s/figures) specifies 8–12 pt figure text, whereas [Nature](https://www.nature.com/nature/for-authors/final-submission) specifies 5–7 pt at final size.

## Physical calibration

The Science reference canvas measures 2.24 × 2.20 inches. Default subplot fractions produce a 1.6128 × 1.452-inch plotting panel. Its shorter side, $L_{ref}=1.452$ inches, defines the pairplot scale reference.

Three raster examples support the earlier visual calibration. Dark-pixel bounds indicate these approximate dimensions.

| Example | Panel size | Tick glyph height | Glyph height / short side |
| --- | --- | --- | --- |
| Heatmap | 208 × 208 px | 12 px | 5.8% |
| Histogram | 222 × 222 px | 12 px | 5.4% |
| Scatter | 212 × 222 px | 12 px | 5.7% |

Screenshot scaling and anti-aliasing limit measurement accuracy. Visible glyph height also differs from nominal font size. Treat these measurements as visual evidence; use point sizes and renderer bounds for implementation tests. Current defaults increase text slightly relative to this earlier calibration.

## Scaling policy

| Drawing | Scale source | Behaviour |
| --- | --- | --- |
| Finished figure (`plots.show()` or `plots.save()`) | Point bases and bounded panel scaling | Refine default text roles and ticks, settle placement, then freeze geometry |
| Ordinary single panel | Canvas width and height relative to the frozen reference | Scale point sizes by the smaller dimension ratio |
| Ordinary subplot grid | Configured point sizes | Retain typography as panel count grows |
| Pairplot | Solved panel short side relative to $L_{ref}$ | Scale labels, ticks, legends, strokes, and marker diameters; retain a floor at the configured sizes |
| Decision tree | Measured node layout and available canvas | Fit text, boxes, and branches together |

Finished single panels at the reference canvas retain configured text sizes. In larger canvases with six or more bar-value labels, more than four category ticks, or more than four legend entries, calculate $s=\min(1.35,\max(1,\sqrt{L/L_{ref}}))$, where $L$ is the measured panel short side and $L_{ref}$ uses the style reference canvas with the default subplot fractions. Sparse panels use $s=\min(2.2,\max(1,L/L_{ref}))$ to retain the stronger proportions of the reference figures. Apply $s$ to default axis labels, ticks, titles and legends. Dense bar-value labels use the configured tick size multiplied by $\min(s,1.1)$; sparse value labels use $\max(1,0.9s)$. Marker areas retain their configured sizes. Default data-line widths follow the outline scale so curves remain stronger than the frame. Outline weight uses its own scale, independently of text density and the shortest panel side. Explicit stroke options retain their values.

For panel width $W$ and height $H$ in inches, let $R=\sqrt{WH/A_{ref}}$, with $A_{ref}$ the reference canvas area multiplied by the default subplot fractions. The outline multiplier is $o=\min(2.2,\max(1.6,1.6+0.4\log_2 R))$. Equal-area panels therefore keep equal outline weight across aspect ratios. The floor strengthens small-panel contours; logarithmic growth limits variation on larger canvases. Apply $o$ to default axes, patch, marker and legend-frame outlines. Default marker edges are limited to one quarter of the marker diameter to preserve a visible colour face; explicit stroke choices remain unchanged.

Cache the factor while canvas dimensions remain unchanged to avoid drift when labels or legends alter margins. Ordinary grids retain point sizes; native tree and pairplot sizing remains independent. Colour-bar typography follows its parent axes without replacing its locator. Default linear numeric axes use three to six intervals, based on physical length and tick-text size; fixed, logarithmic, date and custom locators remain unchanged.

For pairplots, calculate $s=\max(1,L_{min}/L_{ref})$ after reserving label and legend space. Multiply linear sizes by $s$ and marker areas by $s^2$. Recalculate from base values during each layout pass to prevent cumulative scaling. Variable count alone must not multiply font size.

Pairplots and trees manage their own scaling and skip the ordinary renderer multiplier. Pairplot fitting runs during construction; arbitrary later canvas resizing does not repeat it. Ordinary grids preserve point sizes as a readability safeguard, so their glyph-to-panel ratios can differ.

At reference size, a custom `linewidth` gives axes the ratio $0.8/1.1$ and marker edges retain $0.5/1.1$ relative to data lines. Default marker diameter follows `base_fontsize` relative to 10.5 pt, with a 2.5 pt minimum. Constants and reference geometry belong in `plots/typography.py`; see [Implementation ownership](architecture.md) for module responsibilities.

Finishing is an explicit output choice. Ordinary `plt.show()` retains the existing policy; `hdg.plots.show()` refines default text roles and numeric ticks from styled point bases, measures complete artists, and selects layout candidates. See [Implementation ownership](architecture.md#figure-finishing) for scoring and supported collisions.

## User control

Preserve explicit Matplotlib arguments and subsequent artist edits. Values such as `scatter(s=10000)` remain valid. Proportional resizing can scale explicit values, but must avoid caps and cumulative changes.

Users can adjust `set_style()` options, `rcParams`, plot arguments, and artist properties. Font options on axis labels, titles, legends, bar labels and tick methods remain explicit even when they match the configured default. Later font edits and custom locators also remain under author control. Returned figures and axes remain editable. `reset_style()` restores Matplotlib defaults.

## Final document size

LaTeX scales text with the complete figure. For exported width $W_{export}$ and insertion width $W_{print}$, calculate:

$$
f_{print}=f_{export}\frac{W_{print}}{W_{export}}.
$$

Inspect the PDF at its intended physical width. Select fewer variables, split figures, or choose a wider placement when text becomes too small. DPI controls raster resolution; it cannot compensate for reduced physical font size. Automatic layout optimises the supplied canvas and preferences, rather than inferring an unknown insertion width.

## Verification

Check panel dimensions, point sizes, legend placement, and clipping with and without `set_style()`. Compare matrices at equal panel sizes, and test explicit overrides and repeated rendering. Preserve single-panel and grid regression coverage when changing specialised plots. Numerical density tests and visual layout checks address separate requirements.
