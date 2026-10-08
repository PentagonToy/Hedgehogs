"""Tests for table rendering and row insertion functionality."""

from types import MappingProxyType

import pytest
import hedgehogs as hdg


class _DataFrame:
    """Minimal DataFrame protocol used without a pandas dependency."""

    def __init__(self, columns, rows):
        self.columns = columns
        self.rows = rows

    def itertuples(self, *, index, name):
        assert index is False
        assert name is None
        return iter(self.rows)


class _PolarsDataFrame:
    """Minimal Polars DataFrame protocol used without a dependency."""

    def __init__(self, columns, rows):
        self.columns = columns
        self.rows = rows

    def iter_rows(self, *, named):
        assert named is False
        return iter(self.rows)


def test_table_maker_add_row_variants():
    """Verify add_row supports positional arguments, lists, and tuples."""
    table = hdg.Table(
        title="Thermodynamics & Kinetics Summary",
        columns=["Parameter", "Value", "Unit"],
    )

    # 1. Positional arguments
    table.add_row("Temperature", 400.0, "K")
    table.add_row("Equivalence Ratio", 1.000, "-")

    # 2. Single list
    table.add_row(["Pressure", 101.3, "kPa"])
    table.add_row(["Laminar Flame Speed", 0.3850, "m/s"])

    # 3. Single tuple
    table.add_row(("Density", 1.184, "kg/m^3"))

    # Assertions on internal string representations
    assert len(table.data) == 5
    assert table.data[0] == ["Temperature", "400.0", "K"]
    assert table.data[2] == ["Pressure", "101.3", "kPa"]
    assert table.data[4] == ["Density", "1.184", "kg/m^3"]


def test_table_maker_update_row_variants():
    """Verify update_row replaces rows using supported input forms."""
    table = hdg.Table(
        title="Build Status",
        columns=["Component", "Status"],
    )
    table.add_row("SmartRedis", "Pending")
    table.add_row("OpenFOAM", "Pending")

    table.update_row(0, "SmartRedis", "Building")
    table.update_row(1, ["OpenFOAM", "Done"])

    assert table.data == [
        ["SmartRedis", "Building"],
        ["OpenFOAM", "Done"],
    ]


def test_table_maker_update_row_refreshes_live_table(monkeypatch):
    """Verify live tables refresh after an existing row changes."""
    table = hdg.Table(
        title="Build Status",
        columns=["Component", "Status"],
        mode="live",
    )
    updates = []

    monkeypatch.setattr(
        table,
        "_update",
        lambda: updates.append(
            tuple(tuple(row) for row in table.data)
        ),
    )

    table.add_row("SmartRedis", "Pending")
    table.update_row(0, "SmartRedis", "Done")

    assert updates == [
        (("SmartRedis", "Pending"),),
        (("SmartRedis", "Done"),),
    ]


def test_table_maker_update_row_rejects_invalid_index():
    """Verify update_row validates row indices."""
    table = hdg.Table()
    table.add_row("Temperature", "400", "K")

    with pytest.raises(
        TypeError,
        match="Row index must be an integer",
    ):
        table.update_row(
            "0",
            "Temperature",
            "500",
            "K",
        )

    with pytest.raises(
        IndexError,
        match="Row index out of range: 2",
    ):
        table.update_row(
            2,
            "Temperature",
            "500",
            "K",
        )


def test_table_maker_render_output(capsys):
    """Verify standard text rendering output in console mode."""
    table = hdg.Table(
        title="Species Concentration",
        columns=["Species", "Mole Fraction"],
    )
    table.add_row("CH4", 0.0950)
    table.add_row(["O2", 0.1900])

    table.show()
    captured = capsys.readouterr()

    assert "Species Concentration" in captured.out
    assert "CH4" in captured.out
    assert "0.19" in captured.out


def test_text_table_wraps_to_requested_width():
    table = hdg.Table("Doctor", ["Status", "Check", "Detail"])
    table.add_row("PASS", "Runtime", "/a/very/long/runtime/path/that/must/wrap/in/a/narrow/terminal")
    output = table.to_text(width=52)
    assert max(map(len, output.splitlines())) <= 52
    assert "┌" in output and "┐" in output and "└" in output and "┘" in output
    assert "PASS" in output and "Runtime" in output


