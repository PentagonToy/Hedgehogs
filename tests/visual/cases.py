"""Small deterministic figures rendered through the public finishing API."""
from hashlib import sha256
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager, ft2font
import numpy as np

import hedgehogs as hdg

DPI = 100


def environment():
    font = Path(font_manager.findfont(font_manager.FontProperties(family='DejaVu Serif')))
    return {'matplotlib': matplotlib.__version__, 'freetype': ft2font.__freetype_version__,
            'font_sha256': sha256(font.read_bytes()).hexdigest()}


def environment_key():
    values = environment()
    return f"mpl-{values['matplotlib']}_ft-{values['freetype']}_font-{values['font_sha256'][:12]}"


def parity():
    fig, ax = plt.subplots(figsize=(4.48, 4.4))
    x = np.linspace(105, 140, 60)
    ax.scatter(x, x + 3*np.sin(x), s=14, alpha=.6, label='Linear Regression')
    ax.scatter(x, x + np.cos(x), s=14, alpha=.6, label='DNN')
    ax.plot([102, 143], [102, 143], '--', color='black', label='Ideal')
    ax.set(xlim=(102, 143), ylim=(102, 143), title='Airfoil Self-Noise Prediction',
           xlabel='Measured Sound Pressure Level (dB)', ylabel='Predicted Sound Pressure Level (dB)')
    hdg.plots.square(True)
    hdg.plots.legend(domain='outside', loc='upper center', ncol=3)
    return fig


def inside():
    fig, ax = plt.subplots(figsize=(4.48, 4.4))
    x = np.linspace(0, 2*np.pi, 80)
    ax.plot(x, np.sin(x), label='Sine')
    ax.plot(x, np.cos(x), label='Cosine')
    ax.set(xlabel='Phase', ylabel='Amplitude', title='Periodic signals')
    ax.legend(loc='upper right')
    return fig


def colourbar():
    fig, ax = plt.subplots(figsize=(4.48, 4.4))
    x, y = np.meshgrid(np.linspace(-1, 1, 24), np.linspace(-1, 1, 24))
    image = ax.pcolormesh(x, y, x*x + y*y, cmap='viridis', shading='auto')
    fig.colorbar(image, ax=ax, label='Value')
    ax.set(xlabel='x', ylabel='y')
    hdg.plots.square(True)
    return fig


def shared():
    fig, axes = plt.subplots(2, 2, figsize=(6.72, 5.5))
    x = np.linspace(0, 1, 40)
    for i, ax in enumerate(axes.flat):
        ax.plot(x, x**(i+1), label='Model')
        ax.plot(x, x, '--', label='Reference')
        ax.set(xlabel='x', ylabel='y')
    hdg.plots.square(ax=axes)
    hdg.plots.legend(domain='outside', loc='upper center', shared=True, ncol=2)
    return fig


def surface():
    fig = plt.figure(figsize=(4.48, 4.4))
    ax = fig.add_subplot(111, projection='3d')
    x, y = np.meshgrid(np.linspace(0, 1, 24), np.linspace(0, 1, 24))
    ax.plot_surface(x, y, np.sin(5*x)*np.cos(5*y), cmap='viridis')
    ax.set(xlabel='x', ylabel='y', zlabel='Objective', zlim=(-1, 1))
    ax.view_init(elev=25, azim=-60)
    ax.set_box_aspect((1, 1, .6))
    return fig


CASES = {'parity': parity, 'inside': inside, 'colourbar': colourbar,
         'shared': shared, 'surface': surface}


def render(name, destination):
    """Render one isolated reference with fixed font and raster settings."""
    previous = plt.rcParams.copy()
    fig = None
    try:
        plt.rcdefaults()
        hdg.set_style()
        plt.rcParams.update({'font.family': 'DejaVu Serif', 'font.serif': ['DejaVu Serif'],
                             'mathtext.fontset': 'dejavuserif', 'text.usetex': False})
        fig = CASES[name]()
        hdg.plots.save(destination, fig=fig, dpi=DPI, bbox_inches=None, transparent=False)
    finally:
        if fig is not None:
            plt.close(fig)
        hdg.reset_style()
        plt.rcParams.update(previous)
