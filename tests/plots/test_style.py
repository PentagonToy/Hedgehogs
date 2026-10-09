from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest

import hedgehogs as hdg


def test_default_style_uses_science_single_column():
    hdg.set_style()
    assert tuple(plt.rcParams["figure.figsize"]) == hdg.figsize("science", "single")
    assert plt.rcParams["font.size"] == 10.5
    assert plt.rcParams["axes.labelsize"] == 10.5
    assert plt.rcParams["xtick.labelsize"] == 9.5
    assert plt.rcParams["legend.fontsize"] == 9.5
    assert plt.rcParams["lines.markersize"] == pytest.approx(16 ** 0.5)
    assert plt.rcParams["axes.linewidth"] == .9
    assert plt.rcParams["lines.linewidth"] == 1.1
    assert plt.rcParams["axes.xmargin"] == 0.05
    assert plt.rcParams["axes.ymargin"] == 0.05
    hdg.reset_style()


def test_custom_style_can_opt_in_to_width_scaling():
    hdg.set_style(base_fontsize=10.0, figure_size=(6.0, 4.0), auto_scale=True)
    assert plt.rcParams["font.size"] == 10.0
    hdg.set_style(base_fontsize=10.0, figure_size=(3.0, 2.0), auto_scale=True)
    assert plt.rcParams["font.size"] < 10.0
    hdg.reset_style()


def test_markers_follow_typography_without_becoming_too_small():
    hdg.set_style(base_fontsize=12.0, auto_scale=False)
    assert plt.rcParams["lines.markersize"] == pytest.approx(12 * 16 ** 0.5 / 10.5)
    hdg.set_style(base_fontsize=3.0, auto_scale=False)
    assert plt.rcParams["lines.markersize"] == 2.5
    hdg.reset_style()


def test_default_margin_keeps_boundary_markers_inside_axes():
    hdg.set_style()
    fig, ax = hdg.subplots()
    line, = ax.plot([0.0, 1.0], [0.0, 1.0], marker="o")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    marker_bounds = line.get_window_extent(renderer)
    axes_bounds = ax.get_window_extent(renderer)
    assert marker_bounds.x0 >= axes_bounds.x0
    assert marker_bounds.y0 >= axes_bounds.y0
    assert marker_bounds.x1 <= axes_bounds.x1
    assert marker_bounds.y1 <= axes_bounds.y1
    plt.close(fig)
    hdg.reset_style()


def test_subplots_creates_single_axes():
    fig, ax = hdg.subplots(figsize=(4, 3))
    ax.plot([0, 1], [0, 1])
    assert fig.axes == [ax]
    plt.close(fig)


def test_subplots_supports_gridspec():
    fig, axes = hdg.subplots(
        nrows=2,
        ncols=2,
        gridspec_kw={"width_ratios": [2, 1]},
    )
    assert axes.shape == (2, 2)
    assert len(fig.axes) == 4
    plt.close(fig)


def test_subplots_accepts_width_shortcut():
    fig, axes = hdg.subplots(1, 2, widths=[2, 1])
    assert len(axes) == 2
    assert axes[0].get_position().width > axes[1].get_position().width
    plt.close(fig)


def test_subplots_supports_constrained_layout():
    fig, axes = hdg.subplots(
        ncols=2,
        layout="constrained",
    )
    assert len(axes) == 2
    assert fig.get_constrained_layout()
    plt.close(fig)


def test_subplots_forwards_shared_axis_configuration():
    fig, axes = hdg.subplots(1, 2, sharex=True, sharey="all")

    assert axes[0].get_shared_x_axes().joined(axes[0], axes[1])
    assert axes[0].get_shared_y_axes().joined(axes[0], axes[1])
    plt.close(fig)


@pytest.mark.parametrize("journal", ["nature", "science", "ieee", "aps"])
def test_journal_presets_apply(journal):
    options = hdg.set_journal_style(journal)
    assert tuple(plt.rcParams["figure.figsize"]) == options["figure_size"]
    assert plt.rcParams["font.size"] == options["base_fontsize"]
    hdg.reset_style()