def test_html_table_uses_signature_booktabs_presentation():
    table = hdg.Table("OpenFOAM Field Statistics", ["Field", "Min", "Max"])
    table.add_row("U", "8.13e-06", "8.74e-01")

    output = table.to_html()

    assert "Times New Roman" in output
    assert "border-top:2.5px solid currentColor" in output
    assert "border-bottom:1.2px solid currentColor" in output
    assert "border-bottom:2.5px solid currentColor" in output
    assert "border:none" in output


def test_invalid_mode():
    """Verify ValueError when passing an unsupported table mode."""
    with pytest.raises(ValueError, match="Unknown mode 'invalid'"):
        hdg.Table(mode="invalid")

def test_live_table_suppresses_intermediate_non_tty_output(
    capsys,
):
    """Verify redirected live output emits only the final table."""
    table = hdg.Table(
        title="Build Status",
        columns=["Component", "Status"],
        mode="live",
    )

    table.add_row(
        "SmartRedis",
        "Pending",
    )
    table.update_row(
        0,
        "SmartRedis",
        "Building",
    )
    table.update_row(
        0,
        "SmartRedis",
        "Done",
    )

    intermediate = capsys.readouterr()

    assert intermediate.out == ""

    table.finish()

    final = capsys.readouterr()

    assert "Build Status" in final.out
    assert "SmartRedis" in final.out
    assert "Done" in final.out
    assert "Pending" not in final.out
    assert "Building" not in final.out
    assert "\033[" not in final.out


def test_live_table_finish_is_idempotent(
    capsys,
):
    """Verify closing a live table more than once emits no duplicate."""
    table = hdg.Table(
        title="Build Status",
        columns=["Component", "Status"],
        mode="live",
    )
    table.add_row(
        "OpenFOAM",
        "Done",
    )

    table.finish()
    first = capsys.readouterr()

    table.finish()
    second = capsys.readouterr()

    assert "OpenFOAM" in first.out
    assert second.out == ""


def test_table_rejects_wrong_row_width():
    table = hdg.Table(columns=["Name", "Value"])
    with pytest.raises(ValueError, match="Expected 2 values"):
        table.add_row("only-one")


def test_table_format_sort_and_exports(tmp_path):
    table = hdg.Table(
        title="Results",
        columns=["Case", "Error"],
        formatters={"Error": ".2f"},
    )
    table.add_row("B", 2.345)
    table.add_row("A", 1.234)
    table.sort("Case")

    assert table.data == [["A", "1.23"], ["B", "2.35"]]

    csv_path = table.to_csv(tmp_path / "results.csv")
    assert csv_path.read_text().splitlines() == [
        "Case,Error",
        "A,1.23",
        "B,2.35",
    ]

    latex = table.to_latex(caption="A & B", label="tab:results")
    assert r"\caption{A \& B}" in latex
    assert r"\toprule" in latex


def test_table_accepts_read_only_formatter_mapping():
    table = hdg.Table(
        columns=["Case", "Error"],
        formatters=MappingProxyType({"Error": ".2f"}),
    )

    table.add_row("A", 1.234)

    assert table.data == [["A", "1.23"]]


def test_table_from_dataframe_uses_all_columns_in_source_order():
    dataframe = _DataFrame(
        ["case", "phi", "eta_ref"],
        [("lean", 0.45, 0.3123), ("rich", 1.25, 0.8765)],
    )

    table = hdg.Table.from_dataframe(dataframe=dataframe)

    assert table.title == "Analysis"
    assert table.columns == ["case", "phi", "eta_ref"]
    assert table.data == [
        ["lean", "0.45", "0.3123"],
        ["rich", "1.25", "0.8765"],
    ]


