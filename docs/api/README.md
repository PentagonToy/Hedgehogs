# Python API reference

Hedgehogs configures scientific figures and presents results in notebooks and terminals. Examples use `import hedgehogs as hdg`; Matplotlib retains ownership of figures and artists.

## Public namespace

Configure shared defaults with `set_style()` and `figsize()`. Draw, adjust, display and save individual figures through `plots`. Align separate comparison figures with `figures.align(figures=[...])`.

| Group | Public names | Purpose |
| --- | --- | --- |
| Figure settings | `set_style`, `reset_style`, `figsize`, `figures.align` | Configure style and read canvas dimensions |
| Figure helpers | `plots.label`, `plots.square`, `plots.annotate_panels`, `plots.style_colorbar`, `plots.apply_grid`, `plots.enable_minor_ticks` | Label and adjust existing axes and panels |
| General plots | `plots.tree`, `plots.pairplot`, `plots.decision_regions`, `plots.legend`, `plots.show`, `plots.save` | Draw, finish and save figures |
| SHAP visualisation | `plots.force_plot`, `plots.summary_plot`, `plots.waterfall_plot`, `plots.dependence_plot`, `plots.decision_plot` | Draw supplied feature attributions |
| Palettes | `Palette`, `get_palette`, `build_color_map`, `build_style_map`, `register_palette`, `save_palette`, `load_palette` | Select and map colours |
| Tables | `Table` | Format, display and export rows |
| Terminal output | `Progress`, `echo`, `rule`, `info` | Report activity and inspect package versions |
| Numerical support | `EPS` | Read floating-point machine epsilon |

## Reference map

| Task | Reference | Main API |
| --- | --- | --- |
| Configure figure defaults | [Figures](figures.md) | `set_style`, `reset_style`, `figsize`, `figures.align` |
| Draw, label and output plots | [Plots](plots.md) | `plots.label`, `plots.square`, `plots.legend`, `plots.show`, `plots.save` |
| Draw or finish SHAP explanations | [SHAP visualisation](shap.md) | `plots.force_plot`, `plots.summary_plot`, `plots.waterfall_plot`, `plots.dependence_plot`, `plots.decision_plot` |
| Select colours or define series styles | [Palettes](palettes.md) | `get_palette`, `build_style_map`, `register_palette` |
| Format and export results | [Tables](tables.md) | `Table` |
| Report progress and status | [Terminal output](terminal.md) | `Progress`, `echo`, `rule` |

## Reference conventions

API indices summarise purpose and return values. Signatures show keyword-only options after `*`; parameter tables describe defaults and constraints. `None` requests the documented inference or disables an optional behaviour. Paths accept `str` and `os.PathLike`.

Figures remain editable. `set_style()` affects Matplotlib until `reset_style()` restores it. `EPS` equals `sys.float_info.epsilon`.

Read the [documentation roadmap](../README.md) for guides and tutorials, and [implementation ownership](../developer/architecture.md) for lifecycle and extension rules.

The former `hdg.figures` helper paths remain available for existing notebooks; new code uses `hdg.plots` for those helpers. Cross-figure alignment uses `hdg.figures.align`.
