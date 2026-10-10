"""Run the existing synthetic plots notebook in isolated output directories."""
from pathlib import Path
from contextlib import nullcontext
import json
import os
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import hedgehogs as hdg
import legend_grid

output = Path(sys.argv[1]).resolve()
notebook = json.loads((ROOT / 'tutorials/plots.ipynb').read_text())
previous_dir = Path.cwd()
original_show = plt.show
plt.show = lambda **kwargs: None
results = {}
try:
    for mode in ('classic', 'hybrid'):
        directory = output / mode
        directory.mkdir(parents=True, exist_ok=True)
        os.chdir(directory)
        namespace = {}
        with legend_grid.experimental_placement() if mode == 'hybrid' else nullcontext():
            for index, cell in enumerate(notebook['cells']):
                if cell['cell_type'] == 'code':
                    exec(compile(''.join(cell['source']), f'plots.ipynb:cell{index}', 'exec'), namespace)
            results[mode] = [[list(axis.get_position().bounds) for axis in plt.figure(number).axes]
                             for number in plt.get_fignums()]
        plt.close('all')
        hdg.reset_style()
    assert len(results['classic']) == len(results['hybrid'])
    for original, hybrid in zip(results['classic'], results['hybrid']):
        assert np.allclose(original, hybrid, atol=1e-9, rtol=0), (original, hybrid)
    (output / 'notebook.json').write_text(json.dumps(results, indent=2)+'\n')
    print('Notebook figures verified:', len(results['classic']))
finally:
    os.chdir(previous_dir)
    plt.show = original_show
    plt.close('all')
    hdg.reset_style()
