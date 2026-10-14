import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pytest
import hedgehogs as hdg


@pytest.fixture(autouse=True)
def clean():
    yield
    plt.close('all')
    hdg.reset_style()


@pytest.mark.parametrize('values', [[2, -1, .5], [0, 0, 0], [-2, -1, -.5], [2, 1, .5]])
def test_force_additive_endpoint_and_repeat(values, tmp_path):
    hdg.set_style()
    ax = hdg.plots.force_plot(.2, values, feature_names=['A', 'B', 'C'], max_display=1)
    endpoint = .2 + sum(values)
    assert any(np.allclose(line.get_xdata(), [endpoint, endpoint])
               and np.allclose(line.get_ydata(), [-.18, .65]) for line in ax.lines
               if len(line.get_xdata()) == 2)
    # Every drawn band's signed length preserves the complete attribution sum.
    assert sum(p.get_xy()[2, 0] - p.get_xy()[0, 0] for p in ax.patches) == pytest.approx(sum(values))
    hdg.plots.show(block=False)
    bounds = ax.get_position().bounds
    hdg.plots.show(block=False)
    assert ax.get_position().bounds == pytest.approx(bounds)
    ax.figure.savefig(tmp_path / 'force.svg')
    assert not any(p.get_rasterized() for p in ax.patches)


@pytest.mark.parametrize('kind', ['bar', 'dot'])
def test_summary_values_order_points_and_repeat(kind, tmp_path):
    values = np.array([[1, -4, 0], [-2, 3, 0], [0, 2, 0]])
    data = np.array([[1, 'a', np.nan], [2, 'b', np.nan], [3, 'c', np.nan]], dtype=object)
    hdg.set_style()
    ax = hdg.plots.summary_plot(values, data, feature_names=['A', 'B', 'C'], plot_type=kind)
    assert [t.get_text() for t in ax.get_yticklabels()] == ['B', 'A', 'C']
    if kind == 'bar':
        assert [p.get_width() for p in ax.patches] == pytest.approx([3, 1, 0])
    else:
        assert sum(len(p.get_offsets()) for p in ax.collections) == values.size
        assert len(ax.figure.axes) == 2
        positions = [p.get_offsets().copy() for p in ax.collections]
    hdg.plots.show(block=False)
    hdg.plots.show(block=False)
    if kind == 'dot':
        for p, old in zip(ax.collections, positions):
            np.testing.assert_array_equal(p.get_offsets(), old)
    ax.figure.savefig(tmp_path / 'summary.pdf')
    assert not any(p.get_rasterized() for p in ax.collections)


@pytest.mark.parametrize('call', [
    lambda: hdg.plots.force_plot([0, 1], [1, 2]),
    lambda: hdg.plots.force_plot(0, [[1, 2]]),
    lambda: hdg.plots.force_plot(0, [np.nan]),
    lambda: hdg.plots.force_plot(0, [1], feature_names=[]),
    lambda: hdg.plots.summary_plot(np.ones((2, 3, 2))),
    lambda: hdg.plots.summary_plot([[1]], [[1, 2]]),
    lambda: hdg.plots.summary_plot([[1]], plot_type='violin'),
    lambda: hdg.plots.summary_plot([[1]], max_display=0),
])
def test_invalid_input_before_figure_creation(call):
    with pytest.raises(ValueError):
        call()
    assert not plt.get_fignums()


def test_summary_cmap_and_unnamed_palette():
    from matplotlib.colors import to_rgba
    hdg.register_palette('attribution-test', ['#123456', '#abcdef'])
    hdg.set_style(palette='attribution-test')
    ax = hdg.plots.summary_plot([[1], [2]], [[0], [1]])
    assert ax.collections[0].cmap(0.) == pytest.approx(to_rgba('#123456'))
    assert ax.collections[0].cmap(1.) == pytest.approx(to_rgba('#abcdef'))
    plt.close('all')
    ax = hdg.plots.summary_plot([[1], [2]], [[0], [1]], cmap='viridis')
    assert ax.collections[0].cmap.name == 'viridis'


def test_invalid_cmap_does_not_create_figure():
    with pytest.raises(ValueError):
        hdg.plots.summary_plot([[1]], cmap='missing-cmap')
    assert not plt.get_fignums()


def test_force_explicit_size_and_label_connections():
    fig, ax = plt.subplots(figsize=(8, 3))
    hdg.plots.force_plot(0, [2, -1, .1], feature_names=['A', 'B', 'C'])
    assert fig.get_size_inches() == pytest.approx([8, 3])
    labels = [t for t in ax.texts if t.get_text() in ('A', 'B', 'C')]
    assert len(labels) == 3
    assert all(t.get_position()[1] < -.16 for t in labels)


def test_force_uses_continuous_sign_bands_without_dashed_baseline():
    ax = hdg.plots.force_plot(0, [2, 1, -3, -1])
    assert len(ax.patches) == 2
    assert sorted(abs(p.get_xy()[2, 0] - p.get_xy()[0, 0]) for p in ax.patches) == pytest.approx([3, 4])
    assert all(line.get_linestyle() != '--' for line in ax.lines)
    assert all(p.get_edgecolor()[3] == 0 for p in ax.patches)


