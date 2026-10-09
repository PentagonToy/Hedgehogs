"""Finishing, collision scoring, author control, and repeated output."""
import io

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pytest

import hedgehogs as hdg
from hedgehogs.plots.presentation import prepare, _bar_collisions, _data_overlap


@pytest.fixture(autouse=True)
def style():
    hdg.set_style()
    yield
    plt.close('all')
    hdg.reset_style()


def benchmark():
    fig, ax = plt.subplots(figsize=(7, 4.5))
    y = list(range(6))
    first = ax.barh([value - .175 for value in y], [.79, .04, .65, .11, .51, 1.16], .35, label='Polars')
    second = ax.barh([value + .175 for value in y], [16.03, .5, 9.48, 4.98, 11.91, 14.12], .35, label='Pandas')
    labels = [*ax.bar_label(first, fmt='%.2f', padding=3), *ax.bar_label(second, fmt='%.2f', padding=3)]
    ax.set_yticks(y, ['read csv', 'aggregations', 'window functions', 'inner join', 'left join', 'full join'])
    ax.invert_yaxis()
    ax.set(xlabel='Time [s]', title='Speed Comparison', xlim=(0, 16.03 * 1.18))
    ax.legend(loc='center right')
    fig.tight_layout()
    return fig, ax, labels


@pytest.mark.presentation_smoke
def test_show_finishes_before_display_and_preserves_data(monkeypatch):
    fig, ax, labels = benchmark()
    original_limits = ax.get_xlim(), ax.get_ylim()
    values = [patch.get_width() for patch in ax.patches]
    calls = []
    monkeypatch.setattr(plt, 'show', lambda **kwargs: calls.append(kwargs))
    hdg.plots.show(block=False)
    assert calls == [{'block': False}]
    assert 10.5 < ax.xaxis.label.get_fontsize() <= 14.175
    assert labels[0].get_fontsize() < ax.xaxis.label.get_fontsize()
    assert _bar_collisions(fig, fig._get_renderer()) == 0
    assert (ax.get_xlim(), ax.get_ylim()) == original_limits
    assert [patch.get_width() for patch in ax.patches] == values
    legend = ax.get_legend()
    assert _data_overlap(ax, legend.get_window_extent(fig._get_renderer()), fig._get_renderer()) == 0


def test_repeated_preparation_and_exports_do_not_drift(tmp_path):
    fig, ax, labels = benchmark()
    prepare(fig)
    initial = (ax.get_position().bounds, [label.get_position() for label in labels],
               [label.get_fontsize() for label in labels])
    for _ in range(3):
        prepare(fig)
        assert ax.get_position().bounds == pytest.approx(initial[0])
        assert [label.get_position() for label in labels] == initial[1]
        assert [label.get_fontsize() for label in labels] == initial[2]
    paths = hdg.plots.save(tmp_path / 'bars', fig=fig, formats=('png', 'pdf', 'svg'), bbox_inches=None)
    assert all(path.stat().st_size for path in paths)
    assert ax.get_position().bounds == pytest.approx(initial[0])


@pytest.mark.presentation_smoke
def test_explicit_fonts_markers_and_legend_anchor_are_preserved():
    fig, ax = plt.subplots(figsize=(6.72, 4.4))
    points = ax.scatter([0, 1], [0, 1], s=10000, linewidths=3, label='Points')
    text = ax.text(.5, .5, 'Explicit', fontsize=18)
    legend = ax.legend(fontsize=16, bbox_to_anchor=(1, 1), loc='upper right')
    prepare(fig)
    assert text.get_fontsize() == 18
    assert points.get_sizes() == pytest.approx([10000])
    assert points.get_linewidths() == pytest.approx([3])
    assert legend.get_texts()[0].get_fontsize() == 16
    text.set_fontsize(25)
    points.set_sizes([20000])
    prepare(fig)
    assert text.get_fontsize() == 25
    assert points.get_sizes() == pytest.approx([20000])


