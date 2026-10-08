"""Regression checks for ordinary Matplotlib figure sizing and rendering."""

import io

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.figure import Figure

import hedgehogs as hdg


@pytest.fixture(autouse=True)
def styled_figures():
    hdg.set_style()
    yield
    plt.close('all')
    hdg.reset_style()


def sine_figure(size):
    fig, ax = plt.subplots(figsize=size)
    x = np.linspace(0, 10, 100)
    line, = ax.plot(x, np.sin(x), label='Sine Wave', marker='o')
    ax.set(title='Sine Function', xlabel='X-axis', ylabel='Y-axis')
    # Explicit placement isolates point-size scaling from adaptive legend
    # fitting; the latter has separate coverage with wider fallback fonts.
    legend = ax.legend(loc='upper left', bbox_to_anchor=(0, 1))
    fig.canvas.draw()
    return fig, ax, line, legend


def dimensions(fig, ax, line, legend):
    renderer = fig.canvas.get_renderer()
    tick = ax.xaxis.get_major_ticks()[0]
    return np.array([
        ax.title.get_fontsize(), ax.xaxis.label.get_fontsize(),
        tick.label1.get_fontsize(), legend.get_texts()[0].get_fontsize(),
        line.get_linewidth(), line.get_markersize(),
        ax.spines['left'].get_linewidth(), tick.tick1line.get_markersize(),
        tick.tick1line.get_markeredgewidth(), ax.xaxis.labelpad,
        legend.get_window_extent(renderer).width,
        legend.get_window_extent(renderer).height,
    ])


@pytest.mark.parametrize('scale', [0.75, 1.5, 2.0])
@pytest.mark.parametrize('font_family', ['serif', 'DejaVu Serif'])
def test_pyplot_preserves_reference_proportions(scale, font_family):
    plt.rcParams['font.family'] = font_family
    size = hdg.figsize()
    baseline = sine_figure(size)
    enlarged = sine_figure(tuple(value * scale for value in size))
    actual, expected = dimensions(*enlarged), dimensions(*baseline) * scale
    assert actual[:10] == pytest.approx(expected[:10])
    # Raster font hinting rounds glyphs to pixels rather than exact point ratios.
    assert actual[10:] == pytest.approx(expected[10:], abs=2 * scale)
    # Figure-specific sizing must not leak into global defaults or other figures.
    assert plt.rcParams['axes.labelsize'] == 10.5
    assert dimensions(*baseline)[0] == 11.5


@pytest.mark.parametrize('font_family', ['serif', 'DejaVu Serif'])
def test_resize_and_repeated_draws_do_not_accumulate(font_family):
    plt.rcParams['font.family'] = font_family
    fig, ax, line, legend = sine_figure(hdg.figsize())
    base = dimensions(fig, ax, line, legend)
    fig.set_size_inches(*(value * 1.5 for value in hdg.figsize()))
    for _ in range(5):
        fig.canvas.draw()
        actual = dimensions(fig, ax, line, legend)
        assert actual[:10] == pytest.approx(base[:10] * 1.5)
        assert actual[10:] == pytest.approx(base[10:] * 1.5, abs=3)
    fig.set_size_inches(*hdg.figsize())
    fig.canvas.draw()
    assert dimensions(fig, ax, line, legend) == pytest.approx(base)


def test_short_dimension_limits_scaling_for_wide_figures():
    fig, ax, line, _ = sine_figure((4.48, 2.20))
    assert ax.xaxis.label.get_fontsize() == 10.5
    assert line.get_linewidth() == 1.1


def test_new_ticks_and_artists_receive_the_current_scale():
    fig, ax, line, _ = sine_figure((4.48, 4.40))
    ax.set_xticks(np.linspace(0, 10, 25))
    added, = ax.plot([0, 10], [0, 0])
    text = ax.text(0.5, 0.5, 'Added', transform=ax.transAxes)
    fig.canvas.draw()
    assert all(tick.label1.get_fontsize() == 19 for tick in ax.xaxis.get_major_ticks())
    assert added.get_linewidth() == pytest.approx(2.2)
    assert text.get_fontsize() == 21
    assert line.get_linewidth() == pytest.approx(2.2)


