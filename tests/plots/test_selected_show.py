import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backend_bases import CloseEvent
from unittest.mock import Mock
import pytest
import hedgehogs as hdg


@pytest.fixture(autouse=True)
def cleanup():
    hdg.set_style()
    yield
    plt.close('all')
    hdg.reset_style()


@pytest.mark.parametrize('backend', ['inline', 'module://matplotlib_inline.backend_inline'])
def test_inline_selected_display_consumes_batch_preserves_figure_objects(monkeypatch, backend):
    from matplotlib_inline import backend_inline as inline
    import IPython.display
    figures = [plt.figure() for _ in range(3)]
    for fig in figures:
        fig.add_subplot().plot([0, 1], [0, 1])
    display = Mock()
    monkeypatch.setattr(IPython.display, 'display', display)
    monkeypatch.setattr(inline, 'display', Mock(side_effect=AssertionError('Unexpected cell flush')))
    monkeypatch.setattr(plt, 'get_backend', lambda: backend)
    monkeypatch.setattr(inline.InlineBackend.instance(), 'close_figures', True)
    monkeypatch.setattr(inline.show, '_draw_called', True)
    monkeypatch.setattr(inline.show, '_to_draw', figures[:])
    hdg.plots.show(fig=figures[0])
    inline.flush_figures()
    display.assert_called_once_with(figures[0])
    assert not plt.get_fignums()
    hdg.plots.show(fig=figures[1])
    assert display.call_args.args == (figures[1],)
    assert not plt.get_fignums()


@pytest.mark.parametrize('block', [False, True, None])
def test_selected_gui_only_shows_selected_manager_and_owns_its_event_loop(monkeypatch, block):
    first, second = plt.figure(), plt.figure()
    monkeypatch.setattr(first.canvas, 'required_interactive_framework', 'tk')
    first.add_subplot().plot([0, 1], [0, 1])
    other_show = Mock()
    monkeypatch.setattr(second.canvas.manager, 'show', other_show)
    selected_show = Mock()
    monkeypatch.setattr(first.canvas.manager, 'show', selected_show)
    stop = Mock()
    monkeypatch.setattr(first.canvas, 'stop_event_loop', stop)
    loop = Mock(side_effect=lambda **kwargs: CloseEvent('close_event', first.canvas)._process())
    monkeypatch.setattr(first.canvas, 'start_event_loop', loop)
    monkeypatch.setattr(plt, 'show', Mock(spec=[], side_effect=AssertionError('Global show invoked')))
    monkeypatch.setattr(plt, 'isinteractive', lambda: False)
    hdg.plots.show(fig=first, block=block)
    selected_show.assert_called_once()
    other_show.assert_not_called()
    assert loop.call_count == (0 if block is False else 1)
    assert stop.call_count == loop.call_count
    assert len(plt.get_fignums()) == 2


def test_no_selection_retains_global_show(monkeypatch):
    first, second = plt.figure(), plt.figure()
    display = Mock()
    monkeypatch.setattr(plt, 'show', display)
    hdg.plots.show(block=False)
    display.assert_called_once_with(block=False)
    assert first._hedgehogs_finished and second._hedgehogs_finished


@pytest.mark.parametrize('block', [None, True, False])
def test_headless_linux_agg_never_starts_event_loop(monkeypatch, block):
    import sys
    first, second = plt.figure(), plt.figure()
    monkeypatch.setattr(sys, 'platform', 'linux')
    monkeypatch.delenv('DISPLAY', raising=False)
    monkeypatch.setattr(first.canvas, 'start_event_loop', Mock(side_effect=AssertionError('Headless event loop')))
    hdg.plots.show(fig=first, block=block)
    assert plt.fignum_exists(second.number)


@pytest.mark.parametrize('use_hdg', [False, True])
def test_inline_selected_figures_do_not_repeat_in_next_global_show(monkeypatch, tmp_path, use_hdg):
    from matplotlib_inline import backend_inline as inline
    from matplotlib._pylab_helpers import Gcf
    import IPython.display
    figures = [plt.figure() for _ in range(3)]
    for fig in figures:
        fig.add_subplot().plot([0, 1], [0, 1])
    monkeypatch.setattr(plt, 'get_backend', lambda: 'module://matplotlib_inline.backend_inline')
    monkeypatch.setattr(inline.InlineBackend.instance(), 'close_figures', True)
    monkeypatch.setattr(IPython.display, 'display', Mock())
    for fig in figures:
        hdg.plots.show(fig=fig)
    assert not Gcf.get_all_fig_managers()
    # A closed pyplot figure remains usable; even a reused number is safe.
    hdg.plots.save(tmp_path / 'reshown.png', fig=figures[0])
    hdg.plots.show(fig=figures[0])
    next_fig = plt.figure()
    next_fig.add_subplot().plot([0, 1], [1, 0])
    assert [m.canvas.figure for m in Gcf.get_all_fig_managers()] == [next_fig]
    display = Mock()
    monkeypatch.setattr(inline, 'display', display)
    monkeypatch.setattr(plt, 'show', inline.show)
    if use_hdg:
        hdg.plots.show()
    else:
        plt.show()
    assert [call.args[0] for call in display.call_args_list] == [next_fig]


def test_inline_explicit_keep_open_setting_is_respected(monkeypatch):
    from matplotlib_inline import backend_inline as inline
    import IPython.display
    first, second = plt.figure(), plt.figure()
    monkeypatch.setattr(plt, 'get_backend', lambda: 'module://matplotlib_inline.backend_inline')
    monkeypatch.setattr(inline.InlineBackend.instance(), 'close_figures', False)
    monkeypatch.setattr(IPython.display, 'display', Mock())
    hdg.plots.show(fig=first)
    assert plt.fignum_exists(first.number) and plt.fignum_exists(second.number)


@pytest.mark.parametrize('use_hdg', [False, True])
def test_inline_selection_leaves_no_unselected_figures_for_global_show(monkeypatch, use_hdg):
    from matplotlib_inline import backend_inline as inline
    import IPython.display
    figures = [plt.figure() for _ in range(3)]
    for fig in figures:
        fig.add_subplot().plot([0, 1], [0, 1])
    selected_display = Mock()
    global_display = Mock()
    monkeypatch.setattr(plt, 'get_backend', lambda: 'inline')
    monkeypatch.setattr(inline.InlineBackend.instance(), 'close_figures', True)
    monkeypatch.setattr(IPython.display, 'display', selected_display)
    monkeypatch.setattr(inline, 'display', global_display)
    monkeypatch.setattr(plt, 'show', inline.show)
    hdg.plots.show(fig=figures[0])
    if use_hdg:
        hdg.plots.show()
    else:
        plt.show()
    global_display.assert_not_called()
    selected_display.assert_called_once_with(figures[0])
    for fig in figures[1:]:
        hdg.plots.show(fig=fig)
    assert [call.args[0] for call in selected_display.call_args_list] == figures
    assert not plt.get_fignums()
