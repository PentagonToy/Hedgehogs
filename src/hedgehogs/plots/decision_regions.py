"""Two-feature classification regions on editable Matplotlib axes."""

from collections.abc import Mapping, Sequence
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.markers import MarkerStyle
import numpy as np

from ..core.palette import Palette, get_palette
from . import style


def _array(value: Any, *, numeric: bool = False) -> np.ndarray:
    if isinstance(value, Mapping):
        value = np.column_stack(list(value.values()))
    elif callable(getattr(value, 'to_numpy', None)):
        value = value.to_numpy()
    try:
        return np.asarray(value, dtype=float if numeric else object)
    except (TypeError, ValueError) as error:
        raise ValueError('Inputs must contain rectangular arrays of valid values.') from error


def _labels(value: Any, name: str) -> list[Any]:
    array = _array(value)
    if array.ndim == 2 and array.shape[1] == 1:
        array = array[:, 0]
    if array.ndim != 1 or not array.size:
        raise ValueError(f'{name} must be a non-empty vector or one-column table.')
    labels = array.tolist()
    for label in labels:
        try:
            if label is None or bool(label != label):
                raise ValueError('Missing labels are not supported.')
            hash(label)
        except (TypeError, ValueError) as error:
            raise ValueError(f'{name} must contain non-missing, hashable class labels.') from error
    return labels


def decision_regions(
    X: Any,
    y: Any,
    classifier: Any,
    *,
    categories: Mapping[Any, str] | None = None,
    markers: Sequence[Any] | None = None,
    palette: str | Palette | None = None,
) -> Axes:
    """Draw classification regions and samples on the current pyplot axes.

    Accept arrays, lists, DataFrames or mappings of columns. X must contain
    exactly two finite numeric features; y supplies one label per row. The
    fitted classifier must provide predict(X). categories maps class labels to
    display names without changing predictions. Return editable Matplotlib axes;
    call plots.show() or plots.save() to finish the figure.
    """
    features = _array(X, numeric=True)
    if features.ndim != 2 or features.shape[1] != 2 or not len(features):
        raise ValueError('X must be a non-empty table with exactly two features.')
    if not np.isfinite(features).all():
        raise ValueError('X must contain finite numeric features.')
    labels = _labels(y, 'y')
    if len(labels) != len(features):
        raise ValueError('X and y must have the same number of rows.')
    if not callable(getattr(classifier, 'predict', None)):
        raise TypeError('classifier must provide a callable predict(X).')
    known = getattr(classifier, 'classes_', None)
    classes = list(dict.fromkeys(_labels(known, 'classifier.classes_') if known is not None else labels))
    indices = {label: index for index, label in enumerate(classes)}
    if categories is not None:
        if not isinstance(categories, Mapping):
            raise TypeError('categories must be a mapping of class labels to strings.')
        for label, name in categories.items():
            if label not in indices:
                raise ValueError(f'Unknown category label: {label!r}.')
            if not isinstance(name, str) or not name.strip():
                raise ValueError('Category names must be non-empty strings.')
    names = {label: categories.get(label, str(label)) if categories is not None else str(label)
             for label in classes}

    def encode(values: list[Any]) -> np.ndarray:
        try:
            return np.asarray([indices[label] for label in values], dtype=int)
        except KeyError as error:
            raise ValueError(f'Unknown class label: {error.args[0]!r}.') from error

    observed = encode(labels)
    symbols = list(markers) if markers is not None and not isinstance(markers, str) else (
        [markers] if markers is not None else ['s', 'P', 'o', '^', 'v'])
    if not symbols:
        raise ValueError('markers must contain at least one marker.')
    marker_styles = [MarkerStyle(marker) for marker in symbols]
    colours = get_palette(palette) if palette is not None else (
        style._active_palette if style._active_palette is not None else get_palette())
    colour_values = [colours[index % len(colours)] for index in range(len(classes))]

    lower, upper = features.min(axis=0), features.max(axis=0)
    padding = np.where(upper > lower, (upper - lower) * .05, .5)
    lower, upper = lower - padding, upper + padding
    source_columns = getattr(X, 'columns', None)
    columns = list(source_columns) if source_columns is not None else []
    frame_type = type(X) if columns and getattr(classifier, 'feature_names_in_', None) is not None else None

    def predict(bounds):
        xx, yy = np.meshgrid(np.linspace(bounds[0], bounds[1], 200),
                             np.linspace(bounds[2], bounds[3], 200))
        grid = np.column_stack((xx.ravel(), yy.ravel()))
        prediction_input = frame_type({name: grid[:, index] for index, name in enumerate(columns)}) if frame_type else grid
        predicted = _labels(classifier.predict(prediction_input), 'predictions')
        if len(predicted) != len(grid):
            raise ValueError('predict(X) must return one class label per grid point.')
        return xx, yy, encode(predicted).reshape(xx.shape)

    bounds = (lower[0], upper[0], lower[1], upper[1])
    prediction = predict(bounds)
    levels = np.arange(len(classes) + 1) - .5
    cmap = ListedColormap(colour_values)

    axes = plt.gca()

    def draw_region(values):
        # The background must not participate in data autoscaling.
        data_limits = axes.dataLim.frozen()
        ignore_limits = axes.ignore_existing_data_limits
        auto_x, auto_y = axes.get_autoscalex_on(), axes.get_autoscaley_on()
        axes.set_autoscalex_on(False)
        axes.set_autoscaley_on(False)
        try:
            contour = axes.contourf(*values, levels=levels, cmap=cmap,
                                    norm=BoundaryNorm(levels, cmap.N), alpha=.25, zorder=0)
            artists = (contour,) if hasattr(contour, 'sticky_edges') else getattr(contour, 'collections')
            for artist in artists:
                artist.sticky_edges.x.clear()
                artist.sticky_edges.y.clear()
            return contour
        finally:
            axes.dataLim.set(data_limits)
            axes.ignore_existing_data_limits = ignore_limits
            axes.set_autoscalex_on(auto_x)
            axes.set_autoscaley_on(auto_y)

    contour = draw_region(prediction)
    updating = False

    def refresh(_axes):
        nonlocal contour, bounds, updating
        if updating:
            return
        updating = True
        try:
            current = (*axes.get_xlim(), *axes.get_ylim())
            if current == bounds:
                return
            replacement = draw_region(predict(current))
            remove = getattr(contour, 'remove', None)
            if remove is not None:
                remove()
            else:
                for artist in getattr(contour, 'collections'):
                    artist.remove()
            contour = replacement
            bounds = current
        finally:
            updating = False

    axes.callbacks.connect('xlim_changed', refresh)
    axes.callbacks.connect('ylim_changed', refresh)
    for index, label in enumerate(classes):
        selected = observed == index
        if not selected.any():
            continue
        marker = marker_styles[index % len(marker_styles)]
        options: dict[str, Any] = {'edgecolors': 'black'} if marker.is_filled() else {}
        axes.scatter(features[selected, 0], features[selected, 1],
                     color=colour_values[index], marker=marker, alpha=.85,
                     s=plt.rcParams['lines.markersize'] ** 2, label=names[label], **options)
    if axes.get_autoscalex_on():
        axes.set_xlim(lower[0], upper[0], auto=None)
    if axes.get_autoscaley_on():
        axes.set_ylim(lower[1], upper[1], auto=None)
    refresh(axes)
    return axes