def test_manual_edits_remain_stable_then_follow_resize():
    fig, ax, line, _ = sine_figure((4.48, 4.40))
    line.set_linewidth(5)
    ax.xaxis.label.set_fontsize(24)
    fig.canvas.draw()
    assert line.get_linewidth() == 5
    assert ax.xaxis.label.get_fontsize() == 24
    fig.set_size_inches(*hdg.figsize())
    fig.canvas.draw()
    assert line.get_linewidth() == 2.5
    assert ax.xaxis.label.get_fontsize() == 12


def test_scatter_and_exports_preserve_sizes_across_dpi_and_backends():
    fig, ax = plt.subplots(figsize=(4.48, 4.40))
    scatter = ax.scatter([0, 1], [0, 1], s=25, linewidths=0.5, label='Data')
    ax.legend()
    fig.canvas.draw()
    assert scatter.get_sizes() == pytest.approx([100])
    assert scatter.get_linewidths() == pytest.approx([1])
    for format in ('png', 'pdf', 'svg'):
        buffer = io.BytesIO()
        fig.savefig(buffer, format=format, dpi=300, bbox_inches='tight')
        assert buffer.tell() > 0
        assert scatter.get_sizes() == pytest.approx([100])
        assert scatter.get_linewidths() == pytest.approx([1])


def test_each_figure_keeps_its_reference_when_style_changes():
    fig, ax = plt.subplots(figsize=(4.48, 4.40))
    ax.set_xlabel('Original')
    hdg.set_style(figure_size=(4.48, 4.40), base_fontsize=12)
    new, other = plt.subplots()
    other.set_xlabel('New')
    fig.canvas.draw()
    new.canvas.draw()
    assert ax.xaxis.label.get_fontsize() == 21
    assert other.xaxis.label.get_fontsize() == 12


def test_reset_restores_matplotlib_and_import_has_no_hooks():
    hdg.reset_style()
    original_init, original_draw = Figure.__init__, Figure.draw
    hdg.set_style()
    hdg.set_style()
    hdg.reset_style()
    assert Figure.__init__ is original_init
    assert Figure.draw is original_draw
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_xlabel('Matplotlib')
    fig.canvas.draw()
    assert ax.xaxis.label.get_fontsize() == plt.rcParams['font.size']


def test_legend_created_after_draw_does_not_scale_copied_handles_twice():
    fig, ax = plt.subplots(figsize=(4.48, 4.40))
    line, = ax.plot([0, 1], [0, 1], marker='o', label='Line')
    scatter = ax.scatter([0, 1], [1, 0], s=25, label='Scatter')
    fig.canvas.draw()
    legend = ax.legend()
    fig.canvas.draw()
    handles = legend.legend_handles
    assert handles[0].get_linewidth() == line.get_linewidth()
    assert handles[0].get_markersize() == pytest.approx(line.get_markersize() * 0.85)
    assert handles[1].get_sizes() == pytest.approx(scatter.get_sizes() * 0.85 ** 2)


def test_export_can_preserve_canvas_dimensions(tmp_path):
    from PIL import Image

    fig, _ = plt.subplots(figsize=(3.36, 3.30))
    path, = hdg.plots.save(tmp_path / 'canvas', fig=fig, formats=('png',),
                            dpi=100, bbox_inches=None)
    with Image.open(path) as image:
        assert image.size == (336, 330)


def test_named_tick_font_sizes_remain_supported():
    fig, ax = plt.subplots(figsize=(4.48, 4.40))
    ax.tick_params(labelsize='large')
    fig.canvas.draw()
    assert ax.xaxis.get_major_ticks()[0].label1.get_fontsize() == pytest.approx(25.2)


