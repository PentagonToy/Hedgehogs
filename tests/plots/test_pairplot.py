import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pytest
import hedgehogs as hdg


@pytest.fixture(autouse=True)
def style():
    hdg.set_style()
    yield
    plt.close('all')
    hdg.reset_style()


def test_numeric_selection_missing_pairs_and_style_preservation():
    before = dict(plt.rcParams)
    fig, axes = hdg.plots.pairplot({'x': [1, 2, None, 4], 'y': [3, 4, 5, float('nan')],
                            'species': ['A', 'B', 'A', 'B'], 'description': ['text'] * 4}, 'species')
    assert axes.shape == (2, 2)
    assert sum(len(collection.get_offsets()) for collection in axes[1, 0].collections) == 2
    assert dict(plt.rcParams) == before
    assert [text.get_text() for text in fig.legends[0].get_texts()] == ['A', 'B']
    assert axes[0, 0].child_axes[0].get_ylim() != axes[0, 0].get_ylim()
    for format in ('png', 'pdf', 'svg'):
        fig.savefig(io.BytesIO(), format=format)


def test_corner_order_and_histograms_share_bins():
    fig, axes = hdg.plots.pairplot({'x': [1, 2, 4, 5], 'y': [2, 3, 7, 8], 'g': ['a', 'a', 'b', 'b']},
                            'g', vars=['y', 'x'], hue_order=['b', 'a'], corner=True, bins=4, diag_kind='hist')
    assert not axes[0, 1].get_visible()
    assert axes[1, 0].get_xlabel() == 'y'
    first, second = axes[0, 0].child_axes[0].patches
    assert first.get_xy()[:, 0] == pytest.approx(second.get_xy()[:, 0])
    assert [text.get_text() for text in fig.legends[0].get_texts()] == ['b', 'a']


def test_single_variable_constant_and_no_hue():
    fig, axes = hdg.plots.pairplot({'x': [2, 2, 2]})
    fig.canvas.draw()
    assert axes.shape == (1, 1)
    assert not fig.legends
    assert axes[0, 0].get_xlim()[0] < 2 < axes[0, 0].get_xlim()[1]


@pytest.mark.parametrize('data, options', [({}, {}), ({'x': []}, {}),
    ({'x': [1], 'y': [2, 3]}, {}), ({'x': ['a']}, {}),
    ({'x': [1]}, {'vars': ['missing']}), ({'x': [1]}, {'bins': 0}),
    ({'x': [1]}, {'hue': 'missing'}), ({'x': [1]}, {'hue_order': ['a']})])
def test_invalid_data_fails_before_figure_creation(data, options):
    with pytest.raises(ValueError):
        hdg.plots.pairplot(data, **options)
    assert not plt.get_fignums()


def test_pandas_and_polars_inputs_when_installed():
    pd = pytest.importorskip('pandas')
    data = {'x': [1, 2, 3], 'y': [2, 4, 6], 'species': ['A', 'B', 'A']}
    fig, axes = hdg.plots.pairplot(pd.DataFrame(data), 'species')
    assert axes.shape == (2, 2)
    pl = pytest.importorskip('polars')
    fig, axes = hdg.plots.pairplot(pl.DataFrame(data), 'species')
    assert axes.shape == (2, 2)


def test_square_panels_and_active_palette_precedence():
    from matplotlib.colors import to_rgba
    data = {'x': [1, 2, 3], 'y': [4, 5, 6], 'g': ['a', 'b', 'a']}
    hdg.set_style(palette='tableau10')
    fig, axes = hdg.plots.pairplot(data, 'g')
    fig.canvas.draw()
    for ax in axes.flat:
        assert ax.bbox.width == pytest.approx(ax.bbox.height)
    assert axes[1, 0].collections[0].get_facecolors()[0] == pytest.approx(to_rgba(hdg.get_palette('tableau10')[0], alpha=.85))
    assert axes[1, 0].collections[0].get_alpha() == .85
    fig, axes = hdg.plots.pairplot(data, 'g', palette='okabe-ito')
    assert axes[1, 0].collections[0].get_facecolors()[0] == pytest.approx(to_rgba(hdg.get_palette()[0], alpha=.85))
    hdg.reset_style()
    fig, axes = hdg.plots.pairplot(data, 'g')
    assert axes[1, 0].collections[0].get_facecolors()[0] == pytest.approx(to_rgba(hdg.get_palette()[0], alpha=.85))


def test_kde_symmetry_normalisation_and_singular_fallback():
    from hedgehogs.plots.pairplot import _density
    grid = [-10 + i * .01 for i in range(2001)]
    density = _density([-1., 1.], grid)
    assert density is not None
    assert min(density) >= 0
    assert density == pytest.approx(list(reversed(density)), abs=1e-12)
    assert sum((a + b) * .005 for a, b in zip(density, density[1:])) == pytest.approx(1, abs=1e-6)
    assert _density([1.], grid) is None
    assert _density([2., 2.], grid) is None


def test_kde_and_legend_have_readable_defaults():
    fig, axes = hdg.plots.pairplot({'x': [1, 2, 3, 4], 'g': ['a', 'a', 'b', 'b']}, 'g')
    fig.canvas.draw()
    assert len(axes[0, 0].child_axes[0].lines) == 2
    assert len(axes[0, 0].child_axes[0].collections) == 2
    from hedgehogs.plots.typography import panel_scale
    assert fig.legends[0].get_texts()[0].get_fontsize() == pytest.approx(plt.rcParams['legend.fontsize'] * max(1., panel_scale(axes[0, 0])), rel=.01)


