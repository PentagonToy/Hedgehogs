"""Opt-in scatter timings; elapsed time is evidence, not a portable pass limit."""
import json
import platform
import subprocess
import sys
from pathlib import Path
from time import perf_counter

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pytest

import hedgehogs as hdg
from hedgehogs.plots import rendering

pytestmark = pytest.mark.load


@pytest.fixture(scope='module')
def measurements(request):
    rows = []
    yield rows
    report = {
        'python': sys.version, 'executable': sys.executable,
        'platform': platform.platform(), 'machine': platform.machine(),
        'matplotlib': matplotlib.__version__, 'numpy': np.__version__,
        'hedgehogs_source': hdg.__file__, 'backend': matplotlib.get_backend(),
        'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        'source_worktree': subprocess.check_output(['git', 'status', '--short'], text=True).splitlines(),
        'figure_inches': [3.5, 2.65], 'dpi': 150, 'seed': 20261009,
        'measurements': rows,
    }
    destination = request.config.getoption('--load-report')
    if destination:
        path = Path(destination).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2) + '\n')
    if not destination:
        print('\nSCATTER_LOAD_REPORT=' + json.dumps(report))


def timed(operation):
    start = perf_counter()
    operation()
    return perf_counter() - start


@pytest.mark.parametrize('points', [10_000, 100_000, 1_000_000])
@pytest.mark.parametrize('mode', ['matplotlib-fixed', 'matplotlib-best', 'hedgehogs-fixed', 'hedgehogs-best'])
def test_scatter_load(points, mode, measurements, monkeypatch):
    rng = np.random.default_rng(20261009)
    data = rng.normal(size=(points, 2))
    hdg.set_style()
    if mode.startswith('matplotlib-'):
        rendering.disable()  # Same rcParams; isolate the cost of Hedgehogs hooks.
    fig, ax = plt.subplots(figsize=(3.5, 2.65))
    try:
        start = perf_counter()
        scatter = ax.scatter(data[:, 0], data[:, 1], label='Samples')
        ax.set(xlabel='X', ylabel='Y')
        legend = ax.legend(loc='best' if mode.endswith('best') else 'upper right')
        creation = perf_counter() - start
        if mode.startswith('matplotlib-'):
            display = fig.canvas.draw
        else:
            monkeypatch.setattr(plt, 'show', lambda **kwargs: None)
            display = lambda: hdg.plots.show(fig, block=False)
        first = timed(display)
        bounds = ax.get_position().bounds
        repeat = timed(display)
        assert np.array_equal(scatter.get_offsets(), data)
        assert ax.get_position().bounds == pytest.approx(bounds)
        measurements.append({'points': points, 'mode': mode, 'creation_s': creation,
                             'first_show_s': first, 'repeat_show_s': repeat,
                             'legend_location': legend._loc,
                             'legend_bounds': list(legend.get_window_extent(fig.canvas.get_renderer()).bounds)})
    finally:
        plt.close(fig)
        hdg.reset_style()


@pytest.mark.parametrize('rasterized', [False, True])
def test_scatter_pdf_load(rasterized, measurements, tmp_path):
    data = np.random.default_rng(20261009).normal(size=(100_000, 2))
    hdg.set_style()
    fig, ax = plt.subplots(figsize=(3.5, 2.65))
    try:
        scatter = ax.scatter(data[:, 0], data[:, 1], rasterized=rasterized, label='Samples')
        ax.legend(loc='upper right')
        path = tmp_path / 'scatter.pdf'
        elapsed = timed(lambda: hdg.plots.save(path, fig=fig, bbox_inches=None))
        assert path.read_bytes().startswith(b'%PDF-')
        assert np.array_equal(scatter.get_offsets(), data)
        measurements.append({'points': len(data), 'mode': 'pdf-raster' if rasterized else 'pdf-vector',
                             'save_s': elapsed, 'bytes': path.stat().st_size})
    finally:
        plt.close(fig)
        hdg.reset_style()
