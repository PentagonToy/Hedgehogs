# Validation rules

Select checks from the changed behaviour. Keep the development loop small; expand validation after a concrete failure, a cross-module change or release preparation. Passing tests validate behaviour, while representative figures validate appearance.

## Choose the smallest useful check

| Change | Check |
| --- | --- |
| Markdown, links or signature wrapping | Read the diff and check local links; no Python tests or rendering |
| Figure appearance | Render the requested figure once and run `presentation_smoke` |
| Finishing or rendering behaviour | Run the affected presentation or scaling tests |
| Tree or pairplot behaviour | Run its test file; inspect one representative figure |
| Tables or terminal output | Run the affected test file |
| Public namespace | Run `tests/core/test_public_api.py` and affected consumers |
| Packaging or release | Build and check distributions; run the full suite once |

## Fast presentation check

```bash
python -m pytest tests/plots/test_presentation.py -q -m presentation_smoke
```

The three selected tests cover finishing with preserved data, explicit author choices and outline sizing. They are a development check, not a replacement for the full regression suite.

## Full validation

```bash
python -m pytest -q -ra
python -m mypy
```

Run full validation once after functional changes have settled, or before release. Repeat it only after a relevant code change, failure or newly identified risk. Source unchanged since a passing run does not need another full run because documentation, a commit message or a Git hash changed.

CI checks supported Python versions in parallel. Push settled changes once; allow CI to finish in the background during ordinary development. Confirm its outcome before tagging or publishing. Markdown-only pushes skip runtime CI; release checks still validate the built description and source archive.

## Tests and performance

Add tests for observable behaviour and regressions rather than mirroring implementation details. Preserve coverage for author overrides, repeated rendering, scientific coordinates and output formats. Optimise a slow test only after measuring its cost; do not remove coverage merely to shorten a run.

Recent local full-suite runs took about 20–30 seconds, while Linux CI test jobs took about 53–70 seconds per Python version. Those timings depend on the environment. Separate test duration, CI setup and the time spent designing changes when reporting a delay.
