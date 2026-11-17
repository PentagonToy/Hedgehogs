import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pytest
import hedgehogs as hdg


@pytest.fixture(autouse=True)
def clean():
    hdg.set_style()
    yield
    plt.close('all')
    hdg.reset_style()


@pytest.mark.parametrize('size', [(7, 3), (3, 7), (4, 4)])
def test_square_fits_allocated_space_preserves_canvas_and_limits(size, tmp_path):
    fig, ax = plt.subplots(figsize=size)
    ax.plot([0, 10], [0, 1])
    ax.set(xlim=(-1, 11), ylim=(-.1, 1.1), xlabel='Long axis title', ylabel='Value')
    hdg.plots.square()
    fig.canvas.draw()
    allocated = ax.get_position(original=True)
    capacity = min(allocated.width * size[0], allocated.height * size[1])
    assert ax.bbox.width == pytest.approx(ax.bbox.height)
    assert ax.bbox.width / fig.dpi == pytest.approx(capacity)
    hdg.plots.show(block=False)
    assert ax.bbox.width == pytest.approx(ax.bbox.height)
    assert fig.get_size_inches() == pytest.approx(size)
    assert ax.get_xlim() == pytest.approx((-1, 11))
    assert ax.get_ylim() == pytest.approx((-.1, 1.1))
    fig.savefig(tmp_path / 'square.svg')
    fig.set_size_inches(size[::-1])
    hdg.plots.show(block=False)
    assert ax.bbox.width == pytest.approx(ax.bbox.height)
    hdg.plots.square(False)
    assert ax.get_box_aspect() is None


def test_grid_with_colourbar_and_constrained_layout(tmp_path):
    fig, axes = plt.subplots(1, 2, figsize=(8, 4), layout='constrained')
    image = axes[0].imshow(np.arange(12).reshape(3, 4), aspect='auto')
    bar = fig.colorbar(image, ax=axes[0])
    axes[1].plot([0, 10], [0, 1])
    hdg.plots.square(ax=axes)
    hdg.plots.show(block=False)
    for ax in axes:
        assert ax.bbox.width == pytest.approx(ax.bbox.height)
    assert bar.ax.get_box_aspect() != 1
    assert (bar.ax.bbox.y0, bar.ax.bbox.y1) == pytest.approx((axes[0].bbox.y0, axes[0].bbox.y1))
    fig.savefig(tmp_path / 'grid.pdf')
    hdg.plots.square(False, ax=axes)
    assert all(ax.get_box_aspect() is None for ax in axes)


@pytest.mark.parametrize('extension', ['png', 'svg', 'pdf'])
def test_square_title_stays_inside_tight_export(extension, tmp_path):
    width, height = hdg.figsize(name='science', column='single')
    fig, ax = plt.subplots(figsize=(width * 1.5, height * 1.5))
    ax.scatter([8, 10, 12, 14], [4, 7, 10, 13], label='Red')
    ax.scatter([9, 11, 13, 15], [5, 6, 8, 9], label='White')
    ax.set(title='Wine Dataset: Original Features', xlabel='alcohol', ylabel='fixed acidity')
    ax.legend()
    fig.tight_layout()
    hdg.plots.square()
    cropped_bounds = []

    def inspect(event):
        if fig.transFigure._boxout is not fig.bbox:
            cropped_bounds.append((ax.title.get_window_extent(event.renderer).frozen(), fig.bbox.frozen()))

    fig.canvas.mpl_connect('draw_event', inspect)
    hdg.plots.save(tmp_path / f'wine.{extension}', dpi=300, transparent=True)
    assert cropped_bounds
    for title, canvas in cropped_bounds:
        assert title.x0 >= canvas.x0 - 1
        assert title.x1 <= canvas.x1 + 1
        assert title.y1 <= canvas.y1 + 1
    hdg.plots.show(block=False)
    assert ax.bbox.width == pytest.approx(ax.bbox.height)


def test_square_defaults_to_current_figure_panels_and_skips_colourbars():
    _, other = plt.subplots()
    fig, axes = plt.subplots(2, 2, figsize=(6, 5), sharex=True, sharey=True)
    for ax in axes.flat:
        points = ax.scatter([0, 1], [0, 1], c=[0, 1])
    bar = fig.colorbar(points, ax=axes.ravel().tolist())
    original_bar_aspect = bar.ax.get_box_aspect()
    plt.sca(bar.ax)
    hdg.plots.square()
    fig.canvas.draw()
    for ax in axes.flat:
        assert ax.get_box_aspect() == 1
        assert ax.bbox.width == pytest.approx(ax.bbox.height)
    assert bar.ax.get_box_aspect() == original_bar_aspect
    assert other.get_box_aspect() is None
    hdg.plots.square(False)
    assert all(ax.get_box_aspect() is None for ax in axes.flat)
    assert bar.ax.get_box_aspect() == original_bar_aspect