def test_pickled_figures_keep_their_reference_and_resize_history():
    import pickle

    fig, ax, line, _ = sine_figure((4.48, 4.40))
    restored = pickle.loads(pickle.dumps(fig))
    restored.canvas.draw()
    assert restored.axes[0].lines[0].get_linewidth() == pytest.approx(2.2)
    restored.set_size_inches(*hdg.figsize())
    restored.canvas.draw()
    assert restored.axes[0].lines[0].get_linewidth() == pytest.approx(1.1)


def test_default_single_axes_and_saved_canvases_match_across_labels():
    from PIL import Image

    positions = []
    for ylabel, values in [('JSD', [.22, .02]), ('WD', [.4, .15])]:
        fig, ax = plt.subplots()
        ax.plot([1, 16], values)
        ax.set(xlabel='Rank', ylabel=ylabel)
        fig.canvas.draw()
        positions.append(ax.get_position().bounds)
        assert ax.get_box_aspect() is None
        image = io.BytesIO()
        fig.savefig(image, format='png', dpi=100)
        image.seek(0)
        with Image.open(image) as bitmap:
            assert bitmap.size == (224, 220)
        # Larger readable type can require different margins for different
        # tick strings; each solved layout must remain stable on redraw.
        fig.canvas.draw()
        assert ax.get_position().bounds == pytest.approx(positions[-1])
        bounds = ax.get_tightbbox(fig.canvas.get_renderer())
        assert bounds.x0 >= 0 and bounds.x1 <= fig.bbox.x1


def test_explicit_tight_export_and_box_aspect_remain_available():
    fig, ax = plt.subplots()
    ax.set_box_aspect(2)
    fig.canvas.draw()
    assert ax.bbox.height / ax.bbox.width == pytest.approx(2)
    output = io.BytesIO()
    fig.savefig(output, format='png', bbox_inches='tight')
    assert output.tell() > 0


def test_panel_count_preserves_typography_and_colourbar_size():
    fig, axes = plt.subplots(3, 5, figsize=(2.24 * 3.5, 2.2 * 2),
                             layout='constrained')
    image = None
    for ax in axes.flat:
        image = ax.imshow([[0, 1], [1, 0]])
        ax.set(xlabel='Z', ylabel='c')
    colourbar = fig.colorbar(image, ax=axes[-1, :])
    colourbar.set_label('Probability')
    fig.canvas.draw()
    assert axes[0, 0].xaxis.label.get_fontsize() == pytest.approx(10.5)
    assert colourbar.ax.yaxis.label.get_fontsize() == pytest.approx(10.5)


def test_long_legend_is_compact_and_redraws_are_stable():
    fig, ax = plt.subplots()
    ax.scatter([0, 1], [0, 1], label='Flamelet Samples')
    ax.scatter([0, 1], [1, 0], label='Selected Samples', marker='x')
    legend = ax.legend(loc='best')
    fig.canvas.draw()
    width = legend.get_window_extent(fig.canvas.get_renderer()).width
    font = legend.get_texts()[0].get_fontsize()
    assert width <= ax.bbox.width * 0.6
    assert 6 <= font < 9.5
    for _ in range(3):
        fig.canvas.draw()
        assert legend.get_texts()[0].get_fontsize() == pytest.approx(font)
        assert legend.get_window_extent(fig.canvas.get_renderer()).width == pytest.approx(width)


def test_tight_layout_measures_the_final_font_sizes():
    fig, ax = plt.subplots(figsize=(4.48, 4.4))
    ax.set(xlabel='Physical time', ylabel='Response')
    fig.tight_layout()
    assert ax.xaxis.label.get_fontsize() == 21
    fig.canvas.draw()
    assert ax.xaxis.label.get_fontsize() == 21
    assert fig.bbox.contains(*ax.xaxis.label.get_window_extent().get_points()[0])


def test_finalize_is_consistent_before_and_after_rendering():
    values = []
    for first_draw in (False, True):
        fig, ax = plt.subplots(figsize=(4.48, 4.4))
        ax.plot([0, 1], [0, 1], label='Data')
        legend = ax.legend()
        if first_draw:
            fig.canvas.draw()
        hdg.finalize(ax, minor_ticks=True)
        fig.canvas.draw()
        values.append((legend.get_frame().get_linewidth(),
                       ax.xaxis.get_minor_ticks()[0].tick1line.get_markersize()))
    assert values[0] == pytest.approx(values[1])