def test_finish_without_style_and_show_empty_does_not_create_figure(monkeypatch):
    hdg.reset_style()
    calls = []
    monkeypatch.setattr(plt, 'show', lambda **kwargs: calls.append(kwargs))
    hdg.plots.show()
    assert not plt.get_fignums()
    fig, ax = plt.subplots()
    ax.bar([0, 1], [1, 2], label='Data')
    ax.legend()
    prepare(fig)
    fig.savefig(io.BytesIO(), format='png')
    assert len(calls) == 1


def test_explicit_legend_location_stays_inside_even_with_occupied_data():
    from matplotlib.patches import Rectangle
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.add_patch(Rectangle((0, 0), 1, 1, label='Occupied'))
    ax.set(xlim=(0, 1), ylim=(0, 1))
    legend = ax.legend(loc='center')
    prepare(fig)
    assert legend._loc == 10
    assert legend._bbox_to_anchor is None


def test_edits_after_legacy_draw_are_preserved_when_finishing():
    fig, ax = plt.subplots(figsize=(7, 4.5))
    points = ax.scatter([0, 1], [0, 1])
    text = ax.text(.5, .5, 'Edited')
    fig.canvas.draw()
    text.set_fontsize(23)
    points.set_sizes([20000])
    ax.tick_params(labelsize=16)
    prepare(fig)
    assert text.get_fontsize() == 23
    assert points.get_sizes() == pytest.approx([20000])
    assert ax.xaxis.get_major_ticks()[0].label1.get_fontsize() == 16


def test_existing_layout_engine_is_solved_then_frozen_for_output():
    fig, axes = plt.subplots(1, 2, figsize=(6, 3), layout='constrained')
    for ax in axes:
        ax.plot([0, 1], [0, 1])
        ax.set(xlabel='Time', ylabel='Response')
    prepare(fig)
    positions = [ax.get_position().bounds for ax in axes]
    fig.savefig(io.BytesIO(), format='svg')
    assert [ax.get_position().bounds for ax in axes] == positions
    prepare(fig)
    for ax, position in zip(axes, positions):
        assert ax.get_position().bounds == pytest.approx(position, abs=.002)


def test_density_images_are_counted_as_occupied_data():
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.imshow([[0, 1], [1, 0]], extent=(0, 1, 0, 1))
    proxy = plt.Line2D([], [], label='Field')
    legend = ax.legend(handles=[proxy], loc='center')
    prepare(fig)
    assert _data_overlap(ax, legend.get_window_extent(fig._get_renderer()), fig._get_renderer()) > 0
    assert legend._loc == 10


def test_colliding_bar_values_move_outward_without_changing_anchors():
    fig, ax = plt.subplots(figsize=(5, 2))
    first = ax.barh([-.175, .825, 1.825], [1, 1, 1], .35)
    second = ax.barh([.175, 1.175, 2.175], [1, 1, 1], .35)
    labels = [*ax.bar_label(first, fmt='%.2f', padding=3, fontsize=20),
              *ax.bar_label(second, fmt='%.2f', padding=3, fontsize=20)]
    ax.set_xlim(0, 5)
    fig.canvas.draw()
    anchors = [label.xy for label in labels]
    assert _bar_collisions(fig, fig._get_renderer()) > 0
    prepare(fig)
    assert _bar_collisions(fig, fig._get_renderer()) == 0
    assert [label.xy for label in labels] == anchors
    assert all(label.get_position()[1] == 0 for label in labels)
    assert all(label.get_fontsize() == 20 for label in labels)
    assert any(label.get_position()[0] > 3 for label in labels)


def test_data_changes_reopen_candidate_search(monkeypatch):
    from matplotlib.patches import Rectangle
    from hedgehogs.plots import presentation
    fig, ax = plt.subplots(figsize=(6, 4))
    occupied = Rectangle((0, 0), 1, 1, label='Data')
    ax.add_patch(occupied)
    ax.set(xlim=(0, 1), ylim=(0, 1))
    legend = ax.legend(loc='best')
    searches = []
    original_place = presentation._place_legend

    def place(*args, **kwargs):
        searches.append(occupied.get_visible())
        return original_place(*args, **kwargs)

    monkeypatch.setattr(presentation, '_place_legend', place)
    prepare(fig)
    assert legend._bbox_to_anchor is None
    occupied.set_visible(False)
    prepare(fig)
    assert legend._bbox_to_anchor is None
    assert searches == [True, False]
    assert legend._hedgehogs_finish_requested_loc == 0
    assert _data_overlap(ax, legend.get_window_extent(fig._get_renderer()), fig._get_renderer()) == 0


