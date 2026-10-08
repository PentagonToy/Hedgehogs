"""Package identity and responsibility boundaries."""

import hedgehogs as hdg
from hedgehogs.core.version import __version__
from hedgehogs.tables import Table
from hedgehogs.terminal import Progress


def test_package_identity_and_facade():
    assert hdg.__version__ == __version__ == "0.0.1"
    assert hdg.Table is Table
    assert hdg.Progress is Progress
    assert hdg.Table.__module__ == "hedgehogs.tables.table"
    assert hdg.Progress.__module__ == "hedgehogs.terminal.progress"
