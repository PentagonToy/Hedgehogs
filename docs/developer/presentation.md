# Presentation rules

Keep labels, ticks and legends readable at the final document size. Figures communicate patterns and comparisons; tables or accompanying data provide precise values.

## Reference defaults

`set_style()` configures the following bases. Journal presets and user options override them; finishing applies the scaling rules below.

| Element | Base size |
| --- | ---: |
| Labels and body text | 10.5 pt |
| Tick and legend text | 9.5 pt |
| Titles | 11.5 pt |
| Axis and node borders | 1.4 pt |
| Data lines and tree branches | 1.1 pt |
| Marker diameter / area | 4 pt / 16 pt² |
| Marker edges | 0.5 pt |
| Major tick length | 4 pt |

Fonts prefer Times New Roman, Times, then DejaVu Serif. Ordinary text uses normal weight; decision conditions and panel labels may use bold. Minor ticks default to off. Legend handle length, text gap, border padding and row spacing are 1.5, 0.5, 0.35 and 0.35 times its font size.

## Reference geometry

The Science canvas measures 2.24 × 2.20 inches. Default subplot fractions give a 1.6128 × 1.452-inch panel, with reference short side $L_{ref}=1.452$ inches. A custom style reference uses its canvas dimensions and the same default fractions for scaling calculations.

## Scaling policy

| Drawing | Policy |
| --- | --- |
| Ordinary single panel | Scale point sizes by the smaller canvas width/height ratio to its stored reference |
| Ordinary subplot grid | Retain configured point sizes as panel count grows |
| Finished single panel | Apply bounded text sizing and fixed physical strokes |
| Pairplot | Scale text and marker sizes from the smallest solved panel; retain stroke widths |
| Decision tree | Fit text, boxes and branches to the measured node layout |

Reference-size panels and grids retain configured text sizes. For a larger single panel, let $L$ be its short side. Dense panels include 3D axes, images, meshes, at least six bar-value labels or more than four category ticks. Legend count does not change panel typography; placement and outside spacing are handled separately.

| Text role | Multiplier |
| --- | --- |
| Dense panel defaults | $s=\min(1.15,\max(1,\sqrt{L/L_{ref}}))$ |
| Other panel defaults | $s=\min(1.2,\max(1,L/L_{ref}))$ |
| Dense bar-value labels | $\min(s,1.1)$ |
| Sparse bar-value labels | $\max(1,0.9s)$ |

Default tick labels, legend text and legend titles start at the axis label size. Panel titles remain slightly larger. Legends fit the space budget below. Bar-value labels start from the configured tick size; marker areas retain their configured sizes. 3D axes use bounded dense typography and default label spacing based on tick size. Automatic linear tick budgets use projected axis lengths and omit endpoints to avoid shared-corner collisions. Finishing fits projected labels inside the canvas without changing the view, limits or box aspect. Explicit fonts, label padding and tick locators remain unchanged.

Axis frames retain their configured width in points across ordinary draws, finished figures and pairplots. Per-spine widths remain in effect after resizing and export. At the same output DPI the physical stroke width maps to the same pixel width. If you resize the exported image in a document, its stroke scales with the image.

Finishing uses the configured frame width for legend boxes and as the minimum for default data lines and patches. Tick strokes default to 1.05 pt; major and minor marks are 4 and 2 pt long. Default marker edges use 0.8 pt, capped at one quarter of the diameter. These weights do not depend on panel area or aspect. Explicit strokes retain their values.

Default 2D linear ticks use three to six intervals. 3D budgets use projected lengths, then reduce automatic ticks when measured labels overlap. Custom, fixed, logarithmic and date locators stay unchanged. Colour-bar text follows its parent axes.

Pairplots use $s=\max(1,L_{min}/L_{ref})$ after reserving labels and legend space. Text and marker diameters scale by $s$ and marker areas by $s^2$. Pairplots and trees own their sizing and bypass ordinary scaling. Pairplot fitting runs during construction; later canvas resizing does not repeat it.

## Legend fitting and limits

Default inside legends in `show()` and `save()` target at most 60% of panel width, 40% of height and 20% of area. Shared inside legends use the combined panel bounds. Text and spacing scale together; marker sizes and stroke weight follow the plotted sources, including bar and histogram patches. The font floor is `max(7 pt, 0.75 × configured axis label size)`; readability takes priority over these soft targets. Explicit fonts and external anchors retain user control. Native figure legends and the specialised pairplot and tree layouts retain their own sizing. Default inside legend fitting preserves panel geometry and axis typography.

Automatic outside legends use 90% of canvas width and 40% of height above or below panels, or 40% of width and 90% of height beside panels, with the same font floor. Location and column count remain fixed. With automatic outside placement, long default 2D axis labels limit panel typography enlargement to the measured label space; configured sizes remain the minimum. Actual anchors and a 3 pt canvas border further bound the available span. Shared outside legends reserve measured overflow together with their panel decorations before layout is frozen. Explicit anchors bypass this fitting.

