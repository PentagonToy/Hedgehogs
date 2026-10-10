"""Explicit coverage and timing audit for the development-only hybrid policy."""
import argparse
from pathlib import Path
import json
import sys
from time import perf_counter
import statistics

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import hedgehogs as hdg
from hedgehogs.plots import presentation
import legend_grid
from compare_legend_grid import samples, score


def create(kind, seed, size, font, count=1000):
    hdg.set_style(figure_size=size)
    plt.rcParams['font.serif'] = [font]
    fig, ax = plt.subplots(figsize=size, subplot_kw={'projection': 'polar'} if kind == 'polar' else {})
    rng = np.random.default_rng(seed)
    data = rng.uniform(0, 1, (count, 2))
    if kind == 'hole':
        data = samples('off-centre-hole', count, seed)
    elif kind == 'clusters':
        data = samples('clusters', count, seed)
    elif kind == 'masked':
        data = np.ma.array(data, mask=False)
        data.mask[::7] = True
    if kind in ('line', 'long-line', 'log', 'polar'):
        x = np.linspace(.001, 1, 5000 if kind == 'long-line' else 200)
        ax.plot(x, .5 + .3 * np.sin(x * (seed + 5)), label='Response')
        if kind == 'log':
            ax.set_xscale('log')
    elif kind == 'bars':
        ax.bar(range(5), rng.uniform(.1, 1, 5), label='Values')
    elif kind == 'image':
        ax.imshow(rng.uniform(0, 1, (20, 20)), extent=(0, 1, 0, 1))
        ax.plot([.1, .9], [.2, .8], label='Line')
    elif kind == 'fill':
        x = np.linspace(0, 1, 30)
        ax.fill_between(x, .2, .4 + .1 * np.sin(x * 10), label='Band')
    else:
        ax.scatter(*data.T, s=8, label='Samples')
    if kind == 'mixed':
        ax.plot([0, .5, 1], [.2, .7, .3], label='Model')
    if kind == 'long-labels':
        ax.collections[0].set_label('Velocity residual\n(several measurement series)')
    if kind == 'annotation':
        ax.text(.55, .8, 'Important result', transform=ax.transAxes, fontsize=12)
    if kind == 'nan':
        data[::7] = np.nan
        ax.collections[0].set_offsets(data)
    if kind not in ('bars', 'polar', 'log'):
        ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.set(xlabel='x', ylabel='Response')
    ax.legend(loc='best', title='Results' if seed % 2 else None)
    return fig, ax


def numeric(value):
    return np.array([value[key] for key in ('clipping', 'text_overlap', 'data_overlap')])


def no_worse(first, second):
    for left, right in zip(first, second):
        if np.isclose(left, right, rtol=1e-10, atol=1e-12):
            continue
        return left < right
    return True


def validate(output):
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    for kind in ('uniform', 'hole', 'clusters', 'line', 'long-line', 'bars', 'image', 'fill', 'annotation', 'masked', 'nan', 'log', 'polar', 'mixed', 'long-labels'):
        for seed in (3, 12, 29):
            for size in ((2.24, 2.2), (4.76, 3.4)):
                for font in ('Times New Roman', 'DejaVu Serif'):
                    fig, ax = create(kind, seed, size, font)
                    try:
                        presentation.prepare(fig)
                        renderer = fig.canvas.get_renderer()
                        base = score(fig, ax)
                        position = ax.get_legend()._loc
                        bounds = np.array(ax.get_position().bounds)
                        for threshold in (0., .1, .25):
                            presentation._legend_location(ax.get_legend(), 0)
                            legend_grid.hybrid(fig, ax, renderer, min_relative_gain=threshold)
                            result = score(fig, ax)
                            assert no_worse(numeric(result), numeric(base)), (kind, base, result)
                            assert np.allclose(bounds, ax.get_position().bounds, atol=1e-12, rtol=0)
                            if no_worse(numeric(base), numeric(result)):
                                assert ax.get_legend()._loc == position, (kind, position, result)
                            rows.append({'case': kind, 'seed': seed, 'size': size, 'font': font,
                                         'threshold': threshold, 'base': base, 'hybrid': result})
                    finally:
                        plt.close(fig)
                        hdg.reset_style()
    times = []
    for count in (10000, 100000, 1000000):
        for kind in ('uniform', 'hole', 'line'):
            if kind == 'line' and count != 10000:
                continue
            fig, ax = create(kind, 11, (4.76, 3.4), 'Times New Roman', count)
            try:
                presentation.prepare(fig)
                renderer = fig.canvas.get_renderer()
                for mode, method in [('classic', legend_grid.FIXED), ('hybrid', legend_grid.hybrid)]:
                    durations = []
                    for _ in range(5):
                        presentation._legend_location(ax.get_legend(), 0)
                        start = perf_counter()
                        method(fig, ax, renderer)
                        durations.append(perf_counter() - start)
                    times.append({'case': kind, 'points': count if kind != 'line' else 200,
                                  'mode': mode, 'median_s': statistics.median(durations), 'runs_s': durations})
            finally:
                plt.close(fig)
                hdg.reset_style()
    pipeline = []
    from contextlib import nullcontext
    original_show = plt.show
    plt.show = lambda **kwargs: None
    try:
        for count in (100000, 1000000):
            for kind in ('uniform', 'hole'):
                for mode in ('classic', 'hybrid'):
                    durations = []
                    for repeat in range(3):
                        fig, ax = create(kind, 11, (4.76, 3.4), 'Times New Roman', count)
                        try:
                            context = legend_grid.experimental_placement() if mode == 'hybrid' else nullcontext()
                            with context:
                                start = perf_counter()
                                hdg.plots.show(fig, block=False)
                                durations.append(perf_counter() - start)
                        finally:
                            plt.close(fig)
                            hdg.reset_style()
                    pipeline.append({'case': kind, 'points': count, 'mode': mode,
                                     'median_s': statistics.median(durations), 'runs_s': durations})
    finally:
        plt.show = original_show
    (output / 'audit.json').write_text(json.dumps({'cases': rows, 'timings': times, 'show_pipeline': pipeline}, indent=2)+'\n')
    print('Audited cases:', len(rows), 'timing cases:', len(times), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    validate(parser.parse_args().output)