def test_default_colourbar_stays_on_the_fixed_canvas_without_tight_layout():
    fig, ax = plt.subplots(figsize=(2.24 * 1.2, 2.2 * 1.1))
    image = ax.pcolormesh(np.arange(144).reshape(12, 12))
    ax.set(xlabel='Z', ylabel='c')
    ax.set_box_aspect(1)
    colourbar = fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    colourbar.set_label('$P(Z,c)$')
    fig.canvas.draw()
    position = ax.get_position().bounds
    fontsize = ax.xaxis.label.get_fontsize()
    for _ in range(3):
        fig.canvas.draw()
        bounds = colourbar.ax.get_tightbbox(fig.canvas.get_renderer())
        assert bounds.x1 < fig.bbox.x1
        assert ax.bbox.width == pytest.approx(ax.bbox.height)
        assert ax.get_position().bounds == pytest.approx(position)
        assert ax.xaxis.label.get_fontsize() == pytest.approx(fontsize)


def test_inline_notebook_display_preserves_canvas_and_reset_restores_crop(monkeypatch):
    from IPython.core.interactiveshell import InteractiveShell
    from matplotlib_inline.backend_inline import InlineBackend
    from PIL import Image
    from hedgehogs.plots import rendering

    configuration = InlineBackend.instance()
    previous_shell = configuration.shell
    previous = dict(configuration.print_figure_kwargs)
    configuration.shell = InteractiveShell.instance()
    configuration.print_figure_kwargs = {'bbox_inches': 'tight'}
    monkeypatch.setattr(rendering, '_is_jupyter', lambda: True)
    monkeypatch.setattr(plt, 'get_backend', lambda: 'module://matplotlib_inline.backend_inline')
    try:
        hdg.set_style()
        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1])
        data, _ = configuration.shell.display_formatter.format(fig)
        payload = data['image/png']
        if isinstance(payload, str):
            from base64 import b64decode
            payload = b64decode(payload)
        with Image.open(io.BytesIO(payload)) as image:
            assert image.size == (336, 330)
        hdg.reset_style()
        assert configuration.print_figure_kwargs['bbox_inches'] == 'tight'
    finally:
        hdg.reset_style()
        configuration.shell = previous_shell
        configuration.print_figure_kwargs = previous


@pytest.mark.parametrize('font_family', ['serif', 'DejaVu Serif'])
def test_native_rectangular_geometry_is_not_forced_square(font_family):
    plt.rcParams['font.family'] = font_family
    fig, ax = plt.subplots(figsize=(5.6, 4.4))
    assert ax.bbox.width / ax.bbox.height == pytest.approx(5.6 * .72 / (4.4 * .66))
    fig.canvas.draw()
    assert ax.get_box_aspect() is None
    # Wider fonts can trigger label-aware margins. Preserve rectangular
    # geometry and contained decorations, rather than exact initial fractions.
    assert ax.bbox.width > ax.bbox.height
    bounds = ax.get_tightbbox(fig.canvas.get_renderer())
    assert bounds.x0 >= 0 and bounds.y0 >= 0
    assert bounds.x1 <= fig.bbox.x1 and bounds.y1 <= fig.bbox.y1
    position = ax.get_position().bounds
    fig.canvas.draw()
    assert ax.get_position().bounds == pytest.approx(position)


def test_scatter_and_line_legend_handles_share_the_text_centre():
    fig, ax = plt.subplots(figsize=(4.48, 4.4))
    ax.plot([0, 1], [0, 1], label='Sine Wave')
    ax.scatter([0, 1], [1, 0], label='Sine Wave')
    legend = ax.legend()
    fig.canvas.draw()
    line, scatter = legend.legend_handles
    assert line.get_ydata()[0] == pytest.approx(scatter.get_offsets()[0, 1])


