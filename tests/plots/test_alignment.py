import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pytest
import hedgehogs as hdg


@pytest.fixture(autouse=True)
def cleanup():
    hdg.set_style()
    yield
    plt.close('all')
    hdg.reset_style()


def test_alignment_survives_finish_export_and_repeated_alignment(tmp_path):
    figures = []
    for top in (1., 3., 10000.):
        fig, ax = plt.subplots(figsize=hdg.figsize('science', 'single'))
        ax.plot([0, 1], [0, top])
        ax.set(xlabel='x', ylabel='Response', title='Basis')
        figures.append(fig)
    limits = [(f.axes[0].get_xlim(), f.axes[0].get_ylim()) for f in figures]
    hdg.figures.align(figures=figures)
    expected = figures[0].axes[0].get_position().bounds
    for i, fig in enumerate(figures):
        for extension in ('png', 'pdf', 'svg'):
            hdg.plots.save(tmp_path / f'{i}.{extension}', fig=fig, transparent=True)
        hdg.plots.show(fig, block=False)
        assert fig.axes[0].get_position().bounds == pytest.approx(expected)
        assert fig.axes[0].get_xlim() == pytest.approx(limits[i][0])
        assert fig.axes[0].get_ylim() == pytest.approx(limits[i][1])
    hdg.figures.align(figures)
    for fig in figures:
        assert fig.axes[0].get_position().bounds == pytest.approx(expected)
        bbox = fig.axes[0].get_tightbbox(fig.canvas.get_renderer())
        assert bbox.x0 >= 0 and bbox.y0 >= 0
        assert bbox.x1 <= fig.bbox.width and bbox.y1 <= fig.bbox.height


def test_invalid_inputs_do_not_change_valid_figure():
    fig, ax = plt.subplots()
    position = ax.get_position().bounds
    other, _ = plt.subplots(figsize=(8, 8))
    for values in ([fig], [fig, fig], [fig, other]):
        with pytest.raises(ValueError):
            hdg.figures.align(values)
    with pytest.raises(TypeError):
        hdg.figures.align([fig, ax])
    other.set_size_inches(fig.get_size_inches())
    hdg.plots.square(ax=other.axes[0])
    with pytest.raises(ValueError):
        hdg.figures.align([fig, other])
    assert ax.get_position().bounds == pytest.approx(position)


def test_constrained_layout_is_frozen_and_resize_releases_alignment():
    figures = []
    for value in (1., 3.):
        fig, ax = plt.subplots(figsize=(4, 3), layout='constrained')
        ax.plot([0, 1], [0, value])
        ax.set(xlabel='x', ylabel='response')
        figures.append(fig)
    hdg.figures.align(figures)
    expected = figures[0].axes[0].get_position().bounds
    for fig in figures:
        hdg.plots.show(fig, block=False)
        assert fig.axes[0].get_position().bounds == pytest.approx(expected)
    figures[0].set_size_inches(5, 4)
    hdg.plots.show(figures[0], block=False)
    assert not hasattr(figures[0], '_hedgehogs_aligned_layout')
