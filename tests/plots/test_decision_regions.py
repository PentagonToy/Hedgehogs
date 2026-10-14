import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.colors import BoundaryNorm

import hedgehogs as hdg


class Classifier:
    classes_ = np.array(['left', 'right', 'absent'])

    def predict(self, X):
        self.grid = np.asarray(X)
        return np.where(self.grid[:, 0] < 0, 'left', 'right')


@pytest.fixture(autouse=True)
def clean_figures():
    yield
    plt.close('all')
    hdg.reset_style()


def test_named_classes_use_model_order_and_preserve_existing_axes():
    hdg.set_style(palette='tableau10')
    fig, ax = plt.subplots()
    line, = ax.plot([-1, 1], [0, 0])
    model = Classifier()
    result = hdg.plots.decision_regions([[-1, 0], [1, 1]], ['left', 'right'], model)
    assert result is ax and line in ax.lines
    assert model.grid.shape == (40000, 2)
    region = next(item for item in ax.collections if isinstance(item.norm, BoundaryNorm))
    assert region.norm.boundaries.tolist() == [-.5, .5, 1.5, 2.5]
    assert ax.get_legend_handles_labels()[1] == ['left', 'right']
    sample = next(item for item in ax.collections if item.get_label() == 'left')
    assert sample.get_edgecolors()[0, :3] == pytest.approx([0, 0, 0])
    from matplotlib.colors import to_rgba
    assert sample.get_facecolors()[0] == pytest.approx(
        to_rgba(hdg.get_palette('tableau10')[0], alpha=.85))
    assert len(fig.axes) == 1


def test_numeric_labels_column_mappings_and_unfilled_markers():
    class Model:
        def predict(self, X):
            return np.where(X[:, 0] < 0, 10, 20)

    ax = hdg.plots.decision_regions({'a': [-1, 1], 'b': [0, 0]},
                                    {'target': [10, 20]}, Model(), markers=['x'],
                                    palette='okabe-ito')
    assert ax.get_legend_handles_labels()[1] == ['10', '20']
    assert ax.get_ylim()[0] < 0 < ax.get_ylim()[1]


def test_category_names_preserve_class_order_and_predictions():
    class Model:
        classes_ = [1, 0]

        def predict(self, X):
            return np.where(X[:, 0] < 0, 0, 1)

    ax = hdg.plots.decision_regions([[-1, 0], [1, 1]], [0, 1], Model(),
                                    categories={0: 'malignant', 1: 'benign'})
    assert ax.get_legend_handles_labels()[1] == ['benign', 'malignant']
    samples = [item for item in ax.collections if item.get_label() == 'malignant']
    assert samples[0].get_offsets().tolist() == [[-1, 0]]


def test_partial_category_names_keep_original_labels():
    ax = hdg.plots.decision_regions([[-1, 0], [1, 1]], ['left', 'right'], Classifier(),
                                    categories={'left': 'Left-hand class'})
    assert ax.get_legend_handles_labels()[1] == ['Left-hand class', 'right']


@pytest.mark.parametrize('categories,error', [
    (['Left', 'Right'], TypeError), ({'unknown': 'Name'}, ValueError),
    ({'left': 1}, ValueError), ({'left': ' '}, ValueError),
])
def test_invalid_categories_do_not_draw(categories, error):
    with pytest.raises(error):
        hdg.plots.decision_regions([[-1, 0]], ['left'], Classifier(), categories=categories)
    assert not plt.get_fignums()


def test_single_class_and_more_than_five_classes():
    class Model:
        def __init__(self, labels):
            self.classes_ = labels

        def predict(self, X):
            return np.repeat(self.classes_[0], len(X))

    for labels in [[7], list(range(8))]:
        plt.figure()
        ax = hdg.plots.decision_regions([[i, i] for i in range(len(labels))],
                                        labels, Model(labels))
        assert len(ax.collections) == len(labels) + 1
        region = next(item for item in ax.collections if isinstance(item.norm, BoundaryNorm))
        assert region.cmap.N == len(labels)


@pytest.mark.parametrize('X,y', [([], []), ([[1]], [0]),
    ([[1, 2, 3]], [0]), ([[np.nan, 0]], [0]), ([[1, 2]], []),
    ([[1, 2]], [None]), ([[1, 2]], [[0, 1]]), ([[1, 2]], [0, 1])])
def test_invalid_inputs_do_not_create_figures(X, y):
    with pytest.raises(ValueError):
        hdg.plots.decision_regions(X, y, Classifier())
    assert not plt.get_fignums()


def test_invalid_prediction_and_unknown_classes_do_not_draw():
    class Model:
        classes_ = ['left']

        def predict(self, X):
            return ['unknown'] * len(X)

    with pytest.raises(ValueError, match='Unknown class label'):
        hdg.plots.decision_regions([[0, 1]], ['left'], Model())
    assert not plt.get_fignums()


def test_dataframe_features_and_column_labels():
    pd = pytest.importorskip('pandas')

    class Model(Classifier):
        feature_names_in_ = ['a', 'b']

        def predict(self, X):
            assert isinstance(X, pd.DataFrame)
            assert list(X.columns) == self.feature_names_in_
            return super().predict(X)

    ax = hdg.plots.decision_regions(pd.DataFrame({'a': [-1, 1], 'b': [0, 1]}),
                                    pd.DataFrame({'label': ['left', 'right']}), Model())
    assert ax.get_legend_handles_labels()[1] == ['left', 'right']


def test_added_points_expand_limits_and_refresh_vector_background():
    model = Classifier()
    ax = hdg.plots.decision_regions([[-1, 0], [1, 1]], ['left', 'right'], model)
    ax.scatter([-4, 6], [5, -3], marker='X')
    ax.figure.canvas.draw()
    assert ax.get_xlim()[0] < -4 < 6 < ax.get_xlim()[1]
    assert ax.get_ylim()[0] < -3 < 5 < ax.get_ylim()[1]
    assert model.grid[:, 0].min() == pytest.approx(ax.get_xlim()[0])
    assert model.grid[:, 0].max() == pytest.approx(ax.get_xlim()[1])
    assert model.grid[:, 1].min() == pytest.approx(ax.get_ylim()[0])
    assert ax.dataLim.bounds == pytest.approx((-4, -3, 10, 8))
    bounds = (ax.get_xlim(), ax.get_ylim())
    ax.figure.canvas.draw()
    assert (ax.get_xlim(), ax.get_ylim()) == bounds
    assert sum(isinstance(item.norm, BoundaryNorm) for item in ax.collections) == 1
    assert not ax.images


def test_explicit_limits_and_existing_autoscale_choices_are_preserved():
    _, ax = plt.subplots()
    ax.set(xlim=(-8, 8), ylim=(-6, 6))
    model = Classifier()
    hdg.plots.decision_regions([[-1, 0], [1, 1]], ['left', 'right'], model)
    ax.scatter([20], [20])
    ax.figure.canvas.draw()
    assert ax.get_xlim() == (-8, 8)
    assert ax.get_ylim() == (-6, 6)
    assert model.grid[:, 0].min() == -8
    assert not ax.get_autoscalex_on() and not ax.get_autoscaley_on()