def test_explicit_tight_colourbar_export_keeps_labels_visible():
    fig, ax = plt.subplots(figsize=(2.24 * 1.2, 2.2 * 1.1))
    image = ax.pcolormesh(np.arange(144).reshape(12, 12), rasterized=True)
    ax.set(xlabel='$Z$', ylabel='$c$')
    ax.set_box_aspect(1)
    colourbar = fig.colorbar(image, ax=ax, fraction=.046, pad=.04)
    colourbar.set_label('$P(Z,c)$')
    fig.tight_layout()
    fig.canvas.draw()
    bounds = colourbar.ax.get_tightbbox(fig.canvas.get_renderer())
    assert bounds.x1 < fig.bbox.x1
    for format in ('pdf', 'svg'):
        fig.savefig(io.BytesIO(), format=format, bbox_inches='tight', dpi=600)


def test_colourbar_fitting_does_not_force_rectangular_axes_square():
    fig, ax = plt.subplots(figsize=(4, 2.5))
    image = ax.pcolormesh(np.arange(144).reshape(12, 12))
    colourbar = fig.colorbar(image, ax=ax)
    colourbar.set_label('Density')
    ax.apply_aspect()
    ratio = ax.bbox.width / ax.bbox.height
    fig.canvas.draw()
    assert ax.get_box_aspect() is None
    assert ax.bbox.width > ax.bbox.height
    assert ax.bbox.width / ax.bbox.height != pytest.approx(1)


def test_explicit_canvas_bbox_is_fitted_before_the_first_save():
    from PIL import Image

    fig, ax = plt.subplots(figsize=(3.36, 3.36))
    ax.scatter([0, .02], [400, 2200], s=10)
    ax.set(xlabel='$x$ [m]', ylabel=r'$\langle T\rangle$ [K]')
    ax.set_box_aspect(1)
    fig.subplots_adjust(left=.22, right=.97, bottom=.18, top=.96)
    image = io.BytesIO()
    # No canvas.draw() before this save: that would conceal the original bug.
    fig.savefig(image, format='png', bbox_inches=fig.bbox_inches, dpi=160)
    image.seek(0)
    with Image.open(image) as bitmap:
        pixels = np.asarray(bitmap.convert('RGB'))
        assert np.all(pixels[:, :3] == 255)
        assert np.all(pixels[-3:, :] == 255)
    bounds = ax.get_tightbbox(fig.canvas.get_renderer())
    assert bounds.x0 > fig.bbox.x0


def test_colourbar_does_not_shrink_typography_or_leave_excessive_space():
    fig, ax = plt.subplots(figsize=(2.24 * 1.2, 2.2 * 1.1))
    image = ax.pcolormesh(np.linspace(0, 1, 144).reshape(12, 12))
    ax.set(xlabel='x', ylabel='y')
    ax.set_box_aspect(1)
    colourbar = fig.colorbar(image, ax=ax, fraction=.046, pad=.04)
    colourbar.set_label('Density')
    fig.canvas.draw()
    assert ax.xaxis.label.get_fontsize() == pytest.approx(10.5 * 1.1)
    assert ax.bbox.width * ax.bbox.height / (fig.bbox.width * fig.bbox.height) > .20


@pytest.mark.parametrize('rows, columns, size', [(2, 2, (3.36, 3.3)), (3, 2, (4.48, 5.5))])
def test_grid_keeps_explicit_annotation_sizes_and_base_strokes(rows, columns, size):
    fig, axes = plt.subplots(rows, columns, figsize=size, layout='constrained')
    line, = axes.flat[0].plot([0, 1], [0, 1])
    text = axes.flat[0].text(.5, .5, 'Annotation', fontsize=9)
    fig.canvas.draw()
    assert text.get_fontsize() == 9
    assert line.get_linewidth() == pytest.approx(1.1)
    for axis in axes.flat:
        assert axis.xaxis.get_major_ticks()[0].label1.get_fontsize() == 9.5


