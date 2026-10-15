import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pytest
import hedgehogs as hdg


@pytest.fixture(autouse=True)
def clean():
    hdg.set_style()
    yield
    plt.close('all')
    hdg.reset_style()


@pytest.mark.parametrize('size', [(7, 3), (3, 7), (4, 4)])
def test_square_fits_allocated_space_preserves_canvas_and_limits(size, tmp_path):
    fig, ax = plt.subplots(figsize=size)
    ax.plot([0, 10], [0, 1])
    ax.set(xlim=(-1, 11), ylim=(-.1, 1.1), xlabel='Long axis title', ylabel='Value')
    hdg.figures.square()
    fig.canvas.draw()
    allocated = ax.get_position(original=True)
    capacity = min(allocated.width * size[0], allocated.height * size[1])
    assert ax.bbox.width == pytest.approx(ax.bbox.height)
    assert ax.bbox.width / fig.dpi == pytest.approx(capacity)
    hdg.plots.show(block=False)
    assert ax.bbox.width == pytest.approx(ax.bbox.height)
    assert fig.get_size_inches() == pytest.approx(size)
    assert ax.get_xlim() == pytest.approx((-1, 11))
    assert ax.get_ylim() == pytest.approx((-.1, 1.1))
    fig.savefig(tmp_path / 'square.svg')
    fig.set_size_inches(size[::-1])
    hdg.plots.show(block=False)
    assert ax.bbox.width == pytest.approx(ax.bbox.height)
    hdg.figures.square(False)
    assert ax.get_box_aspect() is None


def test_grid_with_colourbar_and_constrained_layout(tmp_path):
    fig, axes = plt.subplots(1, 2, figsize=(8, 4), layout='constrained')
    image = axes[0].imshow(np.arange(12).reshape(3, 4), aspect='auto')
    fig.colorbar(image, ax=axes[0])
    axes[1].plot([0, 10], [0, 1])
    hdg.figures.square(ax=axes)
    hdg.plots.show(block=False)
    for ax in axes:
        assert ax.bbox.width == pytest.approx(ax.bbox.height)
    assert fig.axes[-1].get_box_aspect() != 1
    fig.savefig(tmp_path / 'grid.pdf')
    hdg.figures.square(False, ax=axes)
    assert all(ax.get_box_aspect() is None for ax in axes)


@pytest.mark.parametrize('extension', ['png', 'svg', 'pdf'])
def test_square_title_stays_inside_tight_export(extension, tmp_path):
    width, height = hdg.figsize(name='science', column='single')
    fig, ax = plt.subplots(figsize=(width * 1.5, height * 1.5))
    ax.scatter([8, 10, 12, 14], [4, 7, 10, 13], label='Red')
    ax.scatter([9, 11, 13, 15], [5, 6, 8, 9], label='White')
    ax.set(title='Wine Dataset: Original Features', xlabel='alcohol', ylabel='fixed acidity')
    ax.legend()
    fig.tight_layout()
    hdg.figures.square()
    cropped_bounds = []

    def inspect(event):
        if fig.transFigure._boxout is not fig.bbox:
            cropped_bounds.append((ax.title.get_window_extent(event.renderer).frozen(), fig.bbox.frozen()))

    fig.canvas.mpl_connect('draw_event', inspect)
    hdg.plots.save(tmp_path / f'wine.{extension}', dpi=300, transparent=True)
    assert cropped_bounds
    for title, canvas in cropped_bounds:
        assert title.x0 >= canvas.x0 - 1
        assert title.x1 <= canvas.x1 + 1
        assert title.y1 <= canvas.y1 + 1
    hdg.plots.show(block=False)
    assert ax.bbox.width == pytest.approx(ax.bbox.height)


def test_invalid_flag_does_not_create_axes():
    with pytest.raises(TypeError):hdg.figures.square('yes')
    assert not plt.get_fignums()


@pytest.mark.parametrize('scale', [1, 1.5])
def test_square_dependence_colourbar_matches_parent_after_finish_resize_export(scale, tmp_path):
    fig = plt.figure(figsize=(2.24 * scale, 2.2))
    values = np.array([[1, 2], [2, 3], [3, 4]])
    ax = hdg.plots.dependence_plot(0, values, [[10, 0], [20, 1], [30, 0]], color_by=1)
    hdg.figures.square()
    bar = fig.axes[1]
    hdg.plots.show(block=False)
    assert (bar.bbox.y0, bar.bbox.y1) == pytest.approx((ax.bbox.y0, ax.bbox.y1))
    for ext in ['png', 'pdf', 'svg']:
        fig.savefig(tmp_path / f'colourbar.{ext}', dpi=180)
    hdg.plots.show(block=False)
    assert (bar.bbox.y0, bar.bbox.y1) == pytest.approx((ax.bbox.y0, ax.bbox.y1))
    fig.set_size_inches(4, 3)
    hdg.plots.show(block=False)
    assert (bar.bbox.y0, bar.bbox.y1) == pytest.approx((ax.bbox.y0, ax.bbox.y1))


def test_explicit_shrink_and_custom_colourbar_axes_keep_native_locator():
    fig, ax = plt.subplots(figsize=(4, 3))
    image = ax.imshow(np.arange(9).reshape(3, 3))
    bar = fig.colorbar(image, ax=ax, shrink=.5)
    assert type(bar.ax.get_axes_locator()).__name__ == '_ColorbarAxesLocator'
    fig2, ax2 = plt.subplots(figsize=(4, 3))
    image2 = ax2.imshow(np.arange(9).reshape(3, 3))
    cax = fig2.add_axes([.85, .15, .03, .6])
    custom = fig2.colorbar(image2, cax=cax)
    assert type(custom.ax.get_axes_locator()).__name__ == '_ColorbarAxesLocator'


def test_colourbar_locator_stays_retired_after_reset_and_reenable():
    fig, ax = plt.subplots(figsize=(2.24, 2.2))
    ax.set_box_aspect(1)
    image = ax.scatter([0, 1], [0, 1], c=[0, 1])
    bar = fig.colorbar(image, ax=ax)
    locator = bar.ax.get_axes_locator()
    renderer = fig.canvas.get_renderer()
    hdg.reset_style()
    assert locator(bar.ax, renderer).bounds == pytest.approx(locator.original(bar.ax, renderer).bounds)
    hdg.set_style()
    assert locator(bar.ax, renderer).bounds == pytest.approx(locator.original(bar.ax, renderer).bounds)
