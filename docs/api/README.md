# Python API reference

Hedgehogs configures scientific figures and presents results in notebooks and terminals. Examples use `import hedgehogs as hdg`; Matplotlib retains ownership of figures and artists.

## Public namespace

| Group | Public names | Purpose |
| --- | --- | --- |
| Figure settings | `set_style`, `reset_style`, `figsize` | Configure style and read canvas dimensions |
| Figure helpers | `figures.annotate_panels`, `figures.style_colorbar`, `figures.apply_grid`, `figures.enable_minor_ticks` | Explicitly adjust existing axes and panels |
| Specialised plots | `plots.tree`, `plots.pairplot`, `plots.show`, `plots.save` | Draw, finish and save figures |
| Palettes | `Palette`, `get_palette`, `build_color_map`, `build_style_map`, `register_palette`, `save_palette`, `load_palette` | Select and map colours |
| Tables | `Table` | Format, display and export rows |
| Terminal output | `Progress`, `echo`, `rule`, `info` | Report activity and inspect package versions |
| Numerical support | `EPS` | Read floating-point machine epsilon |

## Reference map

| Task | Reference | Main API |
| --- | --- | --- |
| Style and size figures | [Figures](figures.md) | `set_style`, `figsize`, `figures.*` |
| Draw, finish and save plots | [Plots](plots.md) | `plots.tree`, `plots.pairplot`, `plots.show`, `plots.save` |
| Select colours or define series styles | [Palettes](palettes.md) | `get_palette`, `build_style_map`, `register_palette` |
| Format and export results | [Tables](tables.md) | `Table` |
| Report progress and status | [Terminal output](terminal.md) | `Progress`, `echo`, `rule` |

## Reference conventions

API indices summarise purpose and return values. Signatures show keyword-only options after `*`; parameter tables describe defaults and constraints. `None` requests the documented inference or disables an optional behaviour. Paths accept `str` and `os.PathLike`.

Figures and artists remain editable. `Table` and `Progress` update their state in place. Figure style affects global Matplotlib settings until `reset_style()` restores them. `EPS` equals `sys.float_info.epsilon`; it supplies a floating-point constant rather than a universal numerical tolerance.

Read the [documentation roadmap](../README.md) for guides and tutorials, and [implementation ownership](../developer/architecture.md) for lifecycle and extension rules.
