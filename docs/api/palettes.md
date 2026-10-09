# Palette API

Examples assume `import hedgehogs as hdg`.

## API index

| API | Purpose | Returns |
| --- | --- | --- |
| `hdg.Palette(...)` | Hold named, ordered colours | `Palette` |
| `hdg.get_palette(...)` | Select a registered palette | `Palette` |
| `hdg.build_color_map(...)` | Assign colours to labels | `dict` |
| `hdg.build_style_map(...)` | Assign colour, marker and line styles | `dict` |
| `hdg.register_palette(...)` | Register validated colours | `Palette` |
| `hdg.save_palette(...)` | Write a palette to JSON | `Path` |
| `hdg.load_palette(...)` | Read and register JSON colours | `Palette` |

## Built-in palettes

Hedgehogs provides six categorical palettes; Okabe–Ito is the default. Swatches follow the exact package order, from left to right. The summary lists HEX values in the same order; indices start at zero.

| Palette | Colours | Preview | HEX values in index order |
| --- | ---: | --- | --- |
| `okabe-ito` | 8 | ![okabe-ito colours in index order](../../others/palettes/okabe-ito.svg) | `#0072B2` `#E69F00` `#D55E00`<br>`#009E73` `#56B4E9` `#F0E442`<br>`#CC79A7` `#000000` |
| `tableau10` | 10 | ![tableau10 colours in index order](../../others/palettes/tableau10.svg) | `#4E79A7` `#F28E2B` `#E15759`<br>`#76B7B2` `#59A14F` `#EDC948`<br>`#B07AA1` `#FF9DA7` `#9C755F`<br>`#BAB0AC` |
| `paul-tol-vibrant` | 7 | ![paul-tol-vibrant colours in index order](../../others/palettes/paul-tol-vibrant.svg) | `#0077BB` `#33BBEE` `#009988`<br>`#EE7733` `#CC3311` `#EE3377`<br>`#BBBBBB` |
| `paul-tol-bright` | 7 | ![paul-tol-bright colours in index order](../../others/palettes/paul-tol-bright.svg) | `#4477AA` `#EE6677` `#228833`<br>`#CCBB44` `#66CCEE` `#AA3377`<br>`#BBBBBB` |
| `paul-tol-muted` | 9 | ![paul-tol-muted colours in index order](../../others/palettes/paul-tol-muted.svg) | `#332288` `#88CCEE` `#44AA99`<br>`#117733` `#999933` `#DDCC77`<br>`#CC6677` `#882255` `#AA4499` |
| `ibm` | 5 | ![ibm colours in index order](../../others/palettes/ibm.svg) | `#648FFF` `#785EF0` `#DC267F`<br>`#FE6100` `#FFB000` |

Colour names belong to each palette; the same name can have different HEX values across palettes. These are discrete series colours. Select a Matplotlib colormap separately for continuous fields. Combine colours with markers or line styles for greyscale reproduction.

## Select colours

```python
palette = hdg.get_palette("okabe-ito")
ax.scatter(x, y, color=palette["blue"])
ax.plot(x, prediction, color=palette[1])
```

`Palette` supports colour names, integer indices and slices. Integer indices cycle through the available colours; slices return colour lists. Available names depend on the selected palette. `len(palette)` reports the colour count; `keys()`, `values()` and `items()` expose names, colours and name–colour pairs. Built-in colour-name lookup ignores case. An unknown colour name raises `KeyError`.

Apply a palette to the global figure style with `hdg.set_style(palette="okabe-ito")`. For a pairplot, `hdg.plots.pairplot(data, hue="species", palette="tableau10")` selects its palette explicitly.

For the default palette, `palette[0]` and `palette["blue"]` both return `"#0072B2"`; `palette[8]` repeats the first colour. `palette[:3]` returns a list of the first three colours, while `hdg.get_palette("okabe-ito", n=3)` returns a three-colour `Palette`.

## Assign series styles

```python
styles = hdg.build_style_map(["baseline", "model"])
ax.plot(x, baseline, label="Baseline", **styles["baseline"])
ax.plot(x, prediction, label="Model", **styles["model"])
```

`build_color_map()` assigns colours alone. `build_style_map()` combines colours, markers and line styles for Matplotlib lines. Both functions retain the first occurrence of each label. Their `palette` argument defaults to Okabe–Ito independently of the active figure style; pass it explicitly for another palette. Colours repeat when labels outnumber colours. Line styles cycle through `-`, `--`, `-.` and `:`; markers cycle through `o`, `s`, `^`, `D`, `v`, `P` and `X`. These cycles can eventually repeat complete style combinations.

## Register and save

```python
hdg.register_palette("models", {"baseline": "#0072B2", "model": "#D55E00"})
hdg.save_palette("models", "models.json")
hdg.load_palette("models.json", name="imported-models")
```

Registration lasts for the current Python process; JSON transfers palettes between sessions. See [Custom palettes](#custom-palettes) for validation and file naming.

## Palette objects

### `Palette`

```python
hdg.Palette(names, colors)
```

`names` and `colors` are ordered iterables. See [Select colours](#select-colours) for access and iteration. Use `register_palette()` to construct validated custom palettes.

### `get_palette`

Read a registered palette or select colours from an existing `Palette`.

```python
hdg.get_palette(palette="okabe-ito", n=None) -> Palette
```

Returns a `Palette`; see [Built-in palettes](#built-in-palettes) for names and colour order.

| Parameter | Default | Meaning |
| --- | --- | --- |
| `palette` | `"okabe-ito"` | Registered name or `Palette` object |
| `n` | `None` | Positive integer limiting the number of colours; `None` retains all colours |

An invalid `n` raises `ValueError`. A limit larger than the palette returns all available colours. Palette names ignore case and accept partial family names such as `tol` or `tableau`; an unrecognised name emits `UserWarning` and falls back to Okabe–Ito. Prefer the exact names in the tables for reproducible selection.

## Series mapping

### `build_color_map` and `build_style_map`

Assign colours or combined visual styles to unique labels.

```python
hdg.build_color_map(labels, palette="okabe-ito") -> dict[object, str]
hdg.build_style_map(labels, palette="okabe-ito") -> dict[object, dict[str, str]]
```

`labels` contains hashable labels; `palette` accepts a registered name or `Palette`. `build_style_map()` returns keyword dictionaries for `Axes.plot()`. See [Assign series styles](#assign-series-styles) for ordering and cycles.

## Custom palettes

Register palettes for the current process or transfer them through JSON.

```python
hdg.register_palette(name, colors, names=None, *, overwrite=False) -> Palette
hdg.save_palette(name, path) -> Path
hdg.load_palette(path, *, name=None, overwrite=False) -> Palette
```

`colors` accepts an ordered mapping of names to Matplotlib colours, or an iterable with optional `names`. Omit `names` for mappings; unnamed iterables receive `color-1`, `color-2`, and so on. Prefer lowercase names because lookup lowercases its input. Empty palettes, invalid colours, duplicate names and mismatched lengths raise `ValueError`. Replacing a registration requires `overwrite=True`.

`save_palette()` writes `name`, `names` and `colors` to JSON and returns its path. `load_palette()` registers the file and returns a `Palette`; its name comes from an explicit `name`, the JSON name or the file stem, in that order.

See the [figure guide](figures.md) for styling and export.