def test_table_from_dataframe_selects_and_formats_columns():
    dataframe = _DataFrame(
        ["case", "phi", "eta_ref"],
        [("lean", 0.45, 0.31234)],
    )

    table = hdg.Table.from_dataframe(
        dataframe=dataframe,
        title="Counterflow ranges",
        columns=["eta_ref", "phi"],
        mode="static",
        formatters={"eta_ref": ".4f", "phi": ".2f"},
    )

    assert table.title == "Counterflow ranges"
    assert table.columns == ["eta_ref", "phi"]
    assert table.data == [["0.3123", "0.45"]]


def test_table_from_polars_dataframe_uses_same_public_api():
    dataframe = _PolarsDataFrame(
        ["case", "phi", "eta_ref"],
        [("lean", 0.45, 0.31234)],
    )

    table = hdg.Table.from_dataframe(
        dataframe=dataframe,
        columns=["case", "eta_ref"],
        formatters={"eta_ref": ".4f"},
    )

    assert table.columns == ["case", "eta_ref"]
    assert table.data == [["lean", "0.3123"]]


def test_table_from_dataframe_rejects_unknown_column():
    dataframe = _DataFrame(["case"], [("lean",)])

    with pytest.raises(KeyError, match="Unknown DataFrame column: 'phi'"):
        hdg.Table.from_dataframe(
            dataframe=dataframe,
            columns=["phi"],
        )


def test_table_from_dataframe_rejects_incompatible_object():
    with pytest.raises(TypeError, match="must provide a columns attribute"):
        hdg.Table.from_dataframe(dataframe=object())


def test_table_from_dataframe_rejects_unknown_row_protocol():
    dataframe = type("UnsupportedDataFrame", (), {"columns": ["case"]})()

    with pytest.raises(TypeError, match="itertuples.*iter_rows"):
        hdg.Table.from_dataframe(dataframe=dataframe)


def test_table_from_dataframe_rejects_empty_selection():
    dataframe = _DataFrame(["case"], [("lean",)])

    with pytest.raises(ValueError, match="at least one selected column"):
        hdg.Table.from_dataframe(
            dataframe=dataframe,
            columns=[],
        )


@pytest.mark.parametrize(('alias', 'name'), [('pd', 'pandas'), ('pandas', 'pandas'), ('pl', 'polars'), ('polars', 'polars')])
def test_to_dataframe_preserves_formatted_rows_order_and_independence(monkeypatch, alias, name):
    import sys
    from types import ModuleType
    module = ModuleType(name)
    calls = []
    def dataframe(rows, **options):
        calls.append((rows, options))
        return rows
    module.DataFrame = dataframe
    monkeypatch.setitem(sys.modules, name, module)
    table = hdg.Table(columns=['Value', 'Name'], formatters={'Value': '.2f'})
    table.add_row(1.234, 'A')
    result = table.to_dataframe(alias)
    assert result == [['1.23', 'A']]
    assert calls[0][1] == ({'columns': ['Value', 'Name']} if name == 'pandas' else {'schema': ['Value', 'Name'], 'orient': 'row'})
    result[0][0] = 'changed'
    assert table.data == [['1.23', 'A']]
    assert table.to_dataframe(module) == [['1.23', 'A']]


def test_to_dataframe_validates_backend_and_reports_missing_optional_dependency(monkeypatch):
    import importlib
    table = hdg.Table()
    with pytest.raises(ValueError):
        table.to_dataframe('unknown')
    with pytest.raises(TypeError):
        table.to_dataframe(object())
    def missing(name):
        raise ModuleNotFoundError('missing', name=name)
    monkeypatch.setattr(importlib, 'import_module', missing)
    with pytest.raises(ImportError, match='polars is required'):
        table.to_dataframe('pl')


def test_to_dataframe_empty_table_retains_column_schema(monkeypatch):
    import sys
    from types import ModuleType
    module = ModuleType('polars')
    module.DataFrame = lambda rows, **options: (rows, options)
    monkeypatch.setitem(sys.modules, 'polars', module)
    table = hdg.Table(columns=['A', 'B'])
    assert table.to_dataframe('pl') == ([], {'schema': ['A', 'B'], 'orient': 'row'})