Ordinary drawing retains its 60% axes-width or 90% figure-width target, 40% height target and scaled 6 pt floor. These are Hedgehogs defaults, not publication standards. See the [measured reference examples](../../others/references/legend-typography.json).

`show()` and `save()` refine typography and measure geometry before placing automatic legends. Explicit locations and anchors stay fixed. Large legends may need a wider canvas or external anchor. See [Legend placement mathematics](legend-experiment.md) for the search and acceptance rules.

Finishing preserves every plotted point and vector output unless rasterisation is requested. See [Figure finishing](architecture.md#figure-finishing).

### Reference behaviour and reproducibility

Matplotlib defines artist semantics, transforms, text measurement and explicit placement. Hedgehogs adds its finishing priorities, so automatic `loc="best"` can select a different position from native Matplotlib. Selection is deterministic for unchanged inputs and environment; repeated output must avoid cumulative changes.

For line and scatter plots, data-only edits retain axes geometry when canvas, limits, ticks, labels, fonts and layout stay unchanged. Automatic legends may move. Changes to text or ticks can require a new layout. For separate same-sized single-panel figures, [`figures.align`](../api/figures.md#figuresalign) shares fitted margins and automatic axis-label anchors before export. Explicit label coordinates remain unchanged. It freezes the common plotting boxes without retaining an implicit group; reapply after edits.

Fonts, backends, formats, canvas size and library versions can change automatic positions. Use a named location or explicit anchor for fixed placement.

## User control

Matplotlib arguments, `rcParams` and artist methods remain available. Explicit sizes, strokes, ticks and anchors retain user control. Proportional resizing may scale explicit sizes without cumulative changes or caps. `reset_style()` restores defaults.

## Final document size

For exported width $W_{export}$ and insertion width $W_{print}$, text scales as:

$$
f_{print}=f_{export}\frac{W_{print}}{W_{export}}.
$$

Inspect the figure at its intended physical width and follow the target journal's requirements. Split crowded figures or use a wider placement when text becomes too small. DPI controls raster resolution; it cannot compensate for reduced physical text size.

There is no universal title–label–legend–tick size ladder. [Nature](https://research-figure-guide.nature.com/figures/preparing-figures-our-specifications/) specifies 5–7 pt figure text and 8 pt panel letters; [Elsevier](https://www.elsevier.com/about/policies-and-standards/author/artwork-and-media-instructions/artwork-sizing) suggests about 7 pt normal lettering. These refer to final printed size, independently of manuscript body size.

## Verification

Check dimensions, readability, containment, explicit overrides and repeated output using both the configured serif font and DejaVu Serif. Test ordinary drawing separately from finishing and export. Compare figures at equal physical panel sizes. See [Validation rules](../../tests/README.md) for test selection.

## Default canvas fitting

Untouched implicit horizontal-bar canvases with six or more categories use a minimum width of 4.76 inches and height of `min(12, 0.26 * categories + 1)` inches. Explicit construction sizes and later resizing are preserved.

Default raw horizontal bar endpoint values longer than ten characters use four significant digits. This applies only to plain data-coordinate text matching the unformatted bar width and row; formatted strings and explicit fonts retain ownership. The plotted values are unchanged.

Implicit categorical heatmaps and panels with axis titles exceeding 90% of the corresponding canvas dimension use at least 4.76 × 4.12 inches. Attached colourbars count with their parent. Numeric matrix ticks alone do not enlarge a canvas.

These panels use bounded dense typography, so enlargement does not recreate text collisions. External grids and explicit canvases retain their geometry.

Figure legends clearly placed along the left or right edge reserve a side strip during managed grid layout, matching the existing top/bottom reservation. This prevents native external grid legends from covering the last panel; legend locations remain unchanged.

Default colour bars follow the resolved plotting-box height or width, including bars attached to individual panels in a grid. Shared bars align when their parents share the relevant two edges. The minimum thickness is 5 pt or three times the outline width, subject to the space Matplotlib reserves. Explicit aspect controls thickness. Explicit shrink or anchors, custom colour-bar axes and extension markers retain Matplotlib placement.

In constrained or compressed layouts, a vertical colour bar shared by one row uses a default pad of 2% of the parent span. Horizontal panel padding defaults to 5 pt for these figures. Matplotlib still reserves space for text. Explicit colour-bar padding and non-default horizontal spacing take precedence.

## Fixed-aspect panel grids

Finishing measures each row from the union of its panel and colour-bar bounds, including labels, ticks and panel titles. It packs those rows with 4 pt top and bottom margins and targets 6 pt gaps, including below a figure title. Gaps can decrease to 2 pt to fit the supplied canvas. The canvas shrinks only in height; the panel dimensions, axis limits and colour scales stay fixed.

This pass follows the initial Matplotlib layout and can replace its vertical spacing even when `figsize` or a layout engine was specified. It applies to complete rectangular grids with at least two rows, fixed-aspect panels and colour bars that belong to a single row. Spanning panels, insets, figure legends and figures with additional figure text retain their initial layout. If labels cannot fit, finishing retains the original canvas and reports the limiting dimension.
