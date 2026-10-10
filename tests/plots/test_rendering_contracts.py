"""Hook ownership and geometry under equivalent presentation requirements."""
import io
from functools import wraps

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.legend import Legend

import hedgehogs as hdg
from hedgehogs.plots import rendering
from hedgehogs.plots.presentation import prepare


METHODS = [(Figure, name) for name in ('__init__', 'draw', 'tight_layout', 'savefig', 'colorbar')]
METHODS += [(Axes, name) for name in ('scatter', 'set_xlabel', 'set_ylabel', 'set_title',
                                    'set_xticklabels', 'set_yticklabels', 'bar_label',
                                    'legend', 'tick_params', 'plot', 'bar')]


@pytest.fixture(autouse=True)
def restore_methods():
    hdg.reset_style()
    original = {(owner, name): getattr(owner, name) for owner, name in METHODS}
    yield
    plt.close('all')
    hdg.reset_style()
    for (owner, name), method in original.items():
        setattr(owner, name, method)


@pytest.mark.parametrize('owner,name', METHODS)
def test_reset_preserves_later_third_party_replacement(owner, name):
    hdg.set_style()
    def replacement(*args, **kwargs):
        return None
    setattr(owner, name, replacement)
    hdg.reset_style()
    assert getattr(owner, name) is replacement


def test_retired_draw_hook_stays_inert_when_wrapped_and_reenabled():
    hdg.set_style()
    retired = Figure.draw
    @wraps(retired)
    def third_party(figure, renderer):
        return retired(figure, renderer)
    Figure.draw = third_party
    hdg.reset_style()
    hdg.set_style()
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    calls = []
    fig._hedgehogs_style.apply = lambda *args: calls.append(True)
    fig.canvas.draw()
    assert calls == [True]
    hdg.reset_style()
    assert Figure.draw is third_party


def test_retired_font_hook_does_not_mark_artists_after_reset():
    hdg.set_style()
    retired = Axes.set_xlabel
    @wraps(retired)
    def third_party(axes, *args, **kwargs):
        return retired(axes, *args, **kwargs)
    Axes.set_xlabel = third_party
    hdg.reset_style()
    fig, ax = plt.subplots()
    text = ax.set_xlabel('Native', fontsize=13)
    assert not getattr(text, '_hedgehogs_font_explicit', False)


def test_partial_legend_cache_setup_is_restored_on_failure(monkeypatch):
    fig, axes = plt.subplots(1, 2)
    legends = []
    for ax in axes:
        ax.plot([0, 1], [0, 1], label='Data')
        legends.append(ax.legend(loc='best'))
    original = Legend.__setattr__
    def set_attribute(legend, name, value):
        if legend is legends[1] and name == '_find_best_position':
            raise RuntimeError('cache installation failed')
        return original(legend, name, value)
    monkeypatch.setattr(Legend, '__setattr__', set_attribute)
    with pytest.raises(RuntimeError, match='cache installation failed'):
        with rendering._cached_legend_search(fig):
            pass
    assert '_find_best_position' not in legends[0].__dict__


@pytest.mark.parametrize('layout', [None, 'tight', 'constrained'])
@pytest.mark.parametrize('panels', [1, 2])
@pytest.mark.parametrize('font', ['Times New Roman', 'DejaVu Serif'])
def test_data_shapes_preserve_equivalent_axes_geometry(layout, panels, font):
    hdg.set_style()
    plt.rcParams['font.serif'] = [font]
    positions = []
    x = np.linspace(0, 1, 31)
    for shape in ('ascending', 'descending', 'oscillating'):
        y = {'ascending': x, 'descending': 1 - x, 'oscillating': .5 + .3 * np.sin(8 * np.pi * x)}[shape]
        size = hdg.figsize(column='double' if panels == 2 else 'single')
        fig, axes = plt.subplots(1, panels, figsize=size, layout=layout, squeeze=False)
        for ax in axes.flat:
            ax.scatter(x, y, label='Samples')
            ax.plot(x, y, label='Model')
            ax.set(xlim=(0, 1), ylim=(0, 1), xlabel='x', ylabel='Response', title='Case')
            ax.set_xticks([0, .5, 1])
            ax.set_yticks([0, .5, 1])
            ax.legend(loc='best')
        prepare(fig)
        bounds = np.array([ax.get_position().bounds for ax in axes.flat])
        fig.savefig(io.BytesIO(), format='svg', bbox_inches=None)
        prepare(fig)
        assert np.array([ax.get_position().bounds for ax in axes.flat]) == pytest.approx(bounds)
        positions.append(bounds)
        plt.close(fig)
    for bounds in positions[1:]:
        assert bounds == pytest.approx(positions[0], abs=1e-9)


@pytest.mark.parametrize('layout', [None, 'tight', 'constrained'])
@pytest.mark.parametrize('panels', [1, 2])
def test_data_edits_preserve_axes_geometry(layout, panels, tmp_path):
    hdg.set_style()
    fig, axes = plt.subplots(1, panels, figsize=hdg.figsize(column='double'), layout=layout, squeeze=False)
    x = np.linspace(0, 1, 31)
    artists = []
    for ax in axes.flat:
        points = ax.scatter(x, x, label='Samples')
        line, = ax.plot(x, x, label='Model')
        ax.set(xlim=(0, 1), ylim=(0, 1), xlabel='x', ylabel='Response', title='Case')
        ax.set_xticks([0, .5, 1])
        ax.set_yticks([0, .5, 1])
        ax.legend(loc='best')
        artists.append((points, line))
    prepare(fig)
    bounds = np.array([ax.get_position().bounds for ax in axes.flat])
    for y in (1 - x, .5 + .3 * np.sin(8 * np.pi * x)):
        for points, line in artists:
            points.set_offsets(np.column_stack((x, y)))
            line.set_ydata(y)
        hdg.plots.save(tmp_path / 'data-edit.svg', fig=fig, bbox_inches=None)
        assert np.array([ax.get_position().bounds for ax in axes.flat]) == pytest.approx(bounds, abs=1e-9)


def test_retained_legend_wrapper_does_not_cache_after_draw(monkeypatch):
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1], label='Data')
    legend = ax.legend(loc='best')
    renderer = fig.canvas.get_renderer()
    calls = []
    def native_search(legend, width, height, renderer):
        calls.append(True)
        return (len(calls), 0)
    monkeypatch.setattr(Legend, '_find_best_position', native_search)
    with rendering._cached_legend_search(fig):
        assert legend._find_best_position(10, 20, renderer) == (1, 0)
        assert legend._find_best_position(10, 20, renderer) == (1, 0)
        retired = legend._find_best_position
        def third_party(*args, **kwargs):
            return retired(*args, **kwargs)
        legend._find_best_position = third_party
    assert legend._find_best_position is third_party
    assert legend._find_best_position(10, 20, renderer) == (2, 0)