def test_density_matches_independent_scipy_reference_with_duplicate_samples():
    stats = pytest.importorskip('scipy.stats')
    from hedgehogs.plots.pairplot import _density
    sample = [0., 0., .5, 1., 2.]
    grid = [-1., 0., .5, 1., 3.]
    assert _density(sample, grid) == pytest.approx(stats.gaussian_kde(sample)(grid), rel=1e-12)


@pytest.mark.parametrize('corner', [False, True])
@pytest.mark.parametrize('diag_kind', ['hist', 'kde'])
def test_shared_scatter_ticks_independent_zero_density_and_outer_ticks(corner, diag_kind):
    data = {'x': [1, 2, 3, 4], 'y': [10, 20, 30, 40], 'z': [100, 200, 300, 400]}
    fig, axes = hdg.plots.pairplot(data, corner=corner, diag_kind=diag_kind)
    fig.canvas.draw()
    for row in range(3):
        assert axes[row, row].child_axes[0].get_ylim()[0] == 0
        for col in range(3):
            ax = axes[row, col]
            if not ax.get_visible():
                continue
            assert ax.get_xticks() == pytest.approx(axes[-1, col].get_xticks())
            if row != col:
                assert ax.get_yticks() == pytest.approx(axes[-1, row].get_xticks())
                assert not ax.get_shared_y_axes().joined(ax, axes[row, row].child_axes[0])
            for tick in ax.xaxis.get_major_ticks():
                assert tick.tick1line.get_visible() == (row == 2)
                assert not tick.tick2line.get_visible()
            for tick in ax.yaxis.get_major_ticks():
                assert tick.tick1line.get_visible() == (col == 0)
                assert not tick.tick2line.get_visible()
    if not corner:
        assert axes[1, 0].get_shared_y_axes().joined(axes[1, 0], axes[1, 2])


@pytest.mark.parametrize('categories', [3, 30])
def test_legend_stays_close_to_grid_and_fits_many_categories(categories):
    data = {'x': list(range(categories)), 'y': list(range(categories)),
            'target': [f'Class {index}' for index in range(categories)]}
    fig, axes = hdg.plots.pairplot(data, 'target')
    fig.canvas.draw()
    bounds = fig.legends[0].get_window_extent(fig.canvas.get_renderer())
    right = max(ax.bbox.x1 for ax in axes.flat)
    assert 0 < bounds.x0 - right < fig.dpi * .2
    assert bounds.x1 < fig.bbox.x1
    assert bounds.y0 >= 0 and bounds.y1 <= fig.bbox.y1
    assert len(fig.legends[0].get_texts()) == categories


def test_large_matrix_prioritises_readable_labels_ticks_and_legend():
    fig, axes = hdg.plots.pairplot({'A': [1, 2, 3], 'B': [2, 3, 4], 'C': [3, 4, 5],
                            'D': [4, 5, 6], 'target': ['a', 'b', 'a']}, 'target')
    fig.canvas.draw()
    from hedgehogs.plots.typography import panel_scale
    factor = max(1., panel_scale(axes[-1, 0]))
    assert axes[-1, 0].xaxis.label.get_fontsize() == pytest.approx(10.5 * factor, rel=.01)
    assert axes[-1, 0].xaxis.get_major_ticks()[0].label1.get_fontsize() == pytest.approx(9.5 * factor, rel=.01)
    assert fig.legends[0].get_texts()[0].get_fontsize() == pytest.approx(9.5 * factor, rel=.01)
    renderer = fig.canvas.get_renderer()
    for ax in axes.flat:
        if ax.get_xlabel():
            bounds = ax.xaxis.label.get_window_extent(renderer)
            assert bounds.y0 >= 0
            assert bounds.x0 >= 0 and bounds.x1 <= fig.bbox.x1


def test_custom_style_sizes_and_subsequent_artist_edits_remain_available():
    from hedgehogs.plots.typography import panel_scale
    hdg.set_style(base_fontsize=12, linewidth=2)
    plt.rcParams['lines.markersize'] = 8
    plt.rcParams['axes.linewidth'] = 1.3
    plt.rcParams['legend.fontsize'] = 11
    fig, axes = hdg.plots.pairplot({'x': [1, 2, 3], 'y': [4, 5, 6], 'g': ['a', 'b', 'a']}, 'g')
    fig.canvas.draw()
    factor = max(1., panel_scale(axes[1, 0]))
    points = axes[1, 0].collections[0]
    assert points.get_sizes() == pytest.approx([64 * factor ** 2], rel=.01)
    assert axes[1, 0].spines['left'].get_linewidth() == pytest.approx(1.3 * factor, rel=.01)
    assert fig.legends[0].get_texts()[0].get_fontsize() == pytest.approx(11 * factor, rel=.01)
    points.set_sizes([10000])
    axes[1, 0].xaxis.label.set_fontsize(25)
    fig.canvas.draw()
    assert points.get_sizes() == pytest.approx([10000])
    assert axes[1, 0].xaxis.label.get_fontsize() == 25