def test_per_point_opacity_is_safe_on_repeated_finishing():
    fig, ax = plt.subplots()
    points = ax.scatter([0, 1], [0, 1], alpha=[.3, .7])
    prepare(fig)
    prepare(fig)
    assert points.get_alpha() == pytest.approx([.3, .7])


def test_default_numeric_ticks_are_quieter_but_fixed_ticks_and_sizes_survive():
    from matplotlib.ticker import FixedLocator
    fig, ax, labels = benchmark()
    limits = ax.get_xlim(), ax.get_ylim()
    texts = [label.get_text() for label in labels]
    prepare(fig)
    lo, hi = ax.get_xlim()
    assert len([value for value in ax.get_xticks() if lo <= value <= hi]) <= 6
    assert isinstance(ax.yaxis.get_major_locator(), FixedLocator)
    assert [label.get_text() for label in labels] == texts
    assert (ax.get_xlim(), ax.get_ylim()) == limits
    ax.set_xticks([0, 3, 9, 18])
    ax.tick_params(axis='x', labelsize=17)
    ax.set_xlabel('Custom', fontsize=19)
    labels[0].set_fontsize(22)
    prepare(fig)
    assert list(ax.get_xticks()) == [0, 3, 9, 18]
    assert ax.xaxis.label.get_fontsize() == 19
    assert ax.xaxis.get_major_ticks()[0].label1.get_fontsize() == 17
    assert labels[0].get_fontsize() == 22
    prepare(fig)
    assert labels[0].get_fontsize() == 22


def test_reference_canvas_grids_and_specialised_plots_keep_their_scale():
    fig, ax = plt.subplots(figsize=hdg.figsize())
    ax.set_xlabel('x')
    prepare(fig)
    assert ax.xaxis.label.get_fontsize() == 10.5
    plt.close(fig)
    fig, axes = plt.subplots(2, 2, figsize=(8, 6))
    for ax in axes.flat:
        ax.set_xlabel('x')
    prepare(fig)
    assert all(ax.xaxis.label.get_fontsize() == 10.5 for ax in axes.flat)
    plt.close(fig)
    fig, axes = hdg.plots.pairplot({'x': [1, 2, 3], 'y': [2, 4, 6]})
    before = [ax.xaxis.label.get_fontsize() for ax in axes.flat]
    prepare(fig)
    assert [ax.xaxis.label.get_fontsize() for ax in axes.flat] == before


def test_explicit_locator_and_strokes_remain_author_owned_after_resize():
    from matplotlib.ticker import MaxNLocator
    fig, ax = plt.subplots(figsize=(5, 4))
    locator = MaxNLocator(nbins=9)
    ax.xaxis.set_major_locator(locator)
    ax.spines['left'].set_linewidth(3)
    prepare(fig)
    assert ax.xaxis.get_major_locator() is locator
    assert ax.spines['left'].get_linewidth() == 3
    first = ax.xaxis.label.get_fontsize()
    fig.set_size_inches(10, 8)
    prepare(fig)
    assert ax.xaxis.get_major_locator() is locator
    assert ax.spines['left'].get_linewidth() == 3
    assert ax.xaxis.label.get_fontsize() <= 23.1
    assert ax.xaxis.label.get_fontsize() >= first


