"""Console and Jupyter progress reporting."""

from collections.abc import Iterable, Iterator, Sized
import html as _html
import math
import sys
import time
from typing import Generic, Literal, TypeVar

from ..core.environment import _is_jupyter




_T = TypeVar("_T")


class Progress(Generic[_T]):
    """
    Progress bar with portable plain-text and HTML representations.

    Unlike ``tqdm.auto`` (which uses ipywidgets), this renders as plain
    HTML in Jupyter via ``display(..., display_id=True)`` + ``.update()``.
    The final state is therefore preserved as ``text/html`` cell output
    when the notebook is committed to GitHub, where it renders as a
    completed (frozen-at-100 %) progress bar instead of an empty widget.

    Parameters
    ----------
    iterable : iterable, optional
        Wrap an iterable for tqdm-style usage:
        ``for x in Progress(range(N), desc="..."):``.
    total : int, optional
        Total number of iterations.  Inferred from ``len(iterable)`` if
        omitted.  When unknown, an indeterminate bar is shown.
    desc : str, optional
        Prefix label.
    width : int, optional
        Number of characters in the terminal-mode bar.
    mininterval : float, optional
        Minimum seconds between visual refreshes.  Essential for tight
        loops — without it, fast iteration is bottlenecked by HTML
        rendering rather than the actual workload.

    Examples
    --------
    >>> for x in hdg.Progress(range(1000), desc="Training"):
    ...     do_work(x)

    >>> pb = hdg.Progress(total=N, desc="Sweep")
    >>> for i in range(N):
    ...     compute()
    ...     pb.update()
    >>> pb.finish()
    """

    # ── Design constants ──
    _FONT = "'Times New Roman', Times, serif"
    _BAR_PX = 260

    def __init__(
        self,
        iterable: Iterable[_T] | None = None,
        total: int | None = None,
        desc: str = "",
        width: int = 40,
        mininterval: float = 0.1,
        smoothing: float = 0.3,
    ) -> None:
        self.iterable = iterable
        if total is None and isinstance(iterable, Sized):
            total = len(iterable)
        if total is not None and (
            not isinstance(total, int)
            or isinstance(total, bool)
            or total < 0
        ):
            raise ValueError("total must be a non-negative integer or None.")
        if not isinstance(width, int) or isinstance(width, bool) or width < 1:
            raise ValueError("width must be a positive integer.")
        if mininterval < 0:
            raise ValueError("mininterval must be non-negative.")
        if not 0 <= smoothing <= 1:
            raise ValueError("smoothing must be between 0 and 1.")

        self.total = total
        self.desc = desc
        self.width = width
        self.mininterval = mininterval
        self.smoothing = smoothing

        self.n: int | float = 0
        self._start: float | None = None
        self._last = 0.0
        self._handle = None
        self._jupyter = _is_jupyter()
        self._finished = False
        self._metrics: dict[str, object] = {}
        self._rate = 0.0
        self._rate_n: int | float = 0
        self._rate_time: float | None = None

    # ── Formatting helpers ──

    @staticmethod
    def _fmt_time(s: float | None) -> str:
        if s is None or not math.isfinite(s):
            return "?"
        s = int(s)
        h, rem = divmod(s, 3600)
        m, sec = divmod(rem, 60)
        return f"{h:d}:{m:02d}:{sec:02d}" if h else f"{m:02d}:{sec:02d}"

    def _stats(self):
        elapsed = time.monotonic() - self._start if self._start else 0.0
        rate = self._rate or (self.n / elapsed if elapsed > 0 else 0.0)
        eta = (
            max(0, self.total - self.n) / rate
            if self.total is not None and rate > 0
            else None
        )
        frac = (
            self.n / self.total
            if self.total not in {None, 0}
            else (1.0 if self.total == 0 else 0.0)
        )
        return elapsed, rate, eta, frac

    # ── Renderers ──

    def _render_html(self):
        elapsed, rate, eta, frac = self._stats()

        if self.total is not None:
            pct = max(0.0, min(100.0, frac * 100))
            bar = (
                f'<span style="display:inline-block; width:{self._BAR_PX}px; '
                f'height:12px; border:1.2px solid currentColor; '
                f'vertical-align:middle; margin:0 10px; background:none; '
                f'box-sizing:border-box">'
                f'<span style="display:block; width:{pct:.2f}%; height:100%; '
                f'background:currentColor; opacity:0.85"></span></span>'
            )
            label = f"{pct:5.1f}%"
            stats = (
                f"{self.n}/{self.total} "
                f"[{self._fmt_time(elapsed)}&lt;{self._fmt_time(eta)}, "
                f"{rate:.2f} it/s]"
            )
        else:
            bar = (
                f'<span style="display:inline-block; width:{self._BAR_PX}px; '
                f'text-align:center; margin:0 10px; vertical-align:middle; '
                f'opacity:0.7">·  ·  ·</span>'
            )
            label = f"{self.n}"
            stats = f"[{self._fmt_time(elapsed)}, {rate:.2f} it/s]"

        desc = (
            f'<span style="font-weight:bold">{_html.escape(self.desc)}:</span> '
            if self.desc else ''
        )

        metrics = "".join(
            f' <span><strong>{_html.escape(str(key))}</strong>={_html.escape(str(value))}</span>'
            for key, value in self._metrics.items()
        )
        return (
            f'<div style="font-family:{self._FONT}; color:currentColor; '
            f'font-size:13px; margin:6px 0; line-height:1.6; background:none">'
            f'{desc}'
            f'<span style="display:inline-block; min-width:48px; '
            f'text-align:right">{label}</span>'
            f'{bar}'
            f'<span style="font-size:12px">{stats}{metrics}</span>'
            f'</div>'
        )

    def _render_text(self):
        elapsed, rate, eta, frac = self._stats()
        prefix = f"{self.desc}: " if self.desc else ""
        if self.total is not None:
            frac_clamped = max(0.0, min(1.0, frac))
            filled = int(self.width * frac_clamped)
            bar = "█" * filled + "·" * (self.width - filled)
            pct = frac_clamped * 100
            output = (
                f"{prefix}{pct:5.1f}% |{bar}| "
                f"{self.n}/{self.total} "
                f"[{self._fmt_time(elapsed)}<{self._fmt_time(eta)}, "
                f"{rate:.2f} it/s]"
            )
        else:
            output = (
                f"{prefix}{self.n} "
                f"[{self._fmt_time(elapsed)}, {rate:.2f} it/s]"
            )
        if self._metrics:
            output += " " + " ".join(f"{key}={value}" for key, value in self._metrics.items())
        return output

    def to_text(self) -> str:
        """Return the current progress state as plain text."""
        return self._render_text()

    def to_html(self) -> str:
        """Return the current progress state as portable HTML."""
        return self._render_html()

    def _repr_mimebundle_(self, include=None, exclude=None) -> dict[str, str]:
        return {"text/plain": self.to_text(), "text/html": self.to_html()}

    # ── Refresh ──

    def _refresh(self, force=False):
        now = time.monotonic()
        if not force and (now - self._last) < self.mininterval:
            return
        self._last = now

        if self._jupyter:
            from IPython.display import display, HTML
            html = HTML(self._render_html())
            if self._handle is None:
                self._handle = display(html, display_id=True)
            else:
                self._handle.update(html)
        elif sys.stdout.isatty():
            sys.stdout.write("\r\033[K" + self._render_text())
            sys.stdout.flush()

    # ── Public API ──

    def update(self, n: int | float = 1) -> None:
        """Advance the counter by ``n`` and refresh if throttled interval has elapsed."""
        if self._finished:
            raise RuntimeError("Cannot update a finished Progress.")
        if not isinstance(n, (int, float)) or isinstance(n, bool) or n < 0:
            raise ValueError("n must be a non-negative number.")
        if self._start is None:
            self._start = time.monotonic()
        now = time.monotonic()
        self.n += n
        if self._rate_time is not None and now > self._rate_time:
            instant_rate = (self.n - self._rate_n) / (now - self._rate_time)
            if self._rate == 0.0:
                self._rate = instant_rate
            else:
                self._rate = (
                    self.smoothing * instant_rate
                    + (1 - self.smoothing) * self._rate
                )
        self._rate_n = self.n
        self._rate_time = now
        is_done = self.total is not None and self.n >= self.total
        self._refresh(force=is_done)

    def set_description(self, desc: str) -> None:
        """Change the prefix label and force a refresh."""
        self.desc = desc
        self._refresh(force=True)

    def set(self, **metrics: object) -> None:
        """Set displayed metrics and refresh when the interval has elapsed."""
        self._metrics.update(metrics)
        self._refresh(force=False)

    def finish(self) -> None:
        """Preserve the final progress state in the current environment."""
        if self._finished:
            return
        if self._jupyter or sys.stdout.isatty():
            self._refresh(force=True)
        else:
            sys.stdout.write(self._render_text())
        if not self._jupyter:
            sys.stdout.write("\n")
            sys.stdout.flush()
        self._finished = True

    # ── Iterator + context manager ──

    def __iter__(self) -> Iterator[_T]:
        if self.iterable is None:
            raise TypeError("Progress has no iterable; use update() instead.")
        if self._start is None:
            self._start = time.monotonic()
        self._refresh(force=True)
        try:
            for item in self.iterable:
                yield item
                self.update(1)
        finally:
            self.finish()

    def __enter__(self) -> "Progress[_T]":
        if self._start is None:
            self._start = time.monotonic()
        self._refresh(force=True)
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> Literal[False]:
        self.finish()
        return False
