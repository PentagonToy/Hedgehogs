"""Representative optional scientific-library plots without remote datasets."""
from itertools import combinations
from pathlib import Path
import os
import numpy as np
import matplotlib.pyplot as plt
import pytest
import hedgehogs as hdg

CASES = ['sns-heatmap', 'sns-box', 'sns-violin', 'sns-facet', 'sns-joint',
         'sns-cluster', 'sns-pair', 'sklearn-confusion', 'sklearn-roc',
         'sklearn-pr', 'sklearn-error', 'sklearn-partial', 'pandas-bars',
         'pandas-dates', 'pandas-secondary', 'stats-qq', 'stats-acf', 'stats-pacf']


def create(case):
    rng = np.random.default_rng(47)
    pd = pytest.importorskip('pandas')
    data = pd.DataFrame(rng.normal(size=(120, 3)), columns=['Temperature', 'Pressure', 'Velocity'])
    data['Group'] = np.where(data.Temperature > 0, 'Condition A', 'Condition B')
    if case.startswith('sns-'):
        sns = pytest.importorskip('seaborn')
        if case == 'sns-heatmap':
            ax = sns.heatmap(data.iloc[:, :3].corr(), annot=True, cmap='cividis')
            return ax.figure
        if case == 'sns-box':
            return sns.boxplot(data=data, x='Group', y='Temperature').figure
        if case == 'sns-violin':
            return sns.violinplot(data=data, x='Group', y='Temperature').figure
        if case == 'sns-facet':
            return sns.relplot(data=data, x='Temperature', y='Pressure', col='Group', hue='Group').figure
        if case == 'sns-joint':
            return sns.jointplot(data=data, x='Temperature', y='Pressure', kind='hex').figure
        if case == 'sns-cluster':
            return sns.clustermap(data.iloc[:12, :3], cmap='cividis', figsize=(6, 5)).figure
        return sns.pairplot(data=data, hue='Group', diag_kind='hist').figure
    if case.startswith('sklearn-'):
        metrics = pytest.importorskip('sklearn.metrics')
        truth = np.arange(120) % 2
        scores = .2 + .6 * truth + rng.normal(0, .2, 120)
        if case == 'sklearn-confusion':
            return metrics.ConfusionMatrixDisplay.from_predictions(truth, scores > .5,
                          display_labels=['Negative', 'Positive']).figure_
        if case == 'sklearn-roc':
            return metrics.RocCurveDisplay.from_predictions(truth, scores).figure_
        if case == 'sklearn-pr':
            return metrics.PrecisionRecallDisplay.from_predictions(truth, scores).figure_
        if case == 'sklearn-error':
            return metrics.PredictionErrorDisplay.from_predictions(data.Temperature,
                                 data.Temperature + rng.normal(0, .3, 120)).figure_
        inspection = pytest.importorskip('sklearn.inspection')
        tree = pytest.importorskip('sklearn.tree')
        model = tree.DecisionTreeRegressor(max_depth=3, random_state=7).fit(data.iloc[:, :3], data.Temperature)
        return inspection.PartialDependenceDisplay.from_estimator(model, data.iloc[:, :3], [0, 1]).figure_
    if case == 'pandas-bars':
        return data.iloc[:8, :3].plot.bar().figure
    if case == 'pandas-dates':
        data.index = pd.date_range('2026-01-01', periods=len(data), freq='h')
        return data.iloc[:, :2].plot().figure
    if case == 'pandas-secondary':
        return data.iloc[:30, :2].plot(secondary_y='Pressure').figure
    sm = pytest.importorskip('statsmodels.api')
    if case == 'stats-qq':
        return sm.qqplot(data.Temperature, line='s')
    if case == 'stats-acf':
        return sm.graphics.tsa.plot_acf(data.Temperature, lags=20)
    return sm.graphics.tsa.plot_pacf(data.Temperature, lags=20)