def test_explicit_default_sized_fonts_are_not_treated_as_automatic():
    fig, ax = plt.subplots(figsize=(7, 4.5))
    bars = ax.barh([0, 1], [1, 2], label='Data')
    labels = ax.bar_label(bars, fontsize=10.5)
    ax.set_xlabel('x', fontsize=10.5)
    ax.set_ylabel('y', fontdict={'size': 10.5})
    ax.set_title('Title', fontsize=11.5)
    ax.tick_params(labelsize=9.5)
    legend = ax.legend(fontsize=9.5)
    prepare(fig)
    assert ax.xaxis.label.get_fontsize() == ax.yaxis.label.get_fontsize() == 10.5
    assert ax.title.get_fontsize() == 11.5
    assert labels[0].get_fontsize() == 10.5
    assert legend.get_texts()[0].get_fontsize() == 9.5
    assert ax.xaxis.get_major_ticks()[0].label1.get_fontsize() == 9.5


def test_font_ownership_hooks_restore_and_respect_third_party_methods():
    from matplotlib.axes import Axes
    hdg.reset_style()
    original = Axes.set_xlabel
    hdg.set_style()
    installed = Axes.set_xlabel
    assert installed is not original
    hdg.set_style()
    assert Axes.set_xlabel is installed
    hdg.reset_style()
    assert Axes.set_xlabel is original
    hdg.set_style()
    replacement = lambda *args, **kwargs: None
    setattr(Axes, 'set_xlabel', replacement)
    try:
        hdg.reset_style()
        assert Axes.set_xlabel is replacement
    finally:
        setattr(Axes, 'set_xlabel', original)


def test_default_title_still_fits_after_role_refinement_and_can_grow_on_resize():
    fig, ax = plt.subplots(figsize=(4.48, 3.96))
    ax.set_title('Figure comparison across repeated measurements')
    prepare(fig)
    bounds = ax.title.get_window_extent(fig._get_renderer())
    assert bounds.x0 >= -1 and bounds.x1 <= fig.bbox.x1 + 1
    first = ax.title.get_fontsize()
    fig.set_size_inches(8, 5)
    prepare(fig)
    assert ax.title.get_fontsize() >= first
    ax.title.set_fontsize(20)
    prepare(fig)
    assert ax.title.get_fontsize() == 20


def test_colourbar_typography_follows_its_parent_and_preserves_its_locator():
    fig, ax = plt.subplots(figsize=(5, 4))
    image = ax.imshow([[0, 1], [2, 3]])
    cb = fig.colorbar(image, ax=ax)
    ax.set_xlabel('x')
    cb.set_label('Value')
    locator = cb.ax.yaxis.get_major_locator()
    prepare(fig)
    assert cb.ax.yaxis.get_major_locator() is locator
    assert cb.ax.yaxis.label.get_fontsize() == ax.xaxis.label.get_fontsize()
    assert cb.ax.yaxis.get_major_ticks()[0].label1.get_fontsize() == ax.xaxis.get_major_ticks()[0].label1.get_fontsize()


def test_font_properties_and_legend_title_choices_remain_explicit():
    from matplotlib.font_manager import FontProperties
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.plot([0, 1], [1, 2], label='Data')
    ax.set_xlabel('x', fontproperties=FontProperties(size=10.5))
    ax.tick_params('x', labelsize=9.5)
    legend = ax.legend(title='Group', title_fontsize=9.5)
    prepare(fig)
    assert ax.xaxis.label.get_fontsize() == 10.5
    assert ax.xaxis.get_major_ticks()[0].label1.get_fontsize() == 9.5
    assert ax.yaxis.get_major_ticks()[0].label1.get_fontsize() > 9.5
    assert legend.get_title().get_fontsize() == 9.5
    assert legend.get_texts()[0].get_fontsize() > 9.5


@pytest.mark.presentation_smoke
def test_data_outlines_follow_the_frame_without_scaling_marker_area_or_explicit_widths():
    fig, ax = plt.subplots(figsize=(5, 4))
    default = ax.scatter([0, 1], [1, 2], s=20)
    explicit = ax.scatter([0, 1], [2, 3], s=10000, linewidths=.5)
    bars = ax.bar([0, 1], [1, 2])
    chosen = ax.bar([2], [1], linewidth=.5)
    line, = ax.plot([0, 1], [0, 1], marker='o', markeredgewidth=.5)
    prepare(fig)
    assert default.get_linewidths()[0] > .5
    assert default.get_sizes() == pytest.approx([20])
    assert explicit.get_sizes() == pytest.approx([10000])
    assert explicit.get_linewidths() == pytest.approx([.5])
    assert bars.patches[0].get_linewidth() > .5
    assert chosen.patches[0].get_linewidth() == .5
    assert line.get_markeredgewidth() == .5
    first = default.get_linewidths().copy()
    prepare(fig)
    assert default.get_linewidths() == pytest.approx(first)


