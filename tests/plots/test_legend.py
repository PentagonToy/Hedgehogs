import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
from matplotlib.legend import Legend
import pytest

import hedgehogs as hdg


@pytest.fixture(autouse=True)
def clean_figures():
    yield
    plt.close('all')
    hdg.reset_style()


def test_inside_retains_matplotlib_location_and_collects_current_axes():
    _, ax = plt.subplots()
    ax.plot([0, 1], label='First')
    ax.scatter([0], [1], label='Second')
    result = hdg.plots.legend('upper left', 'inside', 2)
    assert ax.get_legend() is result
    assert result._loc == Legend.codes['upper left']
    assert result._bbox_to_anchor is None
    assert [text.get_text() for text in result.get_texts()] == ['First', 'Second']


@pytest.mark.parametrize('domain', ['inside', 'in', 'i', 'outside', 'out', 'o'])
def test_domain_aliases(domain):
    _, ax = plt.subplots()
    ax.plot([0, 1], label='Data')
    result = hdg.plots.legend('upper center', domain)
    assert ax.get_legend() is result
    if domain in ('inside', 'in', 'i'):
        assert result._bbox_to_anchor is None
        assert result._loc == Legend.codes['upper center']
    else:
        assert result._bbox_to_anchor is not None
        assert result._loc == Legend.codes['lower center']


@pytest.mark.parametrize('location,side', [('upper left', 'top'),
    ('upper center', 'top'), ('upper right', 'top'), ('lower left', 'bottom'),
    ('lower center', 'bottom'), ('lower right', 'bottom'),
    ('center left', 'left'), ('center right', 'right'), ('best', 'right')])
def test_outside_clears_axis_labels_and_titles(location, side):
    hdg.set_style()
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.plot([0, 1], label='Data')
    ax.set(xlabel='Horizontal label', ylabel='Vertical label', title='Title')
    result = hdg.plots.legend(location, 'outside')
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    content = ax.get_tightbbox(renderer, bbox_extra_artists=[])
    box = result.get_window_extent(renderer)
    if side == 'top':
        assert box.y0 > content.y1
    elif side == 'bottom':
        assert box.y1 < content.y0
    elif side == 'left':
        assert box.x1 < content.x0
    else:
        assert box.x0 > content.x1


def test_outside_survives_finishing_resize_and_explicit_anchor(tmp_path):
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.plot([0, 1], label='Data')
    ax.set_xlabel('Horizontal label')
    result = hdg.plots.legend('lower center', 'outside', 1)
    hdg.plots.save(tmp_path / 'legend.pdf', fig=fig)
    fig.set_size_inches(6, 5)
    ax.set_xlabel('Edited horizontal label', fontsize=18)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    assert result.get_window_extent(renderer).y1 < ax.xaxis.label.get_window_extent(renderer).y0
    result.set_bbox_to_anchor((.5, .5), ax.transAxes)
    expected = result.get_bbox_to_anchor().bounds
    fig.canvas.draw()
    assert result.get_bbox_to_anchor().bounds == expected


@pytest.mark.parametrize('kwargs', [{'domain': 'invalid'}, {'ncol': 0},
    {'ncol': True}, {'domain': 'outside', 'loc': 'center'}])
def test_invalid_options_do_not_create_figures(kwargs):
    with pytest.raises(ValueError):
        hdg.plots.legend(**kwargs)
    assert not plt.get_fignums()
