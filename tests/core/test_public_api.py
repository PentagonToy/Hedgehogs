import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt

import hedgehogs as hdg


def test_public_api():
    expected = [
        "EPS",
        "Palette",
        "get_palette",
        "build_color_map",
        "build_style_map",
        "register_palette",
        "save_palette",
        "load_palette",
        "set_style",
        "reset_style",
        "journal_preset",
        "set_journal_style",
        "figsize",
        "subplots",
                "finalize",
        "style_colorbar",
        "annotate_panels",
        "enable_minor_ticks",
        "apply_grid",
        "plots",
        "Table",
        "Progress",
        "echo",
        "rule",
        "info",
    ]

    missing = [name for name in expected if not hasattr(hdg, name)]

    assert not missing
    assert not hasattr(hdg, "fixed_frame")
    assert not hasattr(hdg, "TableMaker")
    assert not hasattr(hdg, "ProgressBar")


def test_plotting_api():
    hdg.set_style()

    palette = hdg.get_palette()

    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1], color=palette[0])

    hdg.finalize(ax)
    hdg.enable_minor_ticks(ax)
    hdg.apply_grid(ax)
    hdg.annotate_panels([ax])

    plt.close(fig)


def test_table_api():
    table = hdg.Table(
        title="Test",
        columns=["Name", "Value"],
        mode="static",
    )

    table.add_row("alpha", 1)

    assert table.data == [["alpha", "1"]]


def test_progress_api():
    progress = hdg.Progress(total=2, desc="Test")

    progress.update()
    progress.update()
    progress.finish()

    assert progress.n == 2


def test_specialised_plots_have_one_public_namespace():
    assert hdg.plots.__all__ == ["tree", "pairplot", "show", "save"]
    assert callable(hdg.plots.tree)
    assert callable(hdg.plots.pairplot)
    assert not hasattr(hdg, "plot_tree")
    assert not hasattr(hdg, "pairplot")
    assert not hasattr(hdg, "export_figure")
    assert callable(hdg.plots.save)


def test_progress_and_table_have_no_duplicate_top_level_helpers():
    assert not hasattr(hdg, "track")
    assert not hasattr(hdg, "sleep")
    assert not hasattr(hdg, "table")
    assert not hasattr(hdg, "progress")


def test_public_introspection_is_clean_and_describes_new_interfaces():
    import inspect
    import pydoc
    assert {name for name in dir(hdg) if not name.startswith('_')} == set(hdg.__all__)
    assert dir(hdg.plots) == sorted(hdg.plots.__all__)
    signature = inspect.signature(hdg.plots.save)
    assert signature.parameters['fig'].default is None
    assert 'current pyplot figure' in pydoc.render_doc(hdg.plots.save)
    assert 'formatted table rows' in pydoc.render_doc(hdg.Table.to_dataframe)
