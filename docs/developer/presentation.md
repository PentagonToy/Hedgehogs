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

Font selection prefers Times New Roman, then Times, then DejaVu Serif. Use normal weight for ordinary text and bold for decision conditions or panel identifiers. Minor ticks are disabled by default. Legend handle length, handle-to-text spacing, border padding and row spacing are 1.5, 0.5, 0.35 and 0.35 times the legend font size, respectively.

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

Finished reference-size panels retain configured text sizes. For a larger single panel with short side $L$, use $s=\min(1.35,\max(1,\sqrt{L/L_{ref}}))$ when it has at least six bar-value labels, more than four category ticks or more than four legend entries. Otherwise use $s=\min(2.2,\max(1,L/L_{ref}))$. Apply $s$ to default axis labels, ticks, titles and legends. Dense bar-value labels use the configured tick size times $\min(s,1.1)$; sparse values use $\max(1,0.9s)$. Marker areas retain their configured sizes.

Outline scaling uses panel area independently of text density. For panel width $W$ and height $H$, let $R=\sqrt{WH/A_{ref}}$, where $A_{ref}$ is the style reference canvas area multiplied by the default subplot fractions. Use $o=\min(2.2,\max(1.6,1.6+0.4\log_2 R))$ for default data lines, axes, patch, marker and legend-frame outlines. Equal-area panels retain equal outline weight across aspect ratios. Default marker edges are capped at one quarter of the diameter; explicit stroke choices retain their values.

A custom `linewidth` gives axes and marker edges the respective base ratios $0.9/1.1$ and $0.5/1.1$ to data lines. Marker diameter follows `base_fontsize` relative to 10.5 pt, with a 2.5 pt minimum. Default linear numeric axes use three to six intervals according to physical length and text size; custom, fixed, logarithmic and date locators retain their settings. Colour-bar typography follows its parent axes.

Pairplots use $s=\max(1,L_{min}/L_{ref})$ after reserving labels and legend space. Linear sizes scale by $s$ and marker areas by $s^2$. Pairplots and trees own their sizing and bypass ordinary scaling. Pairplot fitting runs during construction; later canvas resizing does not repeat it.

## Legend fitting and limits

Ordinary rendering targets a legend width of 60% of its axes, or 90% of the canvas for a figure legend, and a height of 40% of the container. A scaled 6 pt reference font floor takes priority over these compactness targets. Wider fallback fonts can exceed the target at that floor. Explicit external anchors bypass this fitting.

`plots.show()` and `plots.save()` share finishing. They refine default typography, measure geometry, select automatic axes-legend positions and then render. Automatic legends do not reserve provisional layout space. The search ranks ten internal positions by clipping, text overlap and data overlap, using named-location order to break ties. Named locations and explicit anchors retain their placement. Oversized legends or long labels may need a larger canvas, shorter text or an external anchor.

Finishing preserves plotted data and avoids automatic rasterisation or subsampling. PDF and SVG scatter output remains vector unless the author requests rasterisation. See [Figure finishing](architecture.md#figure-finishing) for implementation details.

### Reference behaviour and reproducibility

Matplotlib defines artist semantics, transforms, text measurement and explicit placement. Hedgehogs adds its finishing priorities, so automatic `loc="best"` can select a different position from native Matplotlib. Selection is deterministic for unchanged inputs and environment; repeated output must avoid cumulative changes.

For line and scatter figures with the same canvas, limits, ticks, labels, fonts and layout configuration, changes to data alone should preserve axes geometry. Automatic legends can move with the data. Longer labels, different ticks and other changes in space requirements can require layout adjustment.

Automatic positions can change with Matplotlib or Hedgehogs versions, fonts, backends, output formats or canvas dimensions. Assess those changes against readability, containment, preserved data and author settings. Use a named location or explicit anchor when a particular placement is required.

## User control

Figures and axes remain editable through Matplotlib arguments, `rcParams` and artist methods. Explicit fonts, strokes, marker sizes, locators and legend anchors retain author control, including options that equal the defaults. Proportional resizing may scale explicit sizes; it must avoid cumulative changes or caps. `reset_style()` restores Matplotlib defaults.

## Final document size

For exported width $W_{export}$ and insertion width $W_{print}$, text scales as:

$$
f_{print}=f_{export}\frac{W_{print}}{W_{export}}.
$$

Inspect the figure at its intended physical width and follow the target journal's requirements. Split crowded figures or use a wider placement when text becomes too small. DPI controls raster resolution; it cannot compensate for reduced physical text size.

## Verification

Check dimensions, readability, containment, explicit overrides and repeated output using both the configured serif font and DejaVu Serif. Test ordinary drawing separately from finishing and export. Compare figures at equal physical panel sizes. See [Validation rules](../../tests/README.md) for test selection.