def test_sparse_chart_has_more_typographic_presence_than_a_dense_report():
    dense_fig, dense_ax, _ = benchmark()
    prepare(dense_fig)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(['Length', 'Width'], [.65, .35])
    ax.set_ylabel('Importance')
    prepare(fig)
    assert ax.yaxis.label.get_fontsize() > dense_ax.xaxis.label.get_fontsize()
    assert ax.yaxis.label.get_fontsize() <= 23.1


def test_a_sparse_chart_can_become_dense_without_retaining_oversized_roles():
    fig, ax = plt.subplots(figsize=(7, 4.5))
    first = ax.barh([0, 1], [1, 2])
    ax.bar_label(first)
    ax.set_xlabel('Value')
    prepare(fig)
    larger = ax.xaxis.label.get_fontsize()
    more = ax.barh([2, 3, 4, 5], [1, 2, 3, 4])
    ax.bar_label(more)
    ax.set_yticks(range(6), list('abcdef'))
    prepare(fig)
    assert ax.xaxis.label.get_fontsize() < larger
    assert len(ax.texts) == 6


def test_outline_weight_is_aspect_invariant_and_small_markers_keep_a_face():
    from hedgehogs.plots.typography import outline_scale
    reference = (2.24, 2.2)
    assert outline_scale(1, 4, reference) == pytest.approx(outline_scale(2, 2, reference))
    assert outline_scale(4, 1, reference) == pytest.approx(outline_scale(2, 2, reference))
    fig, ax = plt.subplots(figsize=(2.24, 6.6))
    tiny = ax.scatter([0, 1], [1, 2], s=1)
    explicit = ax.scatter([0, 1], [2, 3], s=1, linewidths=2)
    normal = ax.scatter([0, 1], [3, 4], s=20)
    prepare(fig)
    assert normal.get_linewidths()[0] >= .8
    assert normal.get_sizes() == pytest.approx([20])
    assert tiny.get_linewidths()[0] <= .25
    assert explicit.get_linewidths() == pytest.approx([2])
    before = normal.get_linewidths().copy()
    prepare(fig)
    assert normal.get_linewidths() == pytest.approx(before)
    fig.set_size_inches(4.4, 4.4)
    prepare(fig)
    assert .8 <= normal.get_linewidths()[0] <= 1.1


def test_sine_and_scatter_legends_stay_inside_without_data_overlap_warnings():
    import numpy as np
    import warnings
    for scatter in (False, True):
        fig, ax = plt.subplots(figsize=hdg.figsize())
        x = np.linspace(0, 10, 20)
        if scatter:
            ax.scatter(x, np.sin(x), facecolors='white', edgecolors='black', label='Samples')
            ax.scatter(x[::3], np.sin(x[::3]), marker='x', label='Selected samples')
        else:
            ax.plot(x, np.sin(x), label='Sine wave')
        legend = ax.legend(loc='best')
        with warnings.catch_warnings(record=True) as records:
            warnings.simplefilter('always')
            prepare(fig)
        assert not [w for w in records if 'Legend' in str(w.message) or 'legend' in str(w.message)]
        assert legend._bbox_to_anchor is None
        assert ax.get_position().width > .4
        plt.close(fig)


def test_default_line_and_legend_strokes_follow_frame_but_explicit_widths_survive():
    fig, ax = plt.subplots(figsize=(5.6, 4.4))
    default, = ax.plot([0, 1], [0, 1], label='Default')
    explicit, = ax.plot([0, 1], [1, 0], linewidth=1.1, label='Explicit')
    legend = ax.legend(loc='upper left')
    prepare(fig)
    assert default.get_linewidth() > ax.spines['left'].get_linewidth()
    assert explicit.get_linewidth() == 1.1
    handles = legend.legend_handles if hasattr(legend, 'legend_handles') else legend.legendHandles
    assert handles[0].get_linewidth() == default.get_linewidth()
    assert legend._loc == 2


