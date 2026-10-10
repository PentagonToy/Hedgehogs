"""Actual finishing and export across panels, colourbars and author choices."""
import numpy as np
import pytest
import matplotlib.pyplot as plt
import hedgehogs as hdg
from hedgehogs.plots import presentation
from tools.experiments.legend_grid import experimental_placement


@pytest.fixture(autouse=True)
def style():
    hdg.set_style()
    yield
    plt.close('all')
    hdg.reset_style()


@pytest.mark.parametrize('layout', [None, 'tight', 'constrained'])
@pytest.mark.parametrize('colourbar', [False, True])
@pytest.mark.parametrize('format', ['png', 'pdf', 'svg'])
def test_hybrid_panel_exports_preserve_geometry_and_data(tmp_path, layout, colourbar, format):
    data = np.random.default_rng(47).uniform(0, 1, (500, 2))
    figs = []
    positions = []
    for experimental in (False, True):
        fig, axes = plt.subplots(1, 2, figsize=hdg.figsize(column='double'), layout=layout)
        figs.append(fig)
        points = []
        for ax in axes:
            points.append(ax.scatter(*data.T, c=np.arange(len(data)) if colourbar else 'C0', label='Data'))
            ax.set(xlim=(0, 1), ylim=(0, 1), xlabel='x', ylabel='y')
            ax.set_xticks([0, .5, 1])
            ax.set_yticks([0, .5, 1])
            ax.legend(loc='best')
        if colourbar:
            fig.colorbar(points[0], ax=list(axes))
        if experimental:
            with experimental_placement():
                hdg.plots.save(tmp_path / ('hybrid.' + format), fig=fig, bbox_inches=None)
                first = np.array([axis.get_position().bounds for axis in fig.axes])
                presentation.prepare(fig)
                assert np.allclose(first, [axis.get_position().bounds for axis in fig.axes], atol=1e-9, rtol=0)
        else:
            hdg.plots.save(tmp_path / ('classic.' + format), fig=fig, bbox_inches=None)
        positions.append(np.array([axis.get_position().bounds for axis in fig.axes]))
        for artist in points:
            assert np.array_equal(artist.get_offsets(), data)
    assert np.allclose(positions[0], positions[1], atol=1e-9, rtol=0)


@pytest.mark.parametrize('location', ['upper right', 'lower left', 'center', (.15, .3)])
@pytest.mark.parametrize('external', [False, True])
def test_hybrid_preserves_explicit_author_location(location, external):
    fig, ax = plt.subplots()
    ax.scatter([0, 1], [0, 1], label='Data')
    legend = ax.legend(loc=location, bbox_to_anchor=(1.1, 1) if external else None, fontsize=12)
    original = legend._loc
    anchor = legend._bbox_to_anchor
    with experimental_placement():
        presentation.prepare(fig)
    assert legend._loc == original
    assert legend._bbox_to_anchor is anchor
    assert legend.get_texts()[0].get_fontsize() == 12
