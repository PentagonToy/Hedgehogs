"""Decision-tree semantics, measured geometry, and export regressions."""
import io
from types import SimpleNamespace

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.patches import FancyBboxPatch

import hedgehogs as hdg


@pytest.fixture(autouse=True)
def style():
    hdg.set_style()
    yield
    plt.close('all')
    hdg.reset_style()


def classifier():
    return SimpleNamespace(n_outputs_=1, n_features_in_=1, classes_=np.array(['A', 'B']),
                           criterion='gini', tree_=SimpleNamespace(
                               children_left=[1, -1, -1], children_right=[2, -1, -1],
                               feature=[0, -2, -2], threshold=[.5, -2, -2],
                               n_node_samples=[10, 4, 6], impurity=[.48, 0, 0],
                               value=np.array([[[4, 6]], [[4, 0]], [[0, 6]]])))


def test_graphviz_free_semantics_and_measured_boxes():
    hdg.plots.tree(classifier(), feature_names=['Feature with a long name'], class_names=['Alpha', 'Beta'])
    ax = plt.gca()
    fig = ax.figure
    fig.canvas.draw()
    texts = [text.get_text() for text in ax.texts]
    assert 'Feature with a long name ≤ 0.5' in texts
    assert any('class = Alpha' in text for text in texts)
    assert any('class = Beta' in text for text in texts)
    assert any('value = [4, 6]' in text for text in texts)
    assert texts.count('True') == texts.count('False') == 1
    patches = [p for p in ax.patches if isinstance(p, FancyBboxPatch)]
    assert len(patches) == 3
    renderer = fig.canvas.get_renderer()
    for text in ax.texts:
        if not text.get_text() or text.get_text() in ('True', 'False'):
            continue
        bounds = text.get_window_extent(renderer)
        assert any(p.get_window_extent(renderer).contains(*bounds.get_points()[0])
                   and p.get_window_extent(renderer).contains(*bounds.get_points()[1]) for p in patches)
    sizes = [text.get_fontsize() for text in ax.texts]
    for format in ('png', 'pdf', 'svg'):
        fig.savefig(io.BytesIO(), format=format, dpi=300)
        fig.canvas.draw()
        assert [text.get_fontsize() for text in ax.texts] == sizes


def test_depth_limit_marks_an_omitted_subtree():
    hdg.plots.tree(classifier(), max_depth=0)
    ax = plt.gca()
    assert len(ax.patches) == 1
    assert any('subtree omitted' in text.get_text() for text in ax.texts)


def test_regression_and_existing_axes():
    estimator = classifier()
    del estimator.classes_
    estimator.tree_.value = np.array([[[1.]], [[0.]], [[2.]]])
    fig, ax = plt.subplots(figsize=(6, 3))
    size = fig.get_size_inches().copy()
    annotations = hdg.plots.tree(estimator, ax=ax)
    assert all(artist.axes is ax for artist in annotations)
    fig.canvas.draw()
    assert fig.get_size_inches() == pytest.approx(size)
    assert any('value = 0' in text.get_text() for text in ax.texts)


@pytest.mark.parametrize('options', [{'max_depth': -1}, {'max_depth': True},
                                    {'feature_names': []}, {'class_names': ['A']}])
def test_invalid_options_fail_before_creating_a_figure(options):
    with pytest.raises(ValueError):
        hdg.plots.tree(classifier(), **options)
    assert not plt.get_fignums()


def test_unfitted_and_multioutput_models_fail_clearly():
    with pytest.raises(ValueError, match='fitted'):
        hdg.plots.tree(object())
    estimator = classifier()
    estimator.n_outputs_ = 2
    with pytest.raises(ValueError, match='single-output'):
        hdg.plots.tree(estimator)


@pytest.mark.parametrize('depth', [2, 5])
def test_real_sklearn_tree_has_nonoverlapping_nodes(depth):
    datasets = pytest.importorskip('sklearn.datasets')
    tree_module = pytest.importorskip('sklearn.tree')
    X, y = datasets.load_iris(return_X_y=True)
    estimator = tree_module.DecisionTreeClassifier(max_depth=depth, random_state=42).fit(X[:, 2:], y)
    hdg.plots.tree(estimator, feature_names=['length', 'width'])
    ax = plt.gca()
    ax.figure.canvas.draw()
    assert len(ax.patches) == estimator.tree_.node_count
    renderer = ax.figure.canvas.get_renderer()
    boxes = [patch.get_window_extent(renderer) for patch in ax.patches]
    for i, box in enumerate(boxes):
        assert all(not box.overlaps(other) for other in boxes[i + 1:])
        assert ax.figure.bbox.contains(*box.get_points()[0])
        assert ax.figure.bbox.contains(*box.get_points()[1])


def test_pyplot_canvas_and_annotation_return_match_plot_tree_convention():
    from matplotlib.text import Annotation
    fig = plt.figure(figsize=(10, 8))
    annotations = hdg.plots.tree(decision_tree=classifier(), feature_names=['length'])
    assert plt.gcf() is fig
    assert fig.get_size_inches() == pytest.approx([10, 8])
    assert all(isinstance(artist, Annotation) for artist in annotations)
    fig.canvas.draw()
    assert all(artist.get_fontfamily()[0] == 'Times New Roman' for artist in annotations)
    assert any(artist.get_fontweight() == 'bold' for artist in annotations)
    first_count = len(plt.gca().patches)
    hdg.plots.tree(classifier())
    assert len(plt.gca().patches) == first_count


def test_normalised_weighted_values_are_recovered_as_counts():
    estimator = classifier()
    estimator.tree_.value = np.array([[[.4, .6]], [[1, 0]], [[0, 1]]])
    estimator.tree_.weighted_n_node_samples = [20, 8, 12]
    annotations = hdg.plots.tree(estimator)
    assert any('samples = 10\nvalue = [8, 12]' in artist.get_text() for artist in annotations)
    annotations = hdg.plots.tree(estimator, proportion=True, impurity=False, node_ids=True, precision=2)
    assert any('samples = 100.00%\nvalue = [0.4, 0.6]' in artist.get_text() for artist in annotations)
    assert all('gini' not in artist.get_text() for artist in annotations)
    assert any('node #0' in artist.get_text() for artist in annotations)


def test_labels_can_be_hidden_and_style_options_are_not_exposed():
    annotations = hdg.plots.tree(classifier(), label='none')
    assert not any('samples =' in artist.get_text() for artist in annotations)
    for option in ('filled', 'rounded'):
        with pytest.raises(TypeError):
            hdg.plots.tree(classifier(), **{option: True})


@pytest.mark.parametrize('styled', [False, True])
def test_standalone_tree_uses_symmetric_canvas_margins_with_or_without_style(styled):
    if not styled:
        hdg.reset_style()
    fig = plt.figure(figsize=(6, 5))
    hdg.plots.tree(classifier(), feature_names=['length'])
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    boxes = [patch.get_window_extent(renderer) for patch in plt.gca().patches]
    left, right = min(box.x0 for box in boxes), max(box.x1 for box in boxes)
    top, bottom = max(box.y1 for box in boxes), min(box.y0 for box in boxes)
    assert (left + right) / 2 == pytest.approx(fig.bbox.width / 2, abs=1)
    assert (top + bottom) / 2 == pytest.approx(fig.bbox.height / 2, abs=1)
    assert left > 0 and bottom > 0
    assert right < fig.bbox.width and top < fig.bbox.height
    assert max((right - left) / fig.bbox.width, (top - bottom) / fig.bbox.height) > .8