def test_force_base_output_labels_are_separate_and_features_single_line():
    ax = hdg.plots.force_plot(0, [1, -.99], [1, 2], feature_names=['parch', 'sex'])
    texts = {t.get_text(): t for t in ax.texts}
    base = next(t for name, t in texts.items() if name.startswith('Base '))
    output = next(t for name, t in texts.items() if name.startswith('Output '))
    assert base.get_position()[1] < 0 < output.get_position()[1]
    assert 'parch=1' in texts and 'sex=2' in texts
    assert ax.get_xlabel() == ''



@pytest.mark.parametrize('maximum', [1, 2, 10])
def test_waterfall_grouped_steps_retain_full_sum(maximum, tmp_path):
    values = np.array([3., -2., .5, -.1])
    ax = hdg.plots.waterfall_plot(.2, values, max_display=maximum)
    patches = ax.patches
    signed_sum = sum(float(t.get_text()) for t in ax.texts if t.get_text().startswith(('+', '-')))
    assert signed_sum == pytest.approx(values.sum())
    assert len(patches) <= maximum
    hdg.plots.show(block=False)
    ax.figure.savefig(tmp_path / 'waterfall.svg')


@pytest.mark.parametrize('maximum', [1, 2, 10])
def test_decision_endpoints_order_and_highlight(maximum):
    values = np.array([[3., -2., .5], [-1, 2, 1]])
    ax = hdg.plots.decision_plot(.2, values, feature_names=['A', 'B', 'C'],
                                 feature_order=['C', 'A', 'B'], max_display=maximum, highlight=[1])
    assert [line.get_xdata()[-1] for line in ax.lines] == pytest.approx(.2 + values.sum(axis=1))
    assert ax.lines[1].get_linestyle() == '--'
    assert len(ax.lines) == 2
    hdg.plots.show(block=False)
    old = ax.get_position().bounds
    hdg.plots.show(block=False)
    assert ax.get_position().bounds == pytest.approx(old)


def test_dependence_preserves_pairs_and_missing_colour():
    values = np.array([[1, 2], [2, 3], [3, 4], [4, 5]])
    data = np.array([[10, 1], [20, np.nan], [30, 2], [np.nan, 3]])
    ax = hdg.plots.dependence_plot('A', values, data, feature_names=['A', 'B'], color_by='B', cmap='viridis')
    points = np.concatenate([c.get_offsets() for c in ax.collections])
    assert sorted(map(tuple, points.tolist())) == [(10, 1), (20, 2), (30, 3)]
    assert len(ax.figure.axes) == 2
    assert ax.collections[0].cmap.name == 'viridis'


@pytest.mark.parametrize('call', [
    lambda: hdg.plots.waterfall_plot([0, 1], [1]),
    lambda: hdg.plots.waterfall_plot(0, [[1]]),
    lambda: hdg.plots.decision_plot(0, [[1, 2]], feature_order=[0, 0]),
    lambda: hdg.plots.decision_plot(0, [[1, 2]], highlight=[2]),
    lambda: hdg.plots.decision_plot(0, np.ones((2, 2, 2))),
    lambda: hdg.plots.dependence_plot('missing', [[1]], [[2]]),
    lambda: hdg.plots.dependence_plot(0, [[1]], [['category']]),
    lambda: hdg.plots.dependence_plot(0, [[1]], [[np.nan]]),
])
def test_new_attribution_validation_before_drawing(call):
    with pytest.raises(ValueError):call()
    assert not plt.get_fignums()


@pytest.mark.parametrize('kind', ['waterfall', 'dependence', 'decision'])
def test_new_plots_preserve_explicit_canvas_and_vector_exports(kind, tmp_path):
    fig, ax = plt.subplots(figsize=(7, 4))
    values = np.array([[1., -2], [.5, .1]])
    original = values.copy()
    if kind == 'waterfall':hdg.plots.waterfall_plot(0, values[0])
    elif kind == 'dependence':hdg.plots.dependence_plot(0, values, [[1, 2], [3, 4]])
    else:hdg.plots.decision_plot(0, values)
    assert fig.get_size_inches() == pytest.approx([7, 4])
    hdg.plots.show(block=False)
    geometry = ax.get_position().bounds
    for ext in ['svg', 'pdf']:
        fig.savefig(tmp_path / f'{kind}.{ext}')
    hdg.plots.show(block=False)
    assert ax.get_position().bounds == pytest.approx(geometry)
    np.testing.assert_array_equal(values, original)
    assert not any(artist.get_rasterized() for artist in ax.collections)


def test_constant_decision_output_matches_colourbar():
    ax = hdg.plots.decision_plot(0, [[1, -1], [2, -2]])
    assert ax.lines[0].get_color() == pytest.approx(ax.figure.axes[1]._colorbar.cmap(.5))
