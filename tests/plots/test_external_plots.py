"""Optional real-library compatibility checks; no dataset downloads."""
import numpy as np
import matplotlib.pyplot as plt
import pytest
import hedgehogs as hdg


@pytest.fixture(autouse=True)
def style(monkeypatch):
    monkeypatch.setattr(plt, "show", lambda **kwargs: None)
    hdg.set_style()
    yield
    plt.close('all')
    hdg.reset_style()


@pytest.mark.parametrize('explicit', [False, True])
def test_dense_horizontal_bar_canvas_respects_author_size(explicit):
    fig, ax = plt.subplots(**({'figsize': (3., 2.5)} if explicit else {}))
    initial = fig.get_size_inches().copy()
    ax.barh(np.arange(12), np.arange(12))
    hdg.plots.show(fig)
    if explicit:
        np.testing.assert_array_equal(fig.get_size_inches(), initial)
    else:
        assert fig.get_size_inches()[1] >= 4.
    size = fig.get_size_inches().copy()
    hdg.plots.show(fig)
    np.testing.assert_array_equal(fig.get_size_inches(), size)


def test_resized_default_bar_canvas_is_preserved():
    fig, ax = plt.subplots()
    fig.set_size_inches(5., 6.)
    ax.barh(np.arange(12), np.arange(12))
    hdg.plots.show(fig)
    np.testing.assert_array_equal(fig.get_size_inches(), [5., 6.])


def test_xgboost_importance_without_axes():
    xgb = pytest.importorskip('xgboost')
    ax = xgb.plot_importance({f'Feature {i}': 1000 + i * 500 for i in range(12)})
    fig = ax.figure
    values = [p.get_width() for p in ax.patches]
    limits = ax.get_xlim()
    hdg.plots.show(fig)
    assert fig.get_size_inches()[1] >= 4.
    assert values == [p.get_width() for p in ax.patches]
    assert limits == ax.get_xlim()


@pytest.mark.parametrize('kind', ['bar', 'dot', 'dependence'])
def test_shap_explicit_finishing_preserves_native_font_and_canvas(kind):
    shap = pytest.importorskip('shap')
    rng = np.random.default_rng(7)
    data = rng.normal(size=(80, 8))
    values = data * np.arange(1, 9)
    if kind == 'dependence':
        shap.dependence_plot(0, values, data, show=False)
    else:
        shap.summary_plot(values, data, plot_type=kind, show=False)
    fig = plt.gcf()
    size = fig.get_size_inches().copy()
    hdg.plots.show(fig)
    np.testing.assert_array_equal(fig.get_size_inches(), size)
    assert max(text.get_fontsize() for ax in fig.axes for text in ax.get_yticklabels()) <= 13.01
    bounds = [ax.get_position().bounds for ax in fig.axes]
    hdg.plots.show(fig)
    np.testing.assert_allclose([ax.get_position().bounds for ax in fig.axes], bounds, atol=1e-9)


def test_lightgbm_importance_without_axes():
    lgb = pytest.importorskip('lightgbm')
    rng = np.random.default_rng(7)
    data = rng.normal(size=(120, 12))
    model = lgb.LGBMRegressor(n_estimators=5, num_leaves=4, min_child_samples=2,
                              verbosity=-1, n_jobs=1).fit(data, data.sum(axis=1))
    ax = lgb.plot_importance(model, ignore_zero=False)
    fig = ax.figure
    widths = [p.get_width() for p in ax.patches]
    hdg.plots.show(fig)
    assert fig.get_size_inches()[1] >= 4.
    assert widths == [p.get_width() for p in ax.patches]


@pytest.mark.parametrize('kind', ['bar', 'beeswarm', 'waterfall'])
def test_shap_explanation_plots_finish(kind):
    shap = pytest.importorskip('shap')
    rng = np.random.default_rng(12)
    data = rng.normal(size=(60, 8))
    explanation = shap.Explanation(values=data * np.arange(1, 9), data=data,
                                    base_values=np.zeros(60),
                                    feature_names=[f'Feature {i}' for i in range(8)])
    getattr(shap.plots, kind)(explanation[0] if kind == 'waterfall' else explanation,
                              show=False)
    fig = plt.gcf()
    size = fig.get_size_inches().copy()
    hdg.plots.show(fig)
    np.testing.assert_array_equal(fig.get_size_inches(), size)
    assert all(np.isfinite(ax.get_position().bounds).all() for ax in fig.axes)
    hdg.plots.show(fig)
    np.testing.assert_array_equal(fig.get_size_inches(), size)


def test_raw_bar_values_compact_without_rewriting_custom_labels():
    fig, ax = plt.subplots()
    values = [127.73332977294922, 123.456789012345, 114.19999694824219]
    ax.barh([0, 1, 2], values)
    raw = ax.text(values[0] + 1, 0, str(values[0]))
    custom = ax.text(values[1] + 1, 1, f'{values[1]:.10f}')
    explicit = ax.text(values[2] + 1, 2, str(values[2]), fontsize=8)
    strings = [custom.get_text(), explicit.get_text()]
    hdg.plots.show(fig)
    assert raw.get_text() == '127.7'
    assert [custom.get_text(), explicit.get_text()] == strings
    assert [p.get_width() for p in ax.patches] == values


def test_explicit_default_size_bar_text_retains_content():
    fig, ax = plt.subplots()
    value = 127.73332977294922
    ax.barh([0], [value])
    text = ax.text(value + 1, 0, str(value), fontsize=plt.rcParams['font.size'])
    hdg.plots.show(fig)
    assert text.get_text() == str(value)


def test_retired_text_wrapper_does_not_mark_new_text():
    retired = plt.Axes.text
    hdg.reset_style()
    hdg.set_style()
    fig, ax = plt.subplots()
    text = retired(ax, 0, 0, 'Explicit', fontsize=8)
    assert not getattr(text, '_hedgehogs_font_explicit', False)