@pytest.mark.parametrize('case', CASES)
def test_scientific_plot_finishing(case, monkeypatch):
    monkeypatch.setattr(plt, 'show', lambda **kwargs: None)
    hdg.set_style()
    try:
        fig = create(case)
        limits = [(ax.get_xlim(), ax.get_ylim()) for ax in fig.axes]
        lines = [(line, line.get_xydata().copy()) for ax in fig.axes for line in ax.lines]
        if case in ('sns-heatmap', 'sklearn-confusion'):
            payload = [image.get_array().copy() for ax in fig.axes for image in ax.images]
        else:
            payload = []
        hdg.plots.show(fig)
        if case in ('sns-heatmap', 'sklearn-confusion'):
            renderer = fig.canvas.get_renderer()
            main = fig.axes[0]
            for axis in (main.xaxis, main.yaxis):
                labels = [label for label in axis.get_ticklabels() if label.get_visible() and label.get_text()]
                for first, second in combinations(labels, 2):
                    assert not first.get_window_extent(renderer).overlaps(second.get_window_extent(renderer))
            for before, image in zip(payload, [image for ax in fig.axes for image in ax.images]):
                np.testing.assert_array_equal(image.get_array(), before)
        if case in ('sns-facet', 'sns-pair'):
            renderer = fig.canvas.get_renderer()
            for legend in fig.legends:
                box = legend.get_window_extent(renderer)
                assert box.x0 >= -1 and box.x1 <= fig.bbox.x1 + 1
                for text in [*legend.get_texts(), legend.get_title()]:
                    extent = text.get_window_extent(renderer)
                    assert extent.x0 >= -1 and extent.x1 <= fig.bbox.x1 + 1
                for ax in fig.axes:
                    assert not box.overlaps(ax.bbox)
        if case in ('sklearn-roc', 'sklearn-pr'):
            renderer = fig.canvas.get_renderer()
            for label in (fig.axes[0].xaxis.label, fig.axes[0].yaxis.label):
                box = label.get_window_extent(renderer)
                assert box.x0 >= -1 and box.y0 >= -1
                assert box.x1 <= fig.bbox.x1 + 1 and box.y1 <= fig.bbox.y1 + 1
        bounds = np.array([ax.get_position().bounds for ax in fig.axes])
        text = [(t, t.get_text(), t.get_fontsize()) for t in fig.findobj(plt.Text)]
        hdg.plots.show(fig)
        np.testing.assert_allclose([ax.get_position().bounds for ax in fig.axes], bounds, atol=1e-9, rtol=0)
        assert [(ax.get_xlim(), ax.get_ylim()) for ax in fig.axes] == limits
        for line, points in lines:
            np.testing.assert_array_equal(line.get_xydata(), points)
        for artist, value, size in text:
            assert artist.get_text() == value
            assert artist.get_fontsize() == pytest.approx(size)
        assert np.isfinite(bounds).all()
        output = os.environ.get('HDG_EXTERNAL_OUTPUT')
        if output:
            fig.savefig(Path(output) / (case + '.png'), dpi=140)
            hdg.plots.save(Path(output) / (case + '.svg'), fig=fig, bbox_inches=None)
    finally:
        plt.close('all')
        hdg.reset_style()


@pytest.mark.parametrize('explicit', [False, True])
def test_categorical_matrix_canvas_ownership(explicit, monkeypatch):
    monkeypatch.setattr(plt, 'show', lambda **kwargs: None)
    hdg.set_style()
    try:
        fig, ax = plt.subplots(**({'figsize': (3., 3.)} if explicit else {}))
        initial = fig.get_size_inches().copy()
        image = ax.imshow(np.arange(9).reshape(3, 3))
        fig.colorbar(image, ax=ax)
        ax.set_xticks([0, 1, 2], ['Temperature', 'Pressure', 'Velocity'])
        hdg.plots.show(fig)
        if explicit:
            np.testing.assert_array_equal(fig.get_size_inches(), initial)
        else:
            assert fig.get_size_inches()[0] >= 4.76
            assert fig.get_size_inches()[1] >= 4.12
        np.testing.assert_array_equal(image.get_array(), np.arange(9).reshape(3, 3))
    finally:
        plt.close('all')
        hdg.reset_style()


@pytest.mark.parametrize('side', ['center left', 'center right'])
def test_side_figure_legend_reserves_grid_space(side, monkeypatch):
    monkeypatch.setattr(plt, 'show', lambda **kwargs: None)
    hdg.set_style()
    try:
        fig, axes = plt.subplots(1, 2, figsize=(7, 3))
        for ax in axes:
            ax.plot([0, 1], [0, 1], label='Measured')
        legend = fig.legend(*axes[0].get_legend_handles_labels(), loc=side, fontsize=8)
        hdg.plots.show(fig)
        box = legend.get_window_extent(fig.canvas.get_renderer())
        for ax in axes:
            assert not box.overlaps(ax.bbox)
        position = legend._loc
        hdg.plots.show(fig)
        assert legend._loc == position
        np.testing.assert_array_equal(fig.get_size_inches(), [7, 3])
    finally:
        plt.close('all')
        hdg.reset_style()


def test_dense_bars_do_not_undo_long_label_space(monkeypatch):
    monkeypatch.setattr(plt, 'show', lambda **kwargs: None)
    hdg.set_style()
    try:
        fig, ax = plt.subplots()
        ax.barh(np.arange(6), np.arange(6))
        ax.set_ylabel('Long category description (experimental condition)')
        hdg.plots.show(fig)
        assert fig.get_size_inches()[1] >= 4.12
    finally:
        plt.close('all')
        hdg.reset_style()


def test_numeric_matrix_keeps_default_canvas(monkeypatch):
    monkeypatch.setattr(plt, 'show', lambda **kwargs: None)
    hdg.set_style()
    try:
        fig, ax = plt.subplots()
        initial = fig.get_size_inches().copy()
        ax.imshow(np.arange(9).reshape(3, 3))
        ax.set_xticks([0, 1, 2])
        hdg.plots.show(fig)
        np.testing.assert_array_equal(fig.get_size_inches(), initial)
    finally:
        plt.close('all')
        hdg.reset_style()