@pytest.mark.parametrize('logarithmic', [False, True])
def test_vector_scatter_overlap_matches_scalar_counts_at_boundaries(logarithmic):
    import numpy as np
    from matplotlib.transforms import Bbox
    fig, ax = plt.subplots()
    ax.scatter([1, 2, 3, np.nan, 4], [1, 2, 3, 4, np.inf])
    ax.scatter([], [])
    if logarithmic:
        ax.set(xscale='log', yscale='log')
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    points = ax.transData.transform([[1, 1], [3, 3]])
    boxes = [Bbox.from_extents(*points.flatten()), ax.bbox,
             Bbox.from_bounds(-100, -100, 1, 1)]
    offsets = {c: c.get_offset_transform().transform(c.get_offsets()) for c in ax.collections}
    for box in boxes:
        count = sum(box.contains(*p) for c in ax.collections
                    for p in np.ma.filled(offsets[c], np.nan))
        expected = count * box.width * box.height * .01
        assert _data_overlap(ax, box, renderer) == pytest.approx(expected)
        assert _data_overlap(ax, box, renderer, offsets) == pytest.approx(expected)


@pytest.mark.parametrize('seed', [1, 17, 20261009])
def test_vector_legend_search_retains_scalar_selection(seed, monkeypatch):
    import numpy as np
    from hedgehogs.plots import presentation
    rng = np.random.default_rng(seed)
    fig, ax = plt.subplots()
    ax.scatter(*rng.normal(size=(2, 300)), label='Samples')
    ax.scatter(*rng.uniform(-2, 2, size=(2, 100)), label='Selected')
    legend = ax.legend(loc='best')
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    presentation._place_legend(fig, ax, renderer)
    vector_location = legend._loc
    vector_bounds = legend.get_window_extent(renderer).bounds

    def scalar_overlap(axes, box, renderer, offsets=None):
        return sum(box.contains(*point) for c in axes.collections
                   for point in c.get_offset_transform().transform(c.get_offsets())) * presentation._area(box) * .01

    monkeypatch.setattr(presentation, '_data_overlap', scalar_overlap)
    presentation._legend_location(legend, 0)
    presentation._place_legend(fig, ax, renderer)
    assert legend._loc == vector_location
    assert legend.get_window_extent(renderer).bounds == pytest.approx(vector_bounds)


def test_native_legend_cache_reuses_geometry_and_restores_on_failure(monkeypatch):
    from matplotlib.legend import Legend
    from hedgehogs.plots.rendering import _cached_legend_search
    fig, ax = plt.subplots()
    ax.scatter([0, 1], [0, 1], label='Samples')
    legend = ax.legend(loc='best')
    renderer = fig._get_renderer()
    original = Legend._find_best_position
    calls = []

    def counted(self, *args, **kwargs):
        calls.append(1)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Legend, '_find_best_position', counted)
    with pytest.raises(RuntimeError):
        with _cached_legend_search(fig):
            first = legend._find_best_position(50, 20, renderer)
            assert legend._find_best_position(50, 20, renderer) == first
            assert len(calls) == 1
            ax.set_xlim(-2, 2)
            legend._find_best_position(50, 20, renderer)
            assert len(calls) == 2
            raise RuntimeError('draw failure')
    assert '_find_best_position' not in legend.__dict__
    with _cached_legend_search(fig):
        legend._find_best_position(50, 20, renderer)
    assert len(calls) == 3


