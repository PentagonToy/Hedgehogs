"""Explicit, local experiment; writes measurements and vector comparisons."""
import argparse
from contextlib import nullcontext
import json
from pathlib import Path
import platform
import statistics
import subprocess
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.transforms import Bbox
import hedgehogs as hdg
from hedgehogs.plots import presentation
import legend_grid


def samples(name, count, seed=20261010):
    rng = np.random.default_rng(seed)
    if name == 'off-centre-hole':
        points = rng.uniform(0, 1, (count * 2, 2))
        hole = ((points[:, 0] > .12) & (points[:, 0] < .67)
                & (points[:, 1] > .19) & (points[:, 1] < .48))
        return points[~hole][:count]
    if name == 'clusters':
        centres = np.array([[.15, .2], [.75, .25], [.3, .8], [.82, .85]])
        return rng.normal(0, .065, (count, 2)) + centres[np.arange(count) % 4]
    if name == 'uniform':
        return rng.uniform(0, 1, (count, 2))
    x = np.linspace(.03, .97, count)
    return np.column_stack((x, .5 + .28 * np.sin(x * 17)))


def create(data, name):
    hdg.set_style()
    fig, ax = plt.subplots(figsize=(4.76, 3.4), dpi=130)
    if name == 'line':
        ax.plot(data[:, 0], data[:, 1], label='Response')
    else:
        ax.scatter(data[:, 0], data[:, 1], s=4, label='Samples')
    ax.set(xlim=(0, 1), ylim=(0, 1), xlabel='x', ylabel='y')
    ax.legend(loc='best')
    return fig, ax


def score(fig, ax):
    renderer = fig.canvas.get_renderer()
    legend = ax.get_legend()
    box = legend.get_window_extent(renderer)
    area = max(presentation._area(box), 1.)
    texts = presentation._visible_texts(fig, renderer, set(legend.findobj()))
    return {'clipping': max(0., area - presentation._overlap(box, ax.bbox)) / area,
            'text_overlap': sum(presentation._overlap(box, text) for text in texts) / area,
            'data_overlap': presentation._data_overlap(ax, box, renderer) / area,
            'location': legend._loc, 'legend_bounds': list(box.bounds)}


def native(fig, ax, renderer):
    legend = ax.get_legend()
    presentation._legend_location(legend, 1)
    box = legend.get_window_extent(renderer)
    x, y = legend._find_best_position(box.width, box.height, renderer)
    presentation._legend_location(legend, ((x - ax.bbox.xmin) / ax.bbox.width,
                                            (y - ax.bbox.ymin) / ax.bbox.height))


def run(output, counts):
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    for name in ('off-centre-hole', 'clusters', 'uniform', 'line'):
        for count in (counts if name != 'line' else [301]):
            data = samples(name, count)
            fig, ax = create(data, name)
            presentation.prepare(fig)
            renderer = fig.canvas.get_renderer()
            bounds = np.array(ax.get_position().bounds)
            for mode, function in [('fixed-10', legend_grid.FIXED), ('grid', legend_grid.place), ('native-9', native)]:
                durations = []
                for _ in range(3):
                    presentation._legend_location(ax.get_legend(), 0)
                    start = perf_counter()
                    function(fig, ax, renderer)
                    durations.append(perf_counter() - start)
                row = {'case': name, 'points': len(data), 'mode': mode,
                       'placement_s': statistics.median(durations), **score(fig, ax)}
                assert np.allclose(ax.get_position().bounds, bounds, rtol=0, atol=1e-12)
                rows.append(row)
                if count == counts[0]:
                    hdg.echo(f'{name}: {mode}, overlap={row["data_overlap"]:.2f}, placement={row["placement_s"]:.4f}s')
                    fig.savefig(output / f'{name}-{mode}.svg', bbox_inches=None)
                    fig.savefig(output / f'{name}-{mode}.png', dpi=150, bbox_inches=None)
            plt.close(fig)
            hdg.reset_style()
    # Exercise actual finishing through show(), including edits and repeats.
    for mode in ('fixed-10', 'grid'):
        data = samples('off-centre-hole', counts[-1])
        fig, ax = create(data, 'off-centre-hole')
        original = plt.show
        plt.show = lambda **kwargs: None
        try:
            with legend_grid.experimental_placement() if mode == 'grid' else nullcontext():
                start = perf_counter()
                hdg.plots.show(fig, block=False)
                elapsed = perf_counter() - start
                initial = ax.get_position().bounds
                location = ax.get_legend()._loc
                hdg.plots.show(fig, block=False)
                assert np.allclose(initial, ax.get_position().bounds, rtol=0, atol=1e-12)
                assert ax.get_legend()._loc == location
                assert np.array_equal(ax.collections[0].get_offsets(), data)
                rows.append({'case': 'show-pipeline', 'mode': mode, 'points': len(data),
                             'first_show_s': elapsed, **score(fig, ax)})
        finally:
            plt.show = original
            plt.close(fig)
            hdg.reset_style()
    report = {'source_commit': subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip(),
              'python': sys.version, 'executable': sys.executable, 'platform': platform.platform(),
              'matplotlib': matplotlib.__version__, 'numpy': np.__version__, 'grid_resolution': 128,
              'measurements': rows}
    (output / 'measurements.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--points', type=int, nargs='+', default=[10000, 100000])
    args = parser.parse_args()
    run(args.output, args.points)