def test_square_explicit_selection_leaves_other_panels_unchanged():
    _, axes = plt.subplots(2, 2)
    hdg.plots.square(ax=axes[0])
    assert all(ax.get_box_aspect() == 1 for ax in axes[0])
    assert all(ax.get_box_aspect() is None for ax in axes[1])
    hdg.plots.square(False, ax=axes[0, 0])
    assert axes[0, 0].get_box_aspect() is None
    assert axes[0, 1].get_box_aspect() == 1


def test_invalid_flag_does_not_create_axes():
    with pytest.raises(TypeError):hdg.plots.square('yes')
    assert not plt.get_fignums()


@pytest.mark.parametrize('scale', [1, 1.5])
def test_square_dependence_colourbar_matches_parent_after_finish_resize_export(scale, tmp_path):
    fig = plt.figure(figsize=(2.24 * scale, 2.2))
    values = np.array([[1, 2], [2, 3], [3, 4]])
    ax = hdg.plots.dependence_plot(0, values, [[10, 0], [20, 1], [30, 0]], color_by=1)
    hdg.plots.square()
    bar = fig.axes[1]
    hdg.plots.show(block=False)
    assert (bar.bbox.y0, bar.bbox.y1) == pytest.approx((ax.bbox.y0, ax.bbox.y1))
    for ext in ['png', 'pdf', 'svg']:
        fig.savefig(tmp_path / f'colourbar.{ext}', dpi=180)
    hdg.plots.show(block=False)
    assert (bar.bbox.y0, bar.bbox.y1) == pytest.approx((ax.bbox.y0, ax.bbox.y1))
    fig.set_size_inches(4, 3)
    hdg.plots.show(block=False)
    assert (bar.bbox.y0, bar.bbox.y1) == pytest.approx((ax.bbox.y0, ax.bbox.y1))


def test_explicit_shrink_and_custom_colourbar_axes_keep_native_locator():
    fig, ax = plt.subplots(figsize=(4, 3))
    image = ax.imshow(np.arange(9).reshape(3, 3))
    bar = fig.colorbar(image, ax=ax, shrink=.5)
    assert type(bar.ax.get_axes_locator()).__name__ == '_ColorbarAxesLocator'
    fig2, ax2 = plt.subplots(figsize=(4, 3))
    image2 = ax2.imshow(np.arange(9).reshape(3, 3))
    cax = fig2.add_axes([.85, .15, .03, .6])
    custom = fig2.colorbar(image2, cax=cax)
    assert type(custom.ax.get_axes_locator()).__name__ == '_ColorbarAxesLocator'


def test_shared_row_colourbars_match_plotting_boxes_on_show_and_save(tmp_path):
    fig, axes = plt.subplots(2, 3, figsize=(11.2, 3.3), layout='constrained')
    bars = []
    for row in axes:
        for ax in row:
            image = ax.pcolormesh(np.arange(66).reshape(3, 22))
            ax.set_aspect('equal')
        bars.append(fig.colorbar(image, ax=row))

    draws = []

    def inspect(event):
        for row, bar in zip(axes, bars):
            width_pt = bar.ax.bbox.width / event.renderer.points_to_pixels(1)
            assert width_pt == pytest.approx(5)
            assert bar.outline.get_linewidth() == pytest.approx(1.4)
            for ax in row:
                assert (bar.ax.bbox.y0, bar.ax.bbox.y1) == pytest.approx((ax.bbox.y0, ax.bbox.y1))
                assert ax.spines['left'].get_linewidth() == pytest.approx(1.4)
        draws.append(event.canvas)

    fig.canvas.mpl_connect('draw_event', inspect)
    hdg.plots.show(block=False)
    assert draws
    # Older Matplotlib calls the locator without a renderer during tight export
    for bar in bars:
        locator = bar.ax.get_axes_locator()
        renderer = fig.canvas.get_renderer()
        bar.ax.apply_aspect(locator(bar.ax, renderer))
        expected = bar.ax.get_position().bounds
        bar.ax.apply_aspect(locator(bar.ax, None))
        assert bar.ax.get_position().bounds == pytest.approx(expected)
    fig.set_size_inches(8.4, 2.475)
    draws.clear()
    hdg.plots.save(tmp_path / 'shared.pdf', fig=fig)
    assert draws