def test_probability_field_y_label_fits_after_first_600_dpi_export():
    fig, ax = plt.subplots(figsize=(2.24 * 1.2, 2.2 * 1.1))
    coordinates = np.linspace(0, 1, 80)
    X, Y = np.meshgrid(coordinates, coordinates)
    field = np.exp(-((X - .4)**2 + (Y - .6)**2) / .025)
    image = ax.pcolormesh(X, Y, field, shading='auto', rasterized=True)
    ax.set(xlabel='x', ylabel='y')
    ax.set_box_aspect(1)
    colourbar = fig.colorbar(image, ax=ax, fraction=.046, pad=.04)
    colourbar.set_label('Density')
    fig.savefig(io.BytesIO(), format='pdf', dpi=600)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    assert ax.yaxis.label.get_window_extent(renderer).x0 > 0
    assert colourbar.ax.yaxis.label.get_window_extent(renderer).x1 < fig.bbox.x1


@pytest.mark.parametrize('scale', [.7, 1, 1.5, 2])
def test_plain_subplots_automatically_separate_labels(scale):
    fig, axes = plt.subplots(2, 2, figsize=(4.48 * scale, 4.4 * scale))
    for index, ax in enumerate(axes.flat):
        ax.plot([0, 1], [0, 1], label='Response')
        ax.set(title=f'Panel {index + 1}', xlabel='Physical time (s)', ylabel='Response')
        ax.legend(loc='best')
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    boxes = [ax.get_tightbbox(renderer) for ax in axes.flat]
    for box in boxes:
        assert box.x0 >= 0 and box.y0 >= 0
        assert box.x1 <= fig.bbox.x1 and box.y1 <= fig.bbox.y1
    assert boxes[0].x1 <= boxes[1].x0
    assert boxes[2].y1 <= boxes[0].y0
    assert all(ax.xaxis.label.get_fontsize() == 10.5 for ax in axes.flat)
    positions = [ax.get_position().bounds for ax in axes.flat]
    fig.canvas.draw()
    for ax, position in zip(axes.flat, positions):
        assert ax.get_position().bounds == pytest.approx(position)


def test_automatic_grid_leaves_space_for_a_figure_legend():
    fig, axes = plt.subplots(2, 2, figsize=(4.48, 4.4))
    for ax in axes.flat:
        ax.plot([0, 1], [0, 1], label='Baseline')
        ax.set(xlabel='Physical time', ylabel='Response')
    handles, labels = axes[0, 0].get_legend_handles_labels()
    legend = fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(.5, .01))
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    bounds = legend.get_window_extent(renderer)
    assert all(ax.get_tightbbox(renderer).y0 >= bounds.y1 for ax in axes[-1, :])


def test_explicit_grid_layout_engine_is_retained():
    fig, axes = plt.subplots(2, 2, figsize=(4.48, 4.4), layout='constrained')
    engine = fig.get_layout_engine()
    for ax in axes.flat:
        ax.set(xlabel='Time', ylabel='Response')
    fig.canvas.draw()
    assert fig.get_layout_engine() is engine


def test_shared_colourbars_use_native_constraints_before_creation():
    fig, axes = plt.subplots(3, 5, figsize=(7.84 * .7, 4.4 * .7))
    bars = []
    for row in axes:
        for ax in row:
            image = ax.imshow([[0, 1], [1, 0]])
            ax.set_box_aspect(1)
        bar = fig.colorbar(image, ax=row, pad=.01)
        bar.set_label('Density')
        bars.append(bar)
    fig.canvas.draw()
    assert fig.get_constrained_layout()
    for row, bar in zip(axes, bars):
        assert bar.ax.bbox.x0 >= row[-1].bbox.x1
        assert bar.ax.get_tightbbox(fig.canvas.get_renderer()).x1 <= fig.bbox.x1
        assert row[0].yaxis.label.get_fontsize() == 10.5


