"""Panel selection, numbering, contrast and editable output."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pytest

import hedgehogs as hdg
from hedgehogs.plots.presentation import prepare


@pytest.fixture(autouse=True)
def clean():
    hdg.set_style()
    yield
    plt.close('all')
    hdg.reset_style()


def test_default_panel_selection_grid_numbering_and_update():
    fig, axes = plt.subplots(2, 2)
    image = axes[0, 0].imshow(np.ones((2, 2)))
    fig.colorbar(image, ax=axes[0, 0])
    labels = hdg.plots.label(['Data', 'AND', 'OR', 'NAND'])
    assert [item.get_text() for item in labels] == ['a) Data', 'b) AND', 'c) OR', 'd) NAND']
    assert [item.axes for item in labels] == list(axes.flat)
    updated = hdg.plots.label(['Data', 'AND', 'OR', 'NAND'], axes=axes, bullets='1', halo=False)
    assert updated == labels
    assert [item.get_text() for item in labels] == ['1) Data', '2) AND', '3) OR', '4) NAND']
    fig.canvas.draw()
    assert all(not item.get_path_effects() for item in labels)
    assert all(len(ax.texts) == 1 for ax in axes.flat)


@pytest.mark.parametrize('bullets,expected', [('a', 'a)'), ('alphabet', 'a)'),
    ('1', '1)'), ('n', '1)'), ('numbers', '1)'), (None, '')])
def test_bullet_modes_and_single_axes(bullets, expected):
    _, ax = plt.subplots()
    result = hdg.plots.label(axes=ax, bullets=bullets)
    assert result[0].get_text() == expected
    literal = hdg.plots.label('a) Data', axes=ax, bullets=None)
    assert literal[0].get_text() == 'a) Data'


@pytest.mark.parametrize('location', ['upper left', 'upper center', 'upper right',
    'center left', 'center', 'center right', 'lower left', 'lower center', 'lower right'])
def test_locations_stay_inside_panel(location):
    fig, ax = plt.subplots(figsize=(4, 4))
    text, = hdg.plots.label('Data', loc=location)
    prepare(fig)
    bounds = text.get_window_extent(fig.canvas.get_renderer())
    assert ax.bbox.contains(bounds.x0, bounds.y0)
    assert ax.bbox.contains(bounds.x1, bounds.y1)


@pytest.mark.parametrize('background,expected', [('white', 'black'), ('black', 'white')])
def test_halo_contrast_and_direct_colour_edits(background, expected):
    fig, ax = plt.subplots()
    ax.set_facecolor(background)
    text, = hdg.plots.label('Data')
    fig.canvas.draw()
    assert text.get_color() == expected
    assert text.get_path_effects()
    assert text.get_bbox_patch() is None
    text.set_color('red')
    fig.canvas.draw()
    assert text.get_color() == 'red'


@pytest.mark.parametrize('background', ['white', 'black'])
def test_transparent_export_preserves_displayed_contrast(background, tmp_path):
    fig, ax = plt.subplots()
    ax.set_facecolor(background)
    text, = hdg.plots.label('Data')
    prepare(fig)
    expected = text.get_color()
    colours = []
    fig.canvas.mpl_connect('draw_event', lambda event: colours.append(text.get_color()))
    for ext in ['png', 'svg', 'pdf']:
        hdg.plots.save(tmp_path / f'contrast.{ext}', transparent=True)
    assert colours and all(colour == expected for colour in colours)


def test_image_contrast_follows_background_changes():
    fig, ax = plt.subplots()
    image = ax.imshow(np.zeros((4, 4)), cmap='gray', vmin=0, vmax=1)
    text, = hdg.plots.label()
    fig.canvas.draw()
    assert text.get_color() == 'white'
    image.set_data(np.ones((4, 4)))
    fig.canvas.draw()
    assert text.get_color() == 'black'


@pytest.mark.parametrize('halo', [True, False])
@pytest.mark.parametrize('box', [True, False])
def test_halo_and_box_are_independent_and_can_be_removed(halo, box, tmp_path):
    fig, ax = plt.subplots()
    ax.set_facecolor('black')
    text, = hdg.plots.label('Data', halo=halo, box=box)
    fig.canvas.draw()
    assert bool(text.get_path_effects()) == halo
    patch = text.get_bbox_patch()
    assert (patch is not None) == box
    assert text.get_color() == ('black' if box else 'white')
    if box:
        assert patch.get_facecolor() == pytest.approx((1, 1, 1, .8))
        assert patch.get_linewidth() == 0
    for ext in ['png', 'svg', 'pdf']:
        hdg.plots.save(tmp_path / f'box.{ext}', transparent=True)
    assert bool(text.get_path_effects()) == halo
    assert (text.get_bbox_patch() is not None) == box
    updated = hdg.plots.label('Edited', halo=False, box=False)
    assert updated == [text]
    fig.canvas.draw()
    assert text.get_bbox_patch() is None
    assert not text.get_path_effects()


def test_nested_axes_explicit_style_and_export(tmp_path):
    fig, axes = plt.subplots(2, 2, figsize=(5, 5))
    original = axes[1, 0].text(.5, .5, 'Keep me')
    texts = hdg.plots.label(['A', 'B'], axes=[[axes[0, 0]], [axes[1, 1]]],
                           color='red', fontsize=14, loc='lower right')
    for ext in ['png', 'svg', 'pdf']:
        hdg.plots.save(tmp_path / f'labels.{ext}', dpi=180)
    prepare(fig)
    assert all(text.get_fontsize() == 14 and text.get_color() == 'red' for text in texts)
    assert original in axes[1, 0].texts
    assert not axes[0, 1].texts
    assert all(text.get_path_effects() for text in texts)


def test_labels_follow_finished_typography_without_cumulative_scaling():
    fig, ax = plt.subplots(figsize=(5, 4))
    text, = hdg.plots.label()
    ax.set_xlabel('x')
    prepare(fig)
    expected = text.get_fontsize()
    assert expected > plt.rcParams['font.size']
    prepare(fig)
    assert text.get_fontsize() == expected
    hdg.plots.label('Edited', halo=False)
    prepare(fig)
    assert len(ax.texts) == 1
    assert not text.get_path_effects()


@pytest.mark.parametrize('kwargs,error', [({'bullets': 'bad'}, ValueError),
    ({'loc': 'best'}, ValueError), ({'halo': 1}, TypeError), ({'box': 1}, TypeError),
    ({'fontsize': 0}, ValueError), ({'fontsize': float('nan')}, ValueError),
    ({'axes': 'bad'}, TypeError), ({'labels': ['A']}, ValueError)])
def test_invalid_options_do_not_create_figures(kwargs, error):
    with pytest.raises(error):
        hdg.plots.label(**kwargs)
    assert not plt.get_fignums()