@pytest.mark.parametrize('placement', ['best', 'upper right', 'external'])
def test_cached_draw_matches_uncached_after_edits_and_resize(placement, monkeypatch):
    from contextlib import nullcontext
    import numpy as np
    from hedgehogs.plots import rendering
    original_cache = rendering._cached_legend_search
    outcomes = []
    for cached in (False, True):
        monkeypatch.setattr(rendering, '_cached_legend_search', original_cache if cached else lambda fig: nullcontext())
        fig, ax = plt.subplots(figsize=(3.5, 2.65))
        scatter = ax.scatter([0, .2, .4, .8, 1], [1, .8, .3, .4, .1], label='Samples')
        options = {'loc': 'upper left', 'bbox_to_anchor': (1, 1)} if placement == 'external' else {'loc': placement}
        legend = ax.legend(**options)
        stages = []
        for edited in (False, True):
            if edited:
                scatter.set_offsets([[0, 0], [.2, .1], [.4, .5], [.8, .7], [1, 1]])
                ax.set(xlim=(-.2, 1.2), xlabel='Changed X', yscale='symlog')
                legend.get_texts()[0].set_text('Changed samples')
                fig.set_size_inches(4, 3)
            prepare(fig)
            stages.append((ax.get_position().bounds, legend.get_window_extent(fig._get_renderer()).bounds))
            fig.savefig(io.BytesIO(), format='png')
            stages.append((ax.get_position().bounds, legend.get_window_extent(fig._get_renderer()).bounds))
        assert '_find_best_position' not in legend.__dict__
        outcomes.append(stages)
        plt.close(fig)
    assert np.asarray(outcomes[0]) == pytest.approx(np.asarray(outcomes[1]))


def test_finishing_selects_auto_legend_once_without_rasterising(monkeypatch, tmp_path):
    import numpy as np
    from matplotlib.legend import Legend
    from hedgehogs.plots import presentation
    data = np.random.default_rng(17).normal(size=(500, 2))
    fig, ax = plt.subplots(figsize=(3.5, 2.65))
    scatter = ax.scatter(*data.T, label='Samples')
    legend = ax.legend(loc='best')
    searches = []
    original_place = presentation._place_legend
    draws = []
    original_draw = fig.canvas.draw

    def native_search(*args, **kwargs):
        raise AssertionError('Finishing must not run native best placement.')

    def place(*args, **kwargs):
        searches.append(1)
        return original_place(*args, **kwargs)

    def draw():
        draws.append(1)
        return original_draw()

    monkeypatch.setattr(Legend, '_find_best_position', native_search)
    monkeypatch.setattr(presentation, '_place_legend', place)
    monkeypatch.setattr(fig.canvas, 'draw', draw)
    monkeypatch.setattr(plt, 'show', lambda **kwargs: None)
    hdg.plots.show(fig, block=False)
    assert len(searches) == len(draws) == 1
    assert 1 <= legend._loc <= 10
    assert legend.get_in_layout()
    assert not scatter.get_rasterized()
    assert np.array_equal(scatter.get_offsets(), data)
    hdg.plots.show(fig, block=False)
    assert len(searches) == 1 and len(draws) == 2
    scatter.set_offsets(data * 2)
    fig.set_size_inches(4, 3)
    hdg.plots.show(fig, block=False)
    assert len(searches) == 2
    assert np.array_equal(scatter.get_offsets(), data * 2)
    hdg.plots.save(tmp_path / 'vector', fig=fig, formats=('pdf', 'svg'), bbox_inches=None)
    assert b'/Subtype /Image' not in (tmp_path / 'vector.pdf').read_bytes()
    assert '<image' not in (tmp_path / 'vector.svg').read_text()
    assert not scatter.get_rasterized()


def test_deferred_legend_restores_flags_on_measurement_failure():
    from hedgehogs.plots.presentation import _defer_auto_legends
    fig, axes = plt.subplots(1, 2)
    for ax in axes:
        ax.plot([0, 1], label='Data')
    automatic = axes[0].legend(loc='best')
    explicit = axes[1].legend(loc='upper left', bbox_to_anchor=(1, 1))
    with pytest.raises(RuntimeError):
        with _defer_auto_legends(fig):
            assert automatic._loc == 1 and not automatic.get_in_layout()
            assert explicit._loc == 2 and explicit.get_in_layout()
            raise RuntimeError('measurement failure')
    assert automatic._loc == 0 and automatic.get_in_layout()
    assert explicit._loc == 2 and explicit.get_in_layout()