@pytest.mark.parametrize('layout', [None, 'tight', 'constrained'])
@pytest.mark.parametrize('location', ['left', 'center', 'right'])
def test_toy_title_fits_fixed_canvas_and_recovers_after_resize(layout, location):
    fig, ax = plt.subplots(figsize=(3.36, 3.3), layout=layout)
    scatter = ax.scatter([0, 5, 10], [0, 30, 100], label='Training Data')
    line, = ax.plot([0, 10], [-10, 100], label='Fitted Line (Numpy)')
    title = ax.set_title('Toy Example: Linear Fit to Quadratic Data', loc=location)
    ax.set(xlabel='X', ylabel='y')
    ax.legend()
    if layout is None:
        fig.tight_layout()
    fig.savefig(io.BytesIO(), format='png', dpi=300, transparent=True)
    for _ in range(3):
        fig.canvas.draw()
        bounds = title.get_window_extent(fig.canvas.get_renderer())
        assert bounds.x0 >= 0
        assert bounds.x1 <= fig.bbox.x1
        assert scatter.get_sizes() == pytest.approx([36])
        assert line.get_linewidth() == pytest.approx(1.65)
    fitted_size = title.get_fontsize()
    title.set_text('Short title')
    fig.canvas.draw()
    assert title.get_fontsize() == pytest.approx(17.25)
    assert title.get_fontsize() > fitted_size
    title.set_text('Toy Example: Linear Fit to Quadratic Data')
    fig.set_size_inches(6.72, 3.3)
    fig.canvas.draw()
    # A wider canvas permits a larger title; left/right anchors and wider
    # fallback glyphs can still require fitting below the configured size.
    assert fitted_size < title.get_fontsize() <= 17.25
    bounds = title.get_window_extent(fig.canvas.get_renderer())
    assert bounds.x0 >= 0 and bounds.x1 <= fig.bbox.x1


def test_explicit_scatter_sizes_are_preserved_relative_to_reference():
    fig, ax = plt.subplots(figsize=(3.36, 3.3))
    scatter = ax.scatter([0, 1], [0, 1], s=[2, 20])
    fig.canvas.draw()
    assert scatter.get_sizes() == pytest.approx([4.5, 45])


def test_long_grid_titles_fit_their_panels_and_exports_remain_stable():
    fig, axes = plt.subplots(2, 2, figsize=(4.48, 4.4), layout='constrained')
    for ax in axes.flat:
        ax.set(title='A particularly long scientific panel title', xlabel='X', ylabel='y')
    fig.canvas.draw()
    sizes = [ax.title.get_fontsize() for ax in axes.flat]
    for format in ('png', 'pdf', 'svg'):
        fig.savefig(io.BytesIO(), format=format, dpi=300)
        fig.canvas.draw()
        for ax, size in zip(axes.flat, sizes):
            bounds = ax.title.get_window_extent(fig.canvas.get_renderer())
            assert bounds.x0 >= ax.bbox.x0 - 1
            assert bounds.x1 <= ax.bbox.x1 + 1
            assert ax.title.get_fontsize() == pytest.approx(size, abs=.1)


@pytest.mark.parametrize('marker', ['o', 'X', 's', 'P'])
def test_scatter_colour_does_not_override_default_black_outline(marker):
    from matplotlib.colors import to_rgba
    fig, ax = plt.subplots()
    points = ax.scatter([0], [0], color='red', marker=marker)
    fig.canvas.draw()
    assert points.get_edgecolors()[0] == pytest.approx(to_rgba('black'))
    assert points.get_facecolors()[0] == pytest.approx(to_rgba('red'))


def test_scatter_explicit_outlines_and_unfilled_markers_are_preserved():
    from matplotlib.colors import to_rgba
    fig, ax = plt.subplots()
    points = ax.scatter([0], [0], color='red', edgecolor='blue')
    assert points.get_edgecolors()[0] == pytest.approx(to_rgba('blue'))
    points = ax.scatter([0], [0], color='red', edgecolors='none')
    assert points.get_edgecolors().size == 0
    points = ax.scatter([0], [0], color='red', marker='x')
    assert points.get_edgecolors()[0] == pytest.approx(to_rgba('red'))


