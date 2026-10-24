"""Projected 3D typography, canvas containment and explicit settings."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.ticker import FixedLocator

import hedgehogs as hdg
from hedgehogs.plots.presentation import prepare


@pytest.fixture(autouse=True)
def styled_figures():
    hdg.set_style()
    yield
    plt.close('all')
    hdg.reset_style()


@pytest.mark.parametrize('font_family', ['serif', 'DejaVu Serif'])
@pytest.mark.parametrize('azimuth', [-60, 35])
@pytest.mark.parametrize('scale', [1.5, 2])
def test_surface_labels_fit_and_exports_preserve_geometry(font_family, azimuth, scale, tmp_path):
    plt.rcParams['font.family'] = font_family
    fig = plt.figure(figsize=tuple(v * scale for v in hdg.figsize()))
    ax = fig.add_subplot(111, projection='3d')
    x, y = np.meshgrid(np.linspace(0, 1, 30), np.linspace(0, 1, 30))
    ax.plot_surface(x, y, np.sin(6*x)*np.cos(6*y), cmap='jet')
    ax.set(xlabel=r'$w_1$', ylabel=r'$w_2$', zlabel=r'$J(\mathbf{w})$',
           xlim=(0, 1), ylim=(0, 1), zlim=(-4, 4))
    ax.view_init(elev=25, azim=azimuth)
    ax.set_box_aspect((1, 1, .6))
    plt.tight_layout()
    prepare(fig)
    renderer = fig.canvas.get_renderer()
    tick_boxes = [text.get_window_extent(renderer) for axis in ax._axis_map.values()
                  for tick in axis.majorTicks[:len(axis.get_majorticklocs())] for text in (tick.label1,)
                  if text.get_visible() and text.get_text()]
    for axis in ax._axis_map.values():
        bounds = axis.label.get_window_extent(renderer)
        assert fig.bbox.contains(*bounds.get_points()[0])
        assert fig.bbox.contains(*bounds.get_points()[1])
        assert not any(bounds.overlaps(tick) for tick in tick_boxes)
    for i, box in enumerate(tick_boxes):
        assert not any(box.overlaps(other) for other in tick_boxes[i+1:])
    position = ax.get_position().bounds
    fonts = [axis.label.get_fontsize() for axis in ax._axis_map.values()]
    for extension in ('png', 'svg', 'pdf'):
        hdg.plots.save(tmp_path / ('landscape.' + extension), fig=fig,
                       dpi=300, bbox_inches='tight', transparent=True)
        prepare(fig)
        assert ax.get_position().bounds == pytest.approx(position, abs=1e-6)
        assert [axis.label.get_fontsize() for axis in ax._axis_map.values()] == pytest.approx(fonts)
    assert ax.get_box_aspect() / ax.get_box_aspect()[0] == pytest.approx([1, 1, .6])
    assert ax.get_zlim() == (-4, 4)


def test_3d_explicit_ticks_fonts_and_padding_remain_owned_by_user():
    fig = plt.figure(figsize=(5, 5))
    ax = fig.add_subplot(111, projection='3d')
    ax.plot([0, 1], [0, 1], [0, 1])
    locator = FixedLocator([0, .5, 1])
    ax.zaxis.set_major_locator(locator)
    ax.set_zlabel('Objective', fontsize=8, labelpad=24)
    ax.tick_params(axis='z', labelsize=7)
    prepare(fig)
    assert ax.zaxis.get_major_locator() is locator
    assert ax.zaxis.label.get_fontsize() == 8
    assert ax.zaxis.labelpad == 24
    assert ax.zaxis.get_major_ticks()[0].label1.get_fontsize() == 7
