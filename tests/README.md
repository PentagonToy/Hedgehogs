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

## Explicit load measurements

Ordinary pytest runs and automatic CI skip load tests. Enable them only on explicit request with `--run-load`; selecting their file or marker alone leaves them skipped.

```bash
python -m pytest tests/load -q --run-load --load-report /path/to/output/scatter-load.json
```

| Case | Measurement |
| --- | --- |
| 10,000, 100,000 and 1,000,000 points | Native Matplotlib and Hedgehogs, fixed and automatic legends, first and repeated display |
| Four scatter collections, 100,000 and 1,000,000 total points | Automatic finishing, coordinate preservation and repeat geometry |
| 100,000-point PDF | Vector and explicitly rasterised export time and file size |

Data generation is outside the timed region. Native cases keep initial style settings but disable Hedgehogs hooks; final typography and placement policies can differ. Display windows are suppressed, so timings cover preparation and drawing. Measurements are single observations with shared-process cache effects; elapsed time has no pass threshold.

Store JSON reports outside the source tree with source changes and hardware details. Reports record the interpreter, library versions, source commit, pending changes, timings and output sizes. Rerun only when explicitly requested.

## Regression criteria

Test observable behaviour: preserved data, explicit author settings, readable sizing, representative containment and stable repeated output. Run font-sensitive cases with the configured serif family and DejaVu Serif. Ordinary legend fitting may exceed its 60% width target at the scaled 6 pt font floor; see [Legend fitting and limits](../docs/developer/presentation.md#legend-fitting-and-limits).

Same-environment repeatability does not require identical automatic placement across versions or with native Matplotlib. Compare cached and uncached paths when validating a result-preserving optimisation. Inspect upstream layout changes against the behavioural criteria before updating expectations; see [Reference behaviour and reproducibility](../docs/developer/presentation.md#reference-behaviour-and-reproducibility).

Distinguish non-interactive rendering checks from native GUI checks. Measure test costs before optimising a slow case; retain its behavioural coverage. Keep timings and experiment results in execution reports.
