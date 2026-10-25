"""Readable automatic outside legends without altering plotting contracts."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pytest

import hedgehogs as hdg
from hedgehogs.plots.presentation import prepare


@pytest.fixture(autouse=True)
def styled_figures():
    hdg.set_style()
    yield
    plt.close('all')
    hdg.reset_style()


def comparison(font_family='serif'):
    plt.rcParams['font.family'] = font_family
    fig, ax = plt.subplots(figsize=tuple(v * 2 for v in hdg.figsize()))
    measured = np.linspace(105, 140, 50)
    for offset, name in [(2, 'Linear Regression'), (-1, 'DNN')]:
        ax.scatter(measured, measured + offset, s=14, alpha=.6, label=name)
    ax.plot([103, 142], [103, 142], '--', label='Ideal')
    ax.set(xlim=(103, 142), ylim=(103, 142), title='Airfoil Self-Noise Prediction',
           xlabel='Measured Sound Pressure Level (dB)',
           ylabel='Predicted Sound Pressure Level (dB)')
    hdg.plots.square(True)
    legend = hdg.plots.legend(domain='outside', loc='upper center', ncol=3)
    return fig, ax, legend


@pytest.mark.parametrize('font_family', ['serif', 'DejaVu Serif'])
def test_long_labels_and_square_fit_without_changing_data(font_family, tmp_path):
    fig, ax, legend = comparison(font_family)
    offsets = [item.get_offsets().copy() for item in ax.collections]
    line = ax.lines[0].get_xydata().copy()
    limits = (ax.get_xlim(), ax.get_ylim())
    prepare(fig)
    renderer = fig.canvas.get_renderer()
    panel = ax.get_window_extent(renderer)
    assert panel.width == pytest.approx(panel.height)
    assert panel.width * panel.height > fig.bbox.width * fig.bbox.height * .30
    boxes = [label.get_window_extent(renderer)
             for label in (ax.xaxis.label, ax.yaxis.label, ax.title)]
    boxes.append(legend.get_window_extent(renderer))
    for box in boxes:
        assert fig.bbox.contains(*box.get_points()[0])
        assert fig.bbox.contains(*box.get_points()[1])
    for i, box in enumerate(boxes):
        assert not any(box.overlaps(other) for other in boxes[i+1:])
    assert legend._ncols == 3
    assert [text.get_text() for text in legend.get_texts()] == ['Linear Regression', 'DNN', 'Ideal']
    position = ax.get_position().bounds
    sizes = [ax.xaxis.label.get_fontsize(), *[t.get_fontsize() for t in legend.get_texts()]]
    for extension in ('png', 'pdf', 'svg'):
        hdg.plots.save(tmp_path / ('comparison.' + extension), fig=fig,
                       dpi=300, bbox_inches='tight', transparent=True)
        prepare(fig)
        assert ax.get_position().bounds == pytest.approx(position, abs=1e-6)
        assert [ax.xaxis.label.get_fontsize(), *[t.get_fontsize() for t in legend.get_texts()]] == pytest.approx(sizes)
    assert (ax.get_xlim(), ax.get_ylim()) == limits
    for item, expected in zip(ax.collections, offsets):
        np.testing.assert_array_equal(item.get_offsets(), expected)
    np.testing.assert_array_equal(ax.lines[0].get_xydata(), line)


@pytest.mark.parametrize('font_family', ['serif', 'DejaVu Serif'])
@pytest.mark.parametrize('shared', [False, True])
@pytest.mark.parametrize('location', ['upper left', 'upper center', 'upper right',
                                      'lower left', 'lower center', 'lower right',
                                      'center left', 'center right'])
def test_default_outside_legend_fits_available_canvas(shared, location, font_family, tmp_path):
    plt.rcParams['font.family'] = font_family
    fig, ax = plt.subplots(figsize=(4.48, 4.4))
    for i in range(3):
        ax.plot([0, 1], [i, i+1], label=['Linear Regression', 'Neural Network', 'Ideal Prediction'][i])
    legend = hdg.plots.legend(domain='outside', loc=location,
                              ncol=3 if location.startswith(('upper', 'lower')) else 1, shared=shared)
    prepare(fig)
    bounds = legend.get_window_extent(fig.canvas.get_renderer())
    assert fig.bbox.contains(*bounds.get_points()[0])
    assert fig.bbox.contains(*bounds.get_points()[1])
    position = ax.get_position().bounds
    fonts = [text.get_fontsize() for text in legend.get_texts()]
    for extension in ('png', 'svg'):
        hdg.plots.save(tmp_path / ('outside.' + extension), fig=fig)
        prepare(fig)
        assert ax.get_position().bounds == pytest.approx(position, abs=1e-6)
        assert [text.get_fontsize() for text in legend.get_texts()] == pytest.approx(fonts)


def test_explicit_fonts_and_external_anchor_are_preserved():
    fig, ax, legend = comparison()
    ax.set_xlabel(ax.get_xlabel(), fontsize=8)
    ax.set_ylabel(ax.get_ylabel(), fontsize=9)
    for text in legend.get_texts():
        text.set_fontsize(8)
    legend.set_bbox_to_anchor((.5, .9), fig.transFigure)
    before = legend.get_bbox_to_anchor().bounds
    prepare(fig)
    assert ax.xaxis.label.get_fontsize() == 8
    assert ax.yaxis.label.get_fontsize() == 9
    assert [t.get_fontsize() for t in legend.get_texts()] == [8, 8, 8]
    assert legend.get_bbox_to_anchor().bounds == pytest.approx(before)


@pytest.mark.parametrize('font_family', ['serif', 'DejaVu Serif'])
def test_outside_data_edits_and_resize_remain_stable(font_family):
    fig, ax, legend = comparison(font_family)
    prepare(fig)
    position = ax.get_position().bounds
    sizes = [ax.xaxis.label.get_fontsize(), *[t.get_fontsize() for t in legend.get_texts()]]
    data = ax.collections[0].get_offsets().copy()
    data[:, 1] -= .5
    ax.collections[0].set_offsets(data)
    prepare(fig)
    assert ax.get_position().bounds == pytest.approx(position, abs=1e-6)
    assert [ax.xaxis.label.get_fontsize(), *[t.get_fontsize() for t in legend.get_texts()]] == pytest.approx(sizes)
    fig.set_size_inches(5.6, 5.5)
    prepare(fig)
    box = ax.get_window_extent(fig.canvas.get_renderer())
    assert box.width == pytest.approx(box.height)
    assert box.width * box.height > fig.bbox.width * fig.bbox.height * .30


@pytest.mark.parametrize('font_family', ['serif', 'DejaVu Serif'])
@pytest.mark.parametrize('size,labels,ncols,location,shared,square', [
    ((3.36, 3.3), ('Measured SPL (dB)', 'Predicted SPL (dB)'), 2, 'lower center', False, True),
    ((6.72, 4.4), ('Measured Sound Pressure Level (dB)', 'Predicted Sound Pressure Level (dB)'), 3, 'upper left', False, True),
    ((4.48, 5.5), ('Measured value', 'Predicted value'), 1, 'center right', False, False),
    ((6.72, 4.4), ('x', 'y'), 3, 'upper right', True, False),
    ((4.48, 4.4), ('Measured value', 'Predicted value'), 3, 'lower left', True, True),
])
def test_bounded_layout_combinations(font_family, size, labels, ncols, location, shared, square):
    plt.rcParams['font.family'] = font_family
    fig, ax = plt.subplots(figsize=size)
    x = np.linspace(0, 1, 30)
    for i, name in enumerate(['Linear Regression', 'DNN', 'Ideal']):
        ax.plot(x, x + i, label=name)
    ax.set(xlim=(0, 1), ylim=(-1, 4), xlabel=labels[0], ylabel=labels[1])
    hdg.plots.square(square)
    legend = hdg.plots.legend(domain='outside', loc=location, ncol=ncols, shared=shared)
    prepare(fig)
    renderer = fig.canvas.get_renderer()
    boxes = [artist.get_window_extent(renderer)
             for artist in (ax.xaxis.label, ax.yaxis.label, legend)]
    for box in boxes:
        assert fig.bbox.contains(*box.get_points()[0])
        assert fig.bbox.contains(*box.get_points()[1])
    assert not boxes[0].overlaps(boxes[2])
    assert not boxes[1].overlaps(boxes[2])
    assert legend._ncols == ncols
    if square:
        assert ax.bbox.width == pytest.approx(ax.bbox.height)
    for i, line in enumerate(ax.lines):
        np.testing.assert_array_equal(line.get_ydata(), x + i)


@pytest.mark.parametrize('horizontal', [False, True])
@pytest.mark.parametrize('negative', [False, True])
def test_bar_values_fit_inside_automatic_limits(horizontal, negative):
    fig, ax = plt.subplots(figsize=hdg.figsize(name='science', column='single'))
    values = np.array([2.8, 1.29]) * (-1 if negative else 1)
    bars = (ax.barh if horizontal else ax.bar)(['Linear', 'DNN'], values)
    labels = ax.bar_label(bars, fmt='%.2f')
    prepare(fig)
    renderer = fig.canvas.get_renderer()
    for label in labels:
        bounds = label.get_window_extent(renderer)
        assert bounds.x0 >= ax.bbox.x0
        assert bounds.x1 <= ax.bbox.x1
        assert bounds.y0 >= ax.bbox.y0
        assert bounds.y1 <= ax.bbox.y1
    limits = ax.get_xlim(), ax.get_ylim()
    prepare(fig)
    assert (ax.get_xlim(), ax.get_ylim()) == limits


def test_bar_values_preserve_explicit_limits():
    fig, ax = plt.subplots()
    bars = ax.bar(['A', 'B'], [2.8, 1.29])
    ax.bar_label(bars)
    ax.set_ylim(0, 3)
    prepare(fig)
    assert ax.get_ylim() == (0, 3)
