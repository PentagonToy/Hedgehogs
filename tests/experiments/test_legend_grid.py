"""Small correctness checks; benchmark generation remains an explicit script."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.transforms import Bbox

import hedgehogs as hdg
from hedgehogs.plots import presentation
from tools.experiments import legend_grid


@pytest.fixture(autouse=True)
def style():
    hdg.set_style()
    yield
    plt.close('all')
    hdg.reset_style()


def test_integer_window_sums():
    assert np.array_equal(legend_grid.windows(np.arange(12).reshape(3, 4), 2, 2),
                          [[10, 14, 18], [26, 30, 34]])


def test_fast_bins_match_histogram_including_upper_edges():
    points = np.vstack((np.random.default_rng(42).uniform(-.2, 1.2, (1000, 2)),
                        [[0, 0], [1, 1], [.5, .5], [np.nan, 0]]))
    bounds = Bbox.from_bounds(0, 0, 1, 1)
    finite = points[np.isfinite(points).all(axis=1)]
    edges = np.linspace(0, 1, 17)
    expected = np.histogram2d(finite[:, 1], finite[:, 0], bins=[edges, edges])[0]
    assert np.array_equal(legend_grid.bin_points(points, bounds, 16), expected)


def test_explicit_location_is_untouched():
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1], label='Data')
    legend = ax.legend(loc='lower right')
    legend_grid.place(fig, ax, fig.canvas.get_renderer())
    assert legend._loc == 4


def test_unsupported_artist_uses_existing_placement():
    fig, ax = plt.subplots()
    ax.bar([0, 1], [1, 2], label='Data')
    legend = ax.legend(loc='best')
    legend_grid.place(fig, ax, fig.canvas.get_renderer())
    assert isinstance(legend._loc, int) and legend._loc != 0


def test_context_restores_policy_after_failure():
    original = presentation._place_legend
    with pytest.raises(RuntimeError):
        with legend_grid.experimental_placement():
            assert presentation._place_legend is legend_grid.hybrid
            raise RuntimeError('example failure')
    assert presentation._place_legend is original


def test_experimental_finishing_preserves_data_and_repeat_geometry():
    fig, ax = plt.subplots()
    data = np.random.default_rng(5).uniform(0, 1, (100, 2))
    scatter = ax.scatter(*data.T, label='Samples')
    ax.set(xlim=(0, 1), ylim=(0, 1))
    legend = ax.legend(loc='best')
    with legend_grid.experimental_placement():
        presentation.prepare(fig)
        bounds = ax.get_position().bounds
        location = legend._loc
        presentation.prepare(fig)
        assert ax.get_position().bounds == pytest.approx(bounds)
        assert legend._loc == location
        changed = 1 - data
        scatter.set_offsets(changed)
        presentation.prepare(fig)
        assert ax.get_position().bounds == pytest.approx(bounds)
        assert np.array_equal(scatter.get_offsets(), changed)
    assert legend._loc != 0


def test_hybrid_zero_overlap_skips_grid(monkeypatch):
    fig, ax = plt.subplots()
    ax.plot([0, .1], [0, .1], label='Data')
    ax.set(xlim=(0, 1), ylim=(0, 1))
    legend = ax.legend(loc='best')
    def unexpected(*args, **kwargs):
        raise AssertionError('grid should not run')
    monkeypatch.setattr(legend_grid, 'propose', unexpected)
    legend_grid.hybrid(fig, ax, fig.canvas.get_renderer())
    assert legend._loc == 1


@pytest.mark.parametrize('proposal_cost', [1, 2])
def test_hybrid_keeps_classic_on_equal_or_worse_audit(monkeypatch, proposal_cost):
    fig, ax = plt.subplots()
    ax.scatter([.5], [.5], label='Data')
    ax.set(xlim=(0, 1), ylim=(0, 1))
    legend = ax.legend(loc='best')
    def overlap(ax, box, renderer, offsets=None):
        return presentation._area(box) * (proposal_cost if isinstance(legend._loc, tuple) else 1)
    monkeypatch.setattr(presentation, '_data_overlap', overlap)
    monkeypatch.setattr(legend_grid, 'propose', lambda *args, **kwargs: (.4, .4))
    legend_grid.hybrid(fig, ax, fig.canvas.get_renderer())
    assert legend._loc == 1


def test_policy_switch_revisits_already_finished_figure():
    fig, ax = plt.subplots(figsize=(4.76, 3.4))
    points = np.random.default_rng(17).uniform(0, 1, (6000, 2))
    keep = ~((points[:, 0] > .12) & (points[:, 0] < .67) & (points[:, 1] > .19) & (points[:, 1] < .48))
    ax.scatter(*points[keep].T, s=4, label='Samples')
    ax.set(xlim=(0, 1), ylim=(0, 1))
    legend = ax.legend(loc='best')
    presentation.prepare(fig)
    original = legend._loc
    bounds = ax.get_position().bounds
    with legend_grid.experimental_placement():
        presentation.prepare(fig)
        assert isinstance(legend._loc, tuple)
        assert ax.get_position().bounds == pytest.approx(bounds)
    presentation.prepare(fig)
    assert legend._loc == original
    assert ax.get_position().bounds == pytest.approx(bounds)


@pytest.mark.parametrize('proposal_cost,accepted', [(.99, False), (.91, False), (.9, True), (.89, True), (0., True)])
def test_hybrid_requires_meaningful_data_improvement(monkeypatch, proposal_cost, accepted):
    fig, ax = plt.subplots()
    ax.scatter([.5], [.5], label='Data')
    ax.set(xlim=(0, 1), ylim=(0, 1))
    legend = ax.legend(loc='best')
    def overlap(ax, box, renderer, offsets=None):
        return presentation._area(box) * (proposal_cost if isinstance(legend._loc, tuple) else 1)
    monkeypatch.setattr(presentation, '_data_overlap', overlap)
    monkeypatch.setattr(legend_grid, 'propose', lambda *args, **kwargs: (.4, .4))
    legend_grid.hybrid(fig, ax, fig.canvas.get_renderer())
    assert isinstance(legend._loc, tuple) == accepted
