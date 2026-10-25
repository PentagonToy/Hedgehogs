# Presentation rules

Keep labels, ticks and legends readable at the final document size. Figures communicate patterns and comparisons; tables or accompanying data provide precise values.

## Reference defaults

`set_style()` configures the following bases. Journal presets and user options override them; finishing applies the scaling rules below.

| Element | Base size |
| --- | ---: |
| Labels and body text | 10.5 pt |
| Tick and legend text | 9.5 pt |
| Titles | 11.5 pt |
| Axis and node borders | 0.9 pt |
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
| Finished single panel | Apply bounded default text and outline scales |
| Pairplot | Scale from the smallest solved panel short side; retain configured size floors |
| Decision tree | Fit text, boxes and branches to the measured node layout |

Reference-size panels retain configured text sizes. For a larger panel, let $L$ be its short side. Dense panels include 3D axes, images, meshes, at least six bar-value labels or more than four category ticks. Legend count does not change panel typography; placement and outside spacing are handled separately.

| Text role | Multiplier |
| --- | --- |
| Dense panel defaults | $s=\min(1.35,\max(1,\sqrt{L/L_{ref}}))$ |
| Other panel defaults | $s=\min(2.2,\max(1,L/L_{ref}))$ |
| Dense bar-value labels | $\min(s,1.1)$ |
| Sparse bar-value labels | $\max(1,0.9s)$ |

Apply panel scaling to default labels, ticks and titles. Legends start at the same scale, then fit the space budget below. Bar-value labels start from the configured tick size; marker areas retain their configured sizes. 3D axes use bounded dense typography and default label spacing based on tick size. Automatic linear tick budgets use projected axis lengths and omit endpoints to avoid shared-corner collisions. Finishing fits projected labels inside the canvas without changing the view, limits or box aspect. Explicit fonts, label padding and tick locators remain unchanged.

Default strokes scale independently of text density:

$$
R=\sqrt{WH/A_{ref}},\qquad o=\min(2.2,\max(1.6,1.6+0.4\log_2 R)).
$$

Here $W,H$ are panel dimensions and $A_{ref}$ is the reference canvas area times the default subplot fractions. Equal-area panels retain equal stroke weight. Default marker edges are capped at one quarter of their diameter; explicit strokes retain their values.

Relative to data-line width, axes use $0.9/1.1$ and marker edges $0.5/1.1$. Marker diameter scales with `base_fontsize` relative to 10.5 pt, with a 2.5 pt floor.

Default 2D linear ticks use three to six intervals. 3D budgets use projected lengths, then reduce automatic ticks when measured labels overlap. Custom, fixed, logarithmic and date locators stay unchanged. Colour-bar text follows its parent axes.

Pairplots use $s=\max(1,L_{min}/L_{ref})$ after reserving labels and legend space. Linear sizes scale by $s$ and marker areas by $s^2$. Pairplots and trees own their sizing and bypass ordinary scaling. Pairplot fitting runs during construction; later canvas resizing does not repeat it.

## Legend fitting and limits

Default inside legends in `show()` and `save()` target at most 60% of panel width, 40% of height and 20% of area. Shared inside legends use the combined panel bounds. Text and spacing scale together; marker sizes and stroke weight follow the plotted sources, including bar and histogram patches. The font floor is `max(7 pt, 0.75 × configured legend size)`; readability takes priority over these soft targets. Explicit fonts and external anchors retain user control. Native figure legends and the specialised pairplot and tree layouts retain their own sizing. Default inside legend fitting preserves panel geometry and axis typography.

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

Default vertical colour bars for one parent panel follow its resolved plotting-box height, including fixed box aspects. Non-default shrink, custom colour-bar axes or anchors, shared bars and extension markers retain native placement.
