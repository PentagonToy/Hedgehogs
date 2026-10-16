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


@pytest.mark.parametrize('layout', [None, 'constrained'])
def test_shared_outside_centres_on_panels_and_survives_export(layout, tmp_path):
    from matplotlib.transforms import Bbox
    from hedgehogs.plots.presentation import prepare
    hdg.set_style()
    fig, axes = plt.subplots(2, 2, figsize=(5, 5), sharex=True, sharey=True, layout=layout)
    for ax in axes.flat:
        ax.scatter([0, 1], [0, 1], color='blue', label='1')
        ax.scatter([.2, .8], [.8, .2], color='red', label='0')
    axes[0, 0].set_ylabel('Long left-hand label')
    hdg.plots.square()
    result = hdg.plots.legend('upper center', 'outside', 2, shared=True)
    assert result in fig.legends
    assert all(ax.get_legend() is None for ax in axes.flat)
    assert [text.get_text() for text in result.get_texts()] == ['1', '0']
    for size in [(5, 5), (6, 4)]:
        fig.set_size_inches(size)
        prepare(fig)
        renderer = fig.canvas.get_renderer()
        panels = Bbox.union([ax.bbox for ax in axes.flat])
        box = result.get_window_extent(renderer)
        assert (box.x0 + box.x1) / 2 == pytest.approx((panels.x0 + panels.x1) / 2)
        assert box.y0 > max(ax.get_tightbbox(renderer, bbox_extra_artists=[]).y1 for ax in axes.flat)
        assert box.y1 <= fig.bbox.y1 + 1
        handles = getattr(result, 'legend_handles', None)
        if handles is None:
            handles = result.legendHandles
        assert list(handles[0].get_linewidth()) == list(axes[0, 0].collections[0].get_linewidth())
        for ext in ['png', 'svg', 'pdf']:
            hdg.plots.save(tmp_path / f'shared.{ext}', fig=fig)
    replacement = hdg.plots.legend('lower center', 'outside', 2, shared=True)
    assert fig.legends == [replacement]


@pytest.mark.parametrize('domain', ['inside', 'outside'])
def test_shared_single_panel_and_best_location(domain):
    from hedgehogs.plots.presentation import prepare
    hdg.set_style()
    fig, ax = plt.subplots(figsize=(4, 3))
    ax.scatter([0, 1], [0, 1], label='Data')
    result = hdg.plots.legend(shared=True, domain=domain)
    prepare(fig)
    assert [text.get_text() for text in result.get_texts()] == ['Data']
    assert result.get_window_extent(fig.canvas.get_renderer()).width > 0


def test_shared_conflicting_styles_warn_and_keep_first():
    fig, axes = plt.subplots(1, 2)
    axes[0].scatter([0], [0], color='blue', label='Data')
    axes[1].scatter([0], [0], color='red', label='Data')
    with pytest.warns(UserWarning, match='different styles'):
        result = hdg.plots.legend(shared=True)
    assert len(result.get_texts()) == 1
    assert result._hedgehogs_sources == [axes[0].collections[0]]


def test_shared_rejects_non_boolean_before_creating_figures():
    with pytest.raises(TypeError, match='shared'):
        hdg.plots.legend(shared='yes')
    assert not plt.get_fignums()


def test_shared_frame_matches_panel_legend_and_retains_explicit_edits(tmp_path):
    from hedgehogs.plots.presentation import prepare
    hdg.set_style()
    fig, axes = plt.subplots(2, 2, figsize=(4.48, 4.4))
    for ax in axes.flat:
        ax.scatter([0, 1], [0, 1], label='Data')
    local = axes[0, 0].legend(loc='upper left')
    shared = hdg.plots.legend('upper center', 'outside', shared=True)
    prepare(fig)
    expected = local.get_frame().get_linewidth()
    assert expected > plt.rcParams['patch.linewidth']
    assert shared.get_frame().get_linewidth() == pytest.approx(expected)
    hdg.plots.save(tmp_path / 'frame.png', fig=fig)
    prepare(fig)
    assert shared.get_frame().get_linewidth() == pytest.approx(expected)
    shared.get_frame().set_linewidth(2.7)
    prepare(fig)
    assert shared.get_frame().get_linewidth() == pytest.approx(2.7)


def test_shared_single_panel_typography_matches_local_legend():
    from hedgehogs.plots.presentation import prepare
    hdg.set_style()
    fonts = []
    for shared in [False, True]:
        fig, ax = plt.subplots(figsize=(5, 4))
        ax.scatter([0, 1], [0, 1], label='Data')
        result = hdg.plots.legend('upper left', shared=shared)
        prepare(fig)
        fonts.append(result.get_texts()[0].get_fontsize())
    assert fonts[0] == pytest.approx(fonts[1])


def test_shared_excludes_hidden_panels_and_colourbars_and_preserves_anchor():
    fig, axes = plt.subplots(1, 2)
    image = axes[0].scatter([0, 1], [0, 1], c=[0, 1], label='Data')
    fig.colorbar(image, ax=axes[0])
    axes[1].plot([0, 1], label='Hidden')
    axes[1].set_visible(False)
    result = hdg.plots.legend('upper center', 'outside', shared=True)
    assert [text.get_text() for text in result.get_texts()] == ['Data']
    result.set_bbox_to_anchor((.5, .8), fig.transFigure)
    before = result.get_bbox_to_anchor().bounds
    fig.canvas.draw()
    assert result.get_bbox_to_anchor().bounds == before


@pytest.mark.parametrize('ncol', [1, 2, 3])
@pytest.mark.parametrize('shared', [False, True])
@pytest.mark.parametrize('domain', ['inside', 'outside'])
def test_titles_are_centred_for_any_column_count(ncol, shared, domain):
    from hedgehogs.plots.presentation import prepare
    hdg.set_style()
    fig, ax = plt.subplots(figsize=(5, 4))
    for index, name in enumerate(['One', 'A longer label', 'Three']):
        ax.scatter([index], [index], label=name)
    result = hdg.plots.legend('upper center', domain, ncol, shared=shared, title='Logic gate output')
    for size in [(5, 4), (6, 4)]:
        fig.set_size_inches(size)
        prepare(fig)
        renderer = fig.canvas.get_renderer()
        title = result.get_title().get_window_extent(renderer)
        frame = result.get_window_extent(renderer)
        assert (title.x0 + title.x1) / 2 == pytest.approx((frame.x0 + frame.x1) / 2, abs=.5)
        ratio = plt.rcParams['font.size'] / plt.rcParams['legend.fontsize']
        assert result.get_title().get_fontsize() == pytest.approx(result.get_texts()[0].get_fontsize() * ratio)


def test_multiline_title_stays_centred_through_exports(tmp_path):
    from hedgehogs.plots.presentation import prepare
    hdg.set_style()
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.scatter([0, 1], [0, 1], label='Data')
    result = hdg.plots.legend('upper center', 'outside', shared=True, title='Gate\noutput')
    for ext in ['png', 'pdf', 'svg']:
        hdg.plots.save(tmp_path / f'title.{ext}', fig=fig, transparent=True)
    prepare(fig)
    renderer = fig.canvas.get_renderer()
    title = result.get_title().get_window_extent(renderer)
    frame = result.get_window_extent(renderer)
    assert (title.x0 + title.x1) / 2 == pytest.approx((frame.x0 + frame.x1) / 2, abs=.5)


def test_invalid_title_does_not_create_figures():
    with pytest.raises(TypeError, match='title'):
        hdg.plots.legend(title=42)
    assert not plt.get_fignums()