def test_shared_colourbar_respects_explicit_aspect():
    fig, axes = plt.subplots(1, 2, figsize=(6, 3), layout='constrained')
    for ax in axes:
        image = ax.imshow(np.zeros((2, 8)))
    bar = fig.colorbar(image, ax=axes, aspect=30)

    fig.canvas.draw()
    assert bar.ax.bbox.width == pytest.approx(bar.ax.bbox.height / 30)
    assert bar.ax.bbox.height == pytest.approx(axes[0].bbox.height)


@pytest.mark.parametrize('case', ['different heights', 'multiple rows', 'shrink'])
def test_shared_colourbar_keeps_native_height_without_aligned_default_parents(case):
    shape = (2, 1) if case == 'multiple rows' else (1, 2)
    fig, axes = plt.subplots(*shape, figsize=(6, 6), layout='constrained')
    for ax in axes:
        image = ax.imshow(np.zeros((2, 8)))
    if case == 'different heights':
        axes[0].set_ylim(0, 1)
    options = {'shrink': .5} if case == 'shrink' else {}
    bar = fig.colorbar(image, ax=axes, **options)

    fig.canvas.draw()
    assert bar.ax.bbox.height > max(ax.bbox.height for ax in axes)


def test_colourbar_locator_stays_retired_after_reset_and_reenable():
    fig, ax = plt.subplots(figsize=(2.24, 2.2))
    ax.set_box_aspect(1)
    image = ax.scatter([0, 1], [0, 1], c=[0, 1])
    bar = fig.colorbar(image, ax=ax)
    locator = bar.ax.get_axes_locator()
    renderer = fig.canvas.get_renderer()
    hdg.reset_style()
    assert locator(bar.ax, renderer).bounds == pytest.approx(locator.original(bar.ax, renderer).bounds)
    hdg.set_style()
    assert locator(bar.ax, renderer).bounds == pytest.approx(locator.original(bar.ax, renderer).bounds)


def test_top_colourbar_tracks_fixed_aspect_panel_on_export(tmp_path):
    fig, ax = plt.subplots(figsize=(6, 4), layout='constrained')
    image = ax.imshow(np.arange(24).reshape(8, 3))
    bar = fig.colorbar(image, ax=ax, location='top')
    widths = []

    def inspect(event):
        assert (bar.ax.bbox.x0, bar.ax.bbox.x1) == pytest.approx((ax.bbox.x0, ax.bbox.x1))
        widths.append(bar.ax.bbox.height / event.renderer.points_to_pixels(1))

    fig.canvas.mpl_connect('draw_event', inspect)
    hdg.plots.save(tmp_path / 'top.pdf', fig=fig)
    fig.set_size_inches(4, 3)
    fig.canvas.draw()

    assert widths
    assert min(widths) >= 5 - 1e-6


