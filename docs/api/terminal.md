# Terminal output API

Examples assume `import hedgehogs as hdg`.

## API index

| API | Purpose | Returns |
| --- | --- | --- |
| `hdg.Progress(...)` | Create manual or iterable progress | `Progress` |
| `progress.update(...)` | Advance completed work | `None` |
| `progress.set(...)` | Update reported metrics | `None` |
| `progress.set_description(...)` | Change the progress label | `None` |
| `progress.finish()` | Complete output | `None` |
| `progress.to_text()` | Render current progress as text | `str` |
| `progress.to_html()` | Render current progress as HTML | `str` |
| `hdg.echo(...)` | Write a status message | `None` |
| `hdg.rule(...)` | Write a separator | `None` |
| `hdg.info()` | Print package and Matplotlib versions | `str` |

## `Progress`

Report progress for manually advanced work or an iterable.

```python
hdg.Progress(iterable=None, total=None, desc="", width=40, mininterval=0.1, smoothing=0.3)
```

Invalid constructor values raise `ValueError`; `update()` after `finish()` raises `RuntimeError`.

Calls to `set()` update metrics immediately but remain subject to `mininterval`; the next eligible `set()` or `update()` refresh displays the latest values. `finish()` always preserves the final state.

| Parameter | Type | Default | Constraint or meaning |
| --- | --- | --- | --- |
| `iterable` | iterable or `None` | `None` | Source consumed by iteration |
| `total` | `int` or `None` | Inferred | Non-negative; required for sized progress when length cannot be inferred |
| `desc` | `str` | `""` | Prefix label |
| `width` | `int` | `40` | Positive terminal bar width |
| `mininterval` | `float` | `0.1` | Non-negative minimum refresh interval in seconds |
| `smoothing` | `float` | `0.3` | Rate smoothing from `0` to `1` |

## Terminal output

### `echo`

Write a status message with optional colour and emphasis.

```python
hdg.echo(message, *, tone=None, color=None, bold=False, file=None) -> None
```

Returns `None`. Explicit `color` overrides the colour selected by `tone`; unknown tones or invalid colours raise `ValueError`. `bold=False` disables emphasis, and `file=None` selects notebook HTML or standard output. An explicit `file` receives stream output. Redirected terminal output stays plain; `NO_COLOR` and `TERM=dumb` disable colour.

| Parameter | Default | Meaning |
| --- | --- | --- |
| `message` | Required | Text to write |
| `tone` | `None` | `info`, `success`, `warning`, `error`, or `muted` |
| `color` | `None` | Explicit Matplotlib colour; overrides `tone` |
| `bold` | `False` | Emphasise the message |
| `file` | `None` | Destination stream; `None` selects notebook output or standard output |

| Tone | Intended use |
| --- | --- |
| `info` | Neutral activity or context |
| `success` | Successful completion |
| `warning` | Recoverable concern or fallback |
| `error` | Failed operation |
| `muted` | Secondary information |

### `rule`

Write a horizontal separator with an optional title.

```python
hdg.rule(title="", *, width=None, file=None) -> None
```

| Parameter | Default | Meaning |
| --- | --- | --- |
| `title` | `""` | Centred title; an empty string produces a line alone |
| `width` | `None` | Terminal width; automatic detection falls back to 80 columns |
| `file` | `None` | Destination stream; `None` selects standard output |

Returns `None`.

## Progress updates

```python
progress.update(n=1)
progress.set_description(desc)
progress.set(**metrics)
progress.finish()
progress.to_text()
progress.to_html()
```

`update()` advances completed work by a finite, non-negative amount. `set_description()` changes the label; `set()` records named metrics for the next eligible refresh. These methods and `finish()` return `None`. `to_text()` and `to_html()` return strings without selecting an output destination. A context manager calls `finish()` on exit, including after an exception.

## Package information

```python
hdg.info()
```
`info()` prints the Hedgehogs and Matplotlib versions and returns the same text as a string.
