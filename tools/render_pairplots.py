"""Render Iris pairplots: python tools/render_pairplots.py OUTPUT_DIRECTORY."""
import argparse
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.datasets import load_iris
import hedgehogs as hdg


def render(output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    iris = load_iris()
    data = {name: iris.data[:, i] for i, name in enumerate(iris.feature_names)}
    data['species'] = [iris.target_names[index] for index in iris.target]
    hdg.set_style()
    for corner in (False, True):
        fig, _ = hdg.plots.pairplot(data, 'species', corner=corner)
        for suffix in ('png', 'pdf', 'svg'):
            fig.savefig(output / f'iris_{"corner" if corner else "full"}.{suffix}', dpi=200)
        plt.close(fig)
    hdg.reset_style()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    render(parser.parse_args().output)
