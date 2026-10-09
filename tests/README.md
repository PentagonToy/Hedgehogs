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

Load tests are skipped in ordinary pytest runs and automatic CI. Run them only after an explicit request, using `--run-load`; selecting the file or the `load` marker alone does not enable them.

```bash
python -m pytest tests/load -q -s --run-load --load-report /path/to/output/scatter-load.json
```

The scatter checks use seeded data at 10,000, 100,000 and 1,000,000 points. Both native Matplotlib drawing and Hedgehogs finishing use fixed placement and `loc="best"`, then measure a second unchanged display. The native cases retain the same initial style settings but disable Hedgehogs rendering hooks; finishing can refine typography and placement, so final appearance and placement policies are not identical. Record legend locations and bounds alongside timings. Separate 100,000-point cases measure vector and rasterised PDF output. Native display windows are suppressed; timings cover drawing and `plots.show()` preparation rather than GUI interaction. Data and repeated geometry must remain unchanged.

Record the source commit, pending changes, interpreter, library versions and hardware with each result. The JSON report records runtime metadata, timings and PDF sizes. Data generation is outside the timed region; artist creation is reported separately. Measurements are single observations in a shared process with font-cache effects, not statistical benchmarks or machine-independent performance guarantees. No elapsed-time threshold determines success. Keep reports outside the source tree; rerun only when explicitly requested.

## Tests and performance

### Font-sensitive figure checks

When changing typography, tick lengths or legend spacing, run affected cases with both the configured serif family and explicit DejaVu Serif. A local Times New Roman result does not establish fallback-font behaviour on Linux. Measure bounds with the current renderer and check minimum readable text, placement, author overrides and stable repeated draws.

The ordinary legend renderer targets 60% of axes width but retains a 6 pt reference-scale font floor. Tests must allow the target to be exceeded when that floor is reached; representative legends must still fit their axes. Do not remove the readability floor or relax containment merely to satisfy a pixel-width assertion. Finishing through `plots.show()` or `plots.save()` has a separate placement policy; see [Legend fitting and limits](../docs/developer/presentation.md#legend-fitting-and-limits).

Exercise repeated finishing and output without changing data or accumulating size changes. Distinguish non-interactive preparation and export checks from native GUI display checks when reporting coverage. Documentation-only updates need diff, link and numerical consistency checks, without rerunning Python tests.

### Regression scope

Add tests for observable behaviour and regressions rather than mirroring implementation details. Preserve coverage for author overrides, repeated rendering, scientific coordinates and output formats. Optimise a slow test only after measuring its cost; do not remove coverage merely to shorten a run.

Separate deterministic repeatability in the same environment from equality across versions or with native Matplotlib. Use native Matplotlib as the reference for artist and placement semantics, but do not require Hedgehogs finishing to choose its exact automatic legend position. Compare cached and uncached paths under the same conditions when validating a result-preserving optimisation. Across dependency versions, verify data preservation, explicit locations and anchors, bounded readable sizing, representative containment and absence of cumulative drift. If an upstream change moves an automatic legend, inspect the cause before updating expectations; a changed position alone is not a regression, and upstream changes do not excuse clipping, lost data or ignored author settings. See [Reference behaviour and reproducibility](../docs/developer/presentation.md#reference-behaviour-and-reproducibility).

Recent local full-suite runs took about 20–30 seconds, while Linux CI test jobs took about 53–70 seconds per Python version. Those timings depend on the environment. Separate test duration, CI setup and the time spent designing changes when reporting a delay.