@pytest.mark.parametrize('layout', ['constrained', 'compressed', 'tight', 'none'])
@pytest.mark.filterwarnings('error:This figure includes Axes that are not compatible')
def test_finish_compacts_fixed_rows_with_shared_colourbars(layout, tmp_path):
    from hedgehogs.plots.presentation import prepare

    plt.rcParams['font.family'] = 'DejaVu Serif'
    initial_size = (11.2, 6)
    fig, axes = plt.subplots(2, 3, figsize=initial_size, layout=layout)
    bars = []
    for row, label in zip(axes, ['Temperature [K]', 'Long reaction rate label [1/s]'], strict=True):
        for ax in row:
            image = ax.pcolormesh(np.arange(66).reshape(3, 22), shading='auto')
            ax.set_aspect('equal')
            ax.set(xlabel='Streamwise distance [mm]', ylabel='Span [mm]')
        bars.append(fig.colorbar(image, ax=row, label=label))
    fig.suptitle('Fixed-aspect comparison')
    limits = [(ax.get_xlim(), ax.get_ylim()) for ax in axes.flat]

    prepare(fig)
    size = tuple(fig.get_size_inches())
    assert size[0] == pytest.approx(initial_size[0])
    assert size[1] < initial_size[1]
    assert [(ax.get_xlim(), ax.get_ylim()) for ax in axes.flat] == limits

    renderer = fig.canvas.get_renderer()
    bounds = []
    for row, bar in zip(axes, bars, strict=True):
        row_axes = [*row, bar.ax]
        labels = [axis.label for ax in row_axes for axis in (ax.xaxis, ax.yaxis) if axis.label.get_text()]
        bounds.append(matplotlib.transforms.Bbox.union([
            artist.get_tightbbox(renderer) for artist in [*row_axes, *labels]
        ]))
    assert (bounds[0].y0 - bounds[1].y1) / renderer.points_to_pixels(1) == pytest.approx(6, abs=.2)
    assert bounds[1].y0 / renderer.points_to_pixels(1) == pytest.approx(4, abs=.2)
    assert all(0 <= box.x0 <= box.x1 <= fig.bbox.width for box in bounds)
    for row, bar in zip(axes, bars, strict=True):
        for ax in row:
            assert bar.ax.bbox.intervaly == pytest.approx(ax.bbox.intervaly)
            assert ax.bbox.width / ax.bbox.height == pytest.approx(22 / 3)

    hdg.plots.save(tmp_path / 'compact.pdf', fig=fig, bbox_inches=None)
    prepare(fig)
    assert fig.get_size_inches() == pytest.approx(size)

    if layout == 'constrained':
        fig.suptitle('Fixed-aspect comparison\nLonger figure title')
        prepare(fig)
        edited = tuple(fig.get_size_inches())
        assert size[1] < edited[1] <= initial_size[1]
        prepare(fig)
        assert fig.get_size_inches() == pytest.approx(edited)


def test_shared_row_colourbar_uses_a_closer_gap_and_preserves_custom_spacing():
    from hedgehogs.plots.presentation import prepare

    def measure(explicit):
        fig, axes = plt.subplots(1, 3, figsize=(11.2, 2.1), layout='constrained')
        engine = fig.get_layout_engine()
        for ax in axes:
            image = ax.imshow(np.arange(66).reshape(3, 22))
        if explicit:
            engine.set(w_pad=3 / 72)
        bar = fig.colorbar(image, ax=axes, **({'pad': .05} if explicit else {}))
        prepare(fig)

        renderer = fig.canvas.get_renderer()
        points = renderer.points_to_pixels(1)
        panel_gap = (axes[2].bbox.x0 - axes[1].bbox.x1) / points
        bar_gap = (bar.ax.bbox.x0 - axes[-1].bbox.x1) / points
        assert axes[-1].get_tightbbox(renderer).x1 < bar.ax.bbox.x0
        assert engine.get()['w_pad'] == pytest.approx((3 if explicit else 5) / 72)

        return panel_gap, bar_gap

    default_panel, default_bar = measure(False)
    custom_panel, custom_bar = measure(True)
    assert default_bar < custom_bar
    assert default_panel > custom_panel


@pytest.mark.parametrize('dimension, size', [('width', (4.5, 2.4)), ('height', (9, 2.4))])
def test_fixed_rows_report_labels_that_cannot_fit_without_enlarging(dimension, size, monkeypatch):
    from hedgehogs.plots.presentation import prepare

    if dimension == 'height':
        get_tightbbox = matplotlib.axis.Axis.get_tightbbox

        def layout_bbox(axis, renderer=None, **kwargs):
            return get_tightbbox(axis, renderer, for_layout_only=True)

        # Matplotlib 3.10 measures axes with layout-only label bounds
        monkeypatch.setattr(matplotlib.axis.Axis, 'get_tightbbox', layout_bbox)

    fig, axes = plt.subplots(2, 3, figsize=size, layout='compressed')
    label = 'Long normalised field label [units]'
    for row in axes:
        for ax in row:
            image = ax.imshow(np.zeros((2, 16)))
            ax.set_xlabel('Streamwise coordinate [mm]')
        bar = fig.colorbar(image, ax=row, label=label)
        if dimension == 'height':
            bar.set_label(f'{label} ({label})', fontfamily='DejaVu Serif', fontsize=16)

    with pytest.warns(UserWarning, match=f'need more {dimension}'):
        prepare(fig)

    if dimension == 'height':
        renderer = fig.canvas.get_renderer()
        assert bar.ax.yaxis.label.get_window_extent(renderer).height > fig.bbox.height
    assert fig.get_size_inches() == pytest.approx(size)
