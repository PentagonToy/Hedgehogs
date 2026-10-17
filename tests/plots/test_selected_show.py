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


def test_inline_selected_display_suppresses_cell_flush_preserves_other_figures(monkeypatch):
    from matplotlib_inline import backend_inline as inline
    import IPython.display
    figures = [plt.figure() for _ in range(3)]
    for fig in figures:
        fig.add_subplot().plot([0, 1], [0, 1])
    display = Mock()
    monkeypatch.setattr(IPython.display, 'display', display)
    monkeypatch.setattr(inline, 'display', Mock(side_effect=AssertionError('Unexpected cell flush')))
    monkeypatch.setattr(plt, 'get_backend', lambda: 'module://matplotlib_inline.backend_inline')
    monkeypatch.setattr(inline.show, '_draw_called', True)
    monkeypatch.setattr(inline.show, '_to_draw', figures[:])
    hdg.plots.show(fig=figures[0])
    inline.flush_figures()
    display.assert_called_once_with(figures[0])
    assert len(plt.get_fignums()) == 3
    hdg.plots.show(fig=figures[1])
    assert display.call_args.args == (figures[1],)


@pytest.mark.parametrize('block', [False, True, None])
def test_selected_gui_only_shows_selected_manager_and_owns_its_event_loop(monkeypatch, block):
    first, second = plt.figure(), plt.figure()
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
