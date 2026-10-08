"""Portable table rendering for terminals and notebooks."""

import csv
from collections.abc import Callable, Iterable, Mapping, Sequence
import html
from io import StringIO
from os import PathLike
from pathlib import Path
from types import ModuleType
import shutil
import sys
from typing import Any

from rich import box
from rich.console import Console
from rich.table import Table as RichTable
from rich.text import Text

from ..core.environment import _is_jupyter


_TABLE_MODES = ("static", "live", "dynamic")


class Table:
    """A small scientific table with plain-text and HTML representations."""

    def __init__(self, title: str = "Analysis", columns: Iterable[str] | None = None, mode: str = "static", *, formatters: Mapping[str | int, str | Callable[[Any], Any]] | Sequence[str | Callable[[Any], Any] | None] | None = None) -> None:
        if mode not in _TABLE_MODES:
            raise ValueError(f"Unknown mode {mode!r}; expected one of {_TABLE_MODES}.")
        self.title = title
        self.columns = list(columns or ["Parameter", "Value", "Unit"])
        if not self.columns:
            raise ValueError("Table requires at least one column.")
        self.data: list[list[str]] = []
        self.mode = mode
        self.formatters = formatters
        self._jupyter = _is_jupyter()
        self._handle = None
        self._finished = False
        self._rendered_lines = 0

    @classmethod
    def from_dataframe(
        cls,
        dataframe: Any,
        title: str = "Analysis",
        columns: Iterable[str] | None = None,
        mode: str = "static",
        *,
        formatters: Mapping[str | int, str | Callable[[Any], Any]] | Sequence[str | Callable[[Any], Any] | None] | None = None,
    ) -> "Table":
        """Create a table from pandas or Polars columns and rows."""
        try:
            source_columns = list(dataframe.columns)
        except AttributeError as error:
            raise TypeError(
                "dataframe must provide a columns attribute."
            ) from error

        if callable(itertuples := getattr(dataframe, "itertuples", None)):
            rows = itertuples(index=False, name=None)
        elif callable(iter_rows := getattr(dataframe, "iter_rows", None)):
            rows = iter_rows(named=False)
        else:
            raise TypeError(
                "dataframe must provide pandas itertuples() or Polars iter_rows()."
            )

        selected_columns = source_columns if columns is None else list(columns)
        if not selected_columns:
            raise ValueError("DataFrame requires at least one selected column.")
        positions = []
        for column in selected_columns:
            try:
                positions.append(source_columns.index(column))
            except ValueError as error:
                raise KeyError(f"Unknown DataFrame column: {column!r}.") from error

        table = cls(
            title=title,
            columns=[str(column) for column in selected_columns],
            mode=mode,
            formatters=formatters,
        )
        for row in rows:
            table.add_row(*(row[position] for position in positions))
        return table

    def to_dataframe(self, backend: str | ModuleType = "pandas") -> Any:
        """Return an independent DataFrame containing the formatted table rows.

        ``backend`` accepts "pandas", "pd", "polars", "pl", or the imported
        pandas/Polars module. The selected optional library is imported on demand.
        Column order and stored strings are retained; original numeric precision,
        types and source indices cannot be recovered from formatted rows.

        Unknown names raise ValueError; unsupported objects raise TypeError.
        An unavailable selected library raises ImportError.
        """
        from importlib import import_module

        names = {"pd": "pandas", "pandas": "pandas", "pl": "polars", "polars": "polars"}
        if isinstance(backend, str):
            try:
                name = names[backend.lower()]
            except KeyError as error:
                raise ValueError("backend must be pandas, pd, polars or pl.") from error
            try:
                module = import_module(name)
            except ModuleNotFoundError as error:
                if error.name != name:
                    raise
                raise ImportError(f"{name} is required for this conversion.") from error
        elif isinstance(backend, ModuleType) and backend.__name__ in ("pandas", "polars"):
            module, name = backend, backend.__name__
        else:
            raise TypeError("backend must be a pandas/Polars module or its name.")
        rows = [list(row) for row in self.data]
        columns = list(self.columns)
        if name == "pandas":
            return module.DataFrame(rows, columns=columns)
        return module.DataFrame(rows, schema=columns, orient="row")

    def _normalise_row(self, values: tuple[Any, ...]) -> list[str]:
        row = list(values[0]) if len(values) == 1 and isinstance(values[0], (list, tuple)) else list(values)
        if len(row) != len(self.columns):
            raise ValueError(f"Expected {len(self.columns)} values, received {len(row)}.")
        result = []
        for index, value in enumerate(row):
            formatter = None
            if isinstance(self.formatters, Mapping):
                formatter = self.formatters.get(self.columns[index], self.formatters.get(index))
            elif self.formatters is not None and index < len(self.formatters):
                formatter = self.formatters[index]
            if formatter is None:
                result.append(str(value))
            elif callable(formatter):
                result.append(str(formatter(value)))
            else:
                result.append(format(value, str(formatter)))
        return result

    def add_row(self, *values: Any) -> None:
        """Add a row and refresh live output."""
        self.data.append(self._normalise_row(values))
        if self.mode in {"live", "dynamic"}:
            self._update()

    def update_row(self, index: int, *values: Any) -> None:
        """Replace a row and refresh live output."""
        if not isinstance(index, int) or isinstance(index, bool):
            raise TypeError("Row index must be an integer.")
        try:
            self.data[index] = self._normalise_row(values)
        except IndexError as error:
            raise IndexError(f"Row index out of range: {index}") from error
        if self.mode in {"live", "dynamic"}:
            self._update()

    def sort(self, column: str | int = 0, *, reverse: bool = False, key: Callable[[str], Any] | None = None) -> "Table":
        """Sort rows in place by a column name or index."""
        if isinstance(column, str):
            try:
                column = self.columns.index(column)
            except ValueError as error:
                raise KeyError(f"Unknown table column: {column!r}.") from error
        if not isinstance(column, int) or isinstance(column, bool):
            raise TypeError("column must be a name or integer index.")
        if not -len(self.columns) <= column < len(self.columns):
            raise IndexError(f"Column index out of range: {column}")
        value_key = key or (lambda value: value)
        self.data.sort(key=lambda row: value_key(row[column]), reverse=reverse)
        if self.mode in {"live", "dynamic"}:
            self._update()
        return self

    def to_text(self, width: int | None = None) -> str:
        """Return a terminal-width-aware Rich Unicode table."""
        available = width or shutil.get_terminal_size((120, 20)).columns
        available = max(20, available)
        rendered = StringIO()
        table = RichTable(
            title=Text(str(self.title)),
            title_justify="left",
            box=box.SQUARE,
            show_lines=True,
            header_style="bold",
            padding=(0, 1),
        )
        for index, column in enumerate(self.columns):
            numeric = bool(self.data)
            if numeric:
                try:
                    for row in self.data:
                        float(row[index])
                except ValueError:
                    numeric = False
            table.add_column(
                str(column),
                justify="right" if numeric else "left",
                overflow="fold",
            )
        for row in self.data:
            table.add_row(*(Text(str(value)) for value in row))
        console = Console(
            file=rendered,
            width=available,
            color_system=None,
            force_terminal=False,
            legacy_windows=False,
        )
        console.print(table)
        return rendered.getvalue()

    def to_html(self) -> str:
        """Return the publication-style booktabs HTML table."""
        esc = html.escape
        font = "'Times New Roman', Times, serif"
        headings = "".join(
            f'<th style="padding:10px 14px;text-align:{"left" if index == 0 else "right"};'
            'font-weight:bold;color:currentColor;border-top:2.5px solid currentColor;'
            'border-bottom:1.2px solid currentColor;font-size:14px;background:none">'
            f"{esc(str(value))}</th>"
            for index, value in enumerate(self.columns)
        )
        rows = "".join(
            "<tr>"
            + "".join(
                f'<td style="padding:8px 14px;text-align:{"left" if index == 0 else "right"};'
                f'font-size:13px;color:currentColor;border-bottom:{"2.5px solid currentColor" if row_index + 1 == len(self.data) else "none"};'
                f'background:none">{esc(str(value))}</td>'
                for index, value in enumerate(row)
            )
            + "</tr>"
            for row_index, row in enumerate(self.data)
        )
        return (
            '<div style="margin:15px 0;display:inline-block;background:none">'
            f'<div style="font-family:{font};font-weight:bold;color:currentColor;'
            f'font-size:14px;margin-bottom:10px;text-align:left">{esc(str(self.title))}</div>'
            f'<table style="border-collapse:collapse;font-family:{font};border:none;'
            f'line-height:1.5;color:currentColor;background:none"><thead><tr>{headings}</tr>'
            f"</thead><tbody>{rows}</tbody></table></div>"
        )

    def _repr_mimebundle_(self, include=None, exclude=None) -> dict[str, str]:
        return {"text/plain": self.to_text(), "text/html": self.to_html()}

    def _update(self) -> None:
        if self._jupyter:
            from IPython.display import HTML, display
            rendered = HTML(self.to_html())
            if self._handle is None:
                self._handle = display(rendered, display_id=True)
            else:
                self._handle.update(rendered)
        elif sys.stdout.isatty():
            if self._rendered_lines:
                sys.stdout.write(f"\033[{self._rendered_lines}F\033[J")
            output = self.to_text()
            sys.stdout.write(output)
            sys.stdout.flush()
            self._rendered_lines = output.count("\n")

    def show(self) -> None:
        """Display the table in the current environment."""
        if self._jupyter:
            from IPython.display import HTML, display
            display(HTML(self.to_html()))
        else:
            print(self.to_text(), end="")

    def finish(self) -> None:
        """Preserve the final state of a live table."""
        if self._finished:
            return
        if self.mode in {"live", "dynamic"} and not self._jupyter and not sys.stdout.isatty():
            print(self.to_text(), end="")
        self._finished = True

    def to_csv(self, path: str | PathLike[str]) -> Path:
        destination = Path(path).expanduser()
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(self.columns)
            writer.writerows(self.data)
        return destination

    def to_latex(self, path: str | PathLike[str] | None = None, *, caption: str | None = None, label: str | None = None) -> str:
        """Return a booktabs LaTeX table and optionally write it to a file."""
        replacements = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}"}
        def escape(value: object) -> str:
            return "".join(replacements.get(character, character) for character in str(value))
        lines = [r"\begin{table}", r"\centering"]
        if caption is not None:
            lines.append(rf"\caption{{{escape(caption)}}}")
        if label is not None:
            lines.append(rf"\label{{{escape(label)}}}")
        row_end = " " + "\\" * 2
        lines.extend([rf"\begin{{tabular}}{{{'l' + 'r' * (len(self.columns) - 1)}}}", r"\toprule", " & ".join(map(escape, self.columns)) + row_end, r"\midrule"])
        lines.extend(" & ".join(map(escape, row)) + row_end for row in self.data)
        lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}"])
        output = "\n".join(lines) + "\n"
        if path is not None:
            destination = Path(path).expanduser()
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(output, encoding="utf-8")
        return output