def test_reset_restores_native_scatter_method():
    from hedgehogs.plots import rendering
    original = rendering._original_scatter
    hdg.set_style()
    hdg.reset_style()
    assert plt.Axes.scatter is original


def test_large_explicit_scatter_and_post_draw_edits_are_never_capped():
    fig, ax = plt.subplots()
    points = ax.scatter([0], [0], s=10000, linewidths=3, edgecolors='purple')
    fig.canvas.draw()
    assert points.get_sizes() == pytest.approx([10000])
    assert points.get_linewidths() == pytest.approx([3])
    points.set_sizes([25000])
    ax.spines['left'].set_linewidth(4)
    for _ in range(3):
        fig.canvas.draw()
        assert points.get_sizes() == pytest.approx([25000])
        assert ax.spines['left'].get_linewidth() == 4


@pytest.mark.parametrize('scale', [.75, 1., 1.5, 2.])
def test_fallback_font_legend_fitting_is_bounded_and_stable(scale):
    plt.rcParams['font.family'] = 'DejaVu Serif'
    fig, ax = plt.subplots(figsize=tuple(value * scale for value in hdg.figsize()))
    ax.plot([0, 1], [0, 1], label='Sine Wave')
    ax.set(xlabel='X-axis', ylabel='Y-axis')
    legend = ax.legend()
    fig.canvas.draw()
    size = legend.get_texts()[0].get_fontsize()
    assert 6 * scale <= size <= 9.5 * scale
    bounds = legend.get_window_extent(fig.canvas.get_renderer())
    assert bounds.width <= ax.bbox.width * .6 + 2
    for _ in range(3):
        fig.canvas.draw()
        assert legend.get_texts()[0].get_fontsize() == pytest.approx(size)
        assert legend.get_window_extent(fig.canvas.get_renderer()).bounds == pytest.approx(bounds.bounds)


@pytest.mark.parametrize('first_draw', [False, True])
def test_grouped_bar_legend_and_bar_labels_render_without_container_cache_errors(first_draw):
    fig, ax = plt.subplots(figsize=(6.72, 4.4))
    x = np.arange(6)
    first = ax.bar(x - .175, [.79, .04, .65, .11, .51, 1.16], .35, label='Polars')
    second = ax.bar(x + .175, [16.03, .5, 9.48, 4.98, 11.91, 14.12], .35, label='Pandas')
    ax.bar_label(first, fmt='%.2f', padding=3)
    ax.bar_label(second, fmt='%.2f', padding=3)
    ax.set_xticks(x, ['read csv', 'aggregations', 'window functions', 'inner join', 'left join', 'full join'])
    ax.set(ylabel='Time [s]', title='Polars vs Pandas - Speed Comparison')
    if first_draw:
        fig.canvas.draw()
    legend = ax.legend()
    fig.tight_layout()
    fig.canvas.draw()
    handles = getattr(legend, 'legend_handles', None)
    if handles is None:
        handles = legend.legendHandles
    assert handles[0].get_linewidth() == pytest.approx(first.patches[0].get_linewidth())
    fontsize = legend.get_texts()[0].get_fontsize()
    for format in ('png', 'pdf', 'svg'):
        fig.savefig(io.BytesIO(), format=format)
        fig.canvas.draw()
        assert legend.get_texts()[0].get_fontsize() == pytest.approx(fontsize)
        assert handles[0].get_linewidth() == pytest.approx(first.patches[0].get_linewidth())


@pytest.mark.parametrize('kind', ['errorbar', 'stem'])
def test_other_container_legends_render_and_redraw(kind):
    fig, ax = plt.subplots(figsize=(4.48, 4.4))
    if kind == 'errorbar':
        ax.errorbar([0, 1], [1, 2], yerr=.1, label='Data')
    else:
        ax.stem([0, 1], [1, 2], label='Data')
    fig.canvas.draw()
    legend = ax.legend()
    fig.tight_layout()
    for _ in range(3):
        fig.canvas.draw()
    assert legend.get_texts()[0].get_text() == 'Data'
