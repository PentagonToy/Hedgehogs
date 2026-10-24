# Legend placement experiment

`legend_grid.py` reuses the packaged default hybrid and exposes classic/grid-only comparisons for development. No ML dependency is required.

The policy evaluates an occupancy grid using all finite visible scatter points, supported lines and text. Plot coordinates and vector output remain intact.

This is a bounded approximation. It evaluates a spatial cost map rather than proving a continuous global optimum or predicting human preference. Complex artists, long paths and unsupported axes fall back to the existing policy. Matplotlib and Hedgehogs both use ten named location codes; `right` and `center right` coincide, giving nine distinct standard positions.

The [mathematical design](../../docs/developer/legend-experiment.md) defines costs, tie-breaking and hybrid acceptance.

## Run the comparison

From the repository root with its existing plotting dependencies:

```console
python tools/experiments/compare_legend_grid.py --output /path/to/results --points 10000 100000
```

The explicit script compares fixed locations, grid placement and native Matplotlib on synthetic patterns. Placement timings use the same finished figure and renderer; the two show-pipeline observations also include rendering and have shared-process cache effects. Inspect exact overlap scores and exported figures, not timing alone.

## Validate the hybrid

```console
python tools/experiments/validate_hybrid.py --output /path/to/results
python tools/experiments/validate_notebook.py /path/to/notebook-results
```

These explicit scripts audit three acceptance thresholds across synthetic settings, measure placement and first-show costs up to one million points, and execute the existing synthetic plotting notebook in isolated directories. The hybrid accepts data-only changes after at least 10% exact-score improvement; ties keep the classic placement. A zero-overlap conventional location skips the grid. This engineering preference is separate from the grid's mathematical objective.