def test_journal_typography_is_stable_across_column_widths():
    single = hdg.set_journal_style("science", column="single")
    single_fontsize = plt.rcParams["font.size"]
    double = hdg.set_journal_style("science", column="double")
    assert single["base_fontsize"] == double["base_fontsize"]
    assert plt.rcParams["font.size"] == single_fontsize
    hdg.reset_style()


def test_save_supports_multiple_formats(tmp_path):
    fig, ax = plt.subplots()
    ax.plot([0, 1], [1, 0])
    outputs = hdg.plots.save(tmp_path / "figure", fig=fig, formats=("png", "pdf", "svg"))
    assert outputs == tuple(Path(tmp_path / f"figure.{suffix}") for suffix in ("png", "pdf", "svg"))
    assert all(output.stat().st_size > 0 for output in outputs)
    plt.close(fig)


def test_science_size_and_journal_subplots():
    assert hdg.figsize("science") == (2.24, 2.20)
    fig, _ = hdg.subplots(journal="science", column="double")
    assert tuple(fig.get_size_inches()) == (4.76, 3.40)
    plt.close(fig)


@pytest.mark.parametrize(("filename", "signature"), [("figure.png", b"\x89PNG\r\n\x1a\n"), ("figure.PDF", b"%PDF-")])
def test_save_infers_format_and_retains_filename(tmp_path, filename, signature):
    fig, ax = plt.subplots()
    ax.plot([0, 1], [1, 0])
    target = tmp_path / "nested" / filename
    try:
        assert hdg.plots.save(target, fig=fig, close=True) == (target,)
        assert target.read_bytes().startswith(signature)
        assert list(target.parent.iterdir()) == [target]
        assert not plt.fignum_exists(fig.number)
    finally:
        plt.close(fig)


def test_save_keeps_default_stem_formats(tmp_path):
    fig, _ = plt.subplots()
    try:
        outputs = hdg.plots.save(tmp_path / "figure", fig=fig)
        assert outputs == (tmp_path / "figure.pdf", tmp_path / "figure.png")
        assert outputs[0].read_bytes().startswith(b"%PDF-")
        assert outputs[1].read_bytes().startswith(b"\x89PNG")
    finally:
        plt.close(fig)


@pytest.mark.parametrize("options", [{"formats": ("pdf",)}, {"formats": "pdf"}, {"formats": ()}, {"format": "png"}])
def test_save_rejects_ambiguous_format_before_finishing(tmp_path, options):
    fig, _ = plt.subplots()
    try:
        with pytest.raises(ValueError):
            hdg.plots.save(tmp_path / "nested" / "figure.pdf", fig=fig, **options)
        assert not (tmp_path / "nested").exists()
        assert not getattr(fig, "_hedgehogs_finished", False)
    finally:
        plt.close(fig)


def test_save_accepts_a_format_string(tmp_path):
    fig, _ = plt.subplots()
    try:
        outputs = hdg.plots.save(tmp_path / "figure", fig=fig, formats="pdf")
        assert outputs == (tmp_path / "figure.pdf",)
        assert outputs[0].read_bytes().startswith(b"%PDF-")
    finally:
        plt.close(fig)


def test_save_uses_current_figure_and_does_not_create_empty_figures(tmp_path):
    plt.close('all')
    with pytest.raises(ValueError, match='No current figure'):
        hdg.plots.save(tmp_path / 'empty.pdf')
    assert not plt.get_fignums()
    first, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    second, _ = plt.subplots()
    plt.figure(first.number)
    assert hdg.plots.save(tmp_path / 'current.pdf', close=True) == (tmp_path / 'current.pdf',)
    assert not plt.fignum_exists(first.number)
    assert plt.fignum_exists(second.number)
    plt.close(second)
