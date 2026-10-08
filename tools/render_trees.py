"""Render Iris decision-tree examples: python tools/render_trees.py OUTPUT_DIRECTORY.

Requires scikit-learn for model fitting; rendering itself uses only Matplotlib.
"""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

import hedgehogs as hdg


def render(output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    iris = load_iris()
    X, _, y, _ = train_test_split(iris.data[:, 2:], iris.target, test_size=.2, random_state=42)
    hdg.set_style()
    for depth in (2, 5):
        estimator = DecisionTreeClassifier(max_depth=depth, random_state=42).fit(X, y)
        plt.figure(figsize=(10, 8))
        hdg.plots.tree(estimator, feature_names=['length', 'width'])
        ax = plt.gca()
        for suffix in ('png', 'pdf', 'svg'):
            ax.figure.savefig(output / f'iris_depth_{depth}.{suffix}', dpi=300)
        plt.close(ax.figure)
    hdg.reset_style()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    render(parser.parse_args().output)
