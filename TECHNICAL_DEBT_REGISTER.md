# Technical Debt Register
**Project:** Rainfall Trend Analysis — Phetchaburi–Prachuap Khiri Khan River Basin, Western Thailand (1981–2014)
**Repository:** `s0815547799-lab/rainfall-trend-analysis`
**Register date:** 2026-05-29
**Source:** RELEASE_READINESS_REPORT.md (audit date 2026-05-29)

---

## Preamble

This register documents all known technical debt items that remain open after the Priority-1 remediation commit **ede43b2**. That commit resolved all Blocking and High severity issues identified in REPRODUCIBILITY_AUDIT.md (HP-1, HP-2, HP-3, DEP-1, MG-1, MG-2). The items below are Medium and Low severity only.

**None of the items in this register block journal submission or prevent future pipeline extensions from being started.** They represent known limitations, missing infrastructure, and peripheral script issues that are accepted as reasonable trade-offs given the project scope and timeline.

---

## Summary Table

| ID | Severity | Description | Risk | Status |
|---|---|---|---|---|
| M-1 | Medium | `generate_q1_maps.py` lacks `__main__` guard; shapefile not in repo | Medium | Accepted Technical Debt |
| M-2 | Medium | `Comparative_4MMK.py` non-functional — `statsmodels` not installed | Low–Medium | Accepted Technical Debt |
| M-3 | Medium | TIFF figures excluded from repo (>100 MB); require local regeneration before submission | Low | Accepted Technical Debt |
| M-4 | Medium | Taylor Diagram (Fig09) generates 6x matplotlib y-limit warnings (cosmetic) | Low | Deferred |
| L-1 | Low | No unit tests for statistical functions | Medium (future) | Accepted Technical Debt |
| L-2 | Low | No CI/CD configuration | Low–Medium | Accepted Technical Debt |
| L-3 | Low | `pyproject.toml` absent — no `python_requires` or optional-extras metadata | Low | Accepted Technical Debt |
| L-4 | Low | `rainfall_trend_analysis_v5.py` in repo without documentation | Low | Accepted Technical Debt |
| L-5 | Low | `calval_split.py` input files absent from repo | Low | Out of Scope |

---

## Medium Severity Items

---

### M-1

| Field | Detail |
|---|---|
| **ID** | M-1 |
| **Severity** | Medium |
| **Description** | `generate_q1_maps.py` lacks a `if __name__ == "__main__":` guard. The script also requires the shapefile `30_amarea_prachuap_khiri_khan.shp` plus its sidecar files (`.dbf`, `.prj`, `.shx`) which are not committed to the repository. |
| **Impact on production use** | (a) Importing the module as a library triggers immediate top-level execution. (b) Running the script on a clean machine fails with a shapefile-not-found error before producing any output. Geographic Q1 maps cannot be regenerated without the shapefile. |
| **Risk level** | Medium |
| **Recommended fix** | Add `if __name__ == "__main__":` guard at the entry point. Commit the shapefile set to `data/boundaries/` (files are already present in the working directory root; they need only to be moved and committed) or document a public download source. This was identified as Priority-2 in REPRODUCIBILITY_AUDIT.md and remains open. |
| **Estimated effort** | 1–2 hours (guard + file move + commit) |
| **Resolution status** | Accepted Technical Debt |
| **Rationale** | Geographic Q1 maps are supplemental output, not primary journal figures. The shapefile exists locally and the script produces correct output when run manually. The missing guard does not affect the primary pipeline (`rainfall_trend_analysis_v4.py`) and does not block journal submission. |

---

### M-2

| Field | Detail |
|---|---|
| **ID** | M-2 |
| **Severity** | Medium |
| **Description** | `Comparative_4MMK.py` is non-functional in the current environment. The script imports `statsmodels.api`, `durbin_watson`, `acf`, `pacf`, `adfuller`, and `acorr_ljungbox` at module level. `statsmodels` is not installed, causing an immediate `ModuleNotFoundError`. The `requirements.txt` lists `statsmodels>=0.13` but marks it as required by this script only ("extended: Comparative_4MMK.py only") and it is not present in the active environment. |
| **Impact on production use** | Running `Comparative_4MMK.py` fails immediately. No output is produced. This script is standalone and is not called by the primary pipeline, so the primary trend analysis workflow is unaffected. |
| **Risk level** | Low for primary pipeline; Medium if a collaborator attempts to run the comparative analysis |
| **Recommended fix** | Install `statsmodels` (`pip install statsmodels>=0.13`) and verify the script runs end-to-end. Alternatively, add a runtime import check at the top of `Comparative_4MMK.py` with an informative error message (`"statsmodels is required: pip install statsmodels>=0.13"`). Consider relocating the script to a `scripts/extended/` subdirectory with its own README to signal it is not part of the primary pipeline. |
| **Estimated effort** | 30 minutes (install + verification) or 2 hours (relocation + README) |
| **Resolution status** | Accepted Technical Debt |
| **Rationale** | `Comparative_4MMK.py` is an extended standalone utility, documented as such in `requirements.txt`. Its non-functionality does not affect scientific results or journal submission. The fix is trivial once `statsmodels` is installed in the target environment. |

---

### M-3

| Field | Detail |
|---|---|
| **ID** | M-3 |
| **Severity** | Medium |
| **Description** | TIFF-format figures are generated locally during `generate_trend_comparison_analysis.py` execution (10 files confirmed present in `results/final_N33_v5/publication_maps_v51/` locally, e.g., `Fig_Modified_MK.tif`) but are excluded from version control by `.gitignore` (`*.tif` pattern). Individual TIFF files exceed 100 MB each at 600 DPI, making repository storage impractical. Most Q1 hydrology journals (Journal of Hydrology, Water Resources Research, Journal of Hydrometeorology) require figure submission in TIFF at 300–600 DPI. Primary pipeline figures (Fig01–FigSP4) do not generate TIFF output. |
| **Impact on production use** | No TIFF archive exists in the repository. Before submitting to a journal that requires TIFF, all figures must be regenerated locally and verified. The regeneration is deterministic (fixed seed, committed inputs), so results will be identical. |
| **Risk level** | Low |
| **Recommended fix** | Document in README and in `FIGURE_INVENTORY.md` that TIFF files must be generated locally before submission. Note expected file sizes so contributors are not surprised. Alternatively, submit figures in PDF (which IS committed to the archive) — many Q1 journals now accept PDF figures at equivalent resolution. |
| **Estimated effort** | Documentation: 30 minutes. Regeneration before submission: 10–20 minutes pipeline runtime. |
| **Resolution status** | Accepted Technical Debt |
| **Rationale** | Repository storage of multi-hundred-MB binary files is impractical and contra Git best practices. The figures are fully reproducible from committed code and data. This is a submission-workflow note, not a scientific or engineering gap. |

---

### M-4

| Field | Detail |
|---|---|
| **ID** | M-4 |
| **Severity** | Medium |
| **Description** | Fig09 (Taylor Diagram) generates 6 runtime warnings of the form `"Ignoring fixed y limits to fulfill fixed data aspect with adjustable data limits"` during execution of `rta/figures/taylor.py`. These are emitted by matplotlib's aspect-ratio adjustment logic and are cosmetic — the figure is rendered correctly. |
| **Impact on production use** | No impact on the figure output. Warnings appear in execution logs and may concern a first-time collaborator. In a CI/CD environment they would pollute log output and potentially trigger warning-level checks. |
| **Risk level** | Low |
| **Recommended fix** | Suppress the warnings within the Taylor diagram rendering block using `warnings.filterwarnings("ignore", "Ignoring fixed y limits")` scoped to the relevant lines in `rta/figures/taylor.py`. This is a one-line fix that does not affect figure output. |
| **Estimated effort** | 15 minutes |
| **Resolution status** | Deferred |
| **Rationale** | The figure is correct. The fix is trivial but was not prioritized during the remediation cycle. It should be applied before setting up CI/CD (L-2) to prevent log noise in automated runs. |

---

## Low Severity Items

---

### L-1

| Field | Detail |
|---|---|
| **ID** | L-1 |
| **Severity** | Low |
| **Description** | No unit tests or integration test suite exists. There is no `tests/` directory, no `test_*.py` files, and no test runner configuration (`pytest.ini`, `tox.ini`, etc.). Correctness of the statistical implementations (Standard MK, Modified MK, PW-MK, TFPW-MK, Sen's slope) has been verified only by end-to-end pipeline execution against the known dataset and by cross-checking against the committed results workbook. |
| **Impact on production use** | No impact on current results. All statistical implementations are verified against known values. However, any future refactor of `rta/trend_tests.py`, `rta/pw.py`, or `rta/tfpw.py` has no regression protection — a change could silently alter results without any automated detection. |
| **Risk level** | Low for current state; Medium for any future modification of statistical modules |
| **Recommended fix** | Add a `tests/` directory with at minimum 3–5 unit tests for core statistical functions, using known result values as expected outputs (e.g., `standard_mk()` should return a specific Z-value for a known station-scale combination; `sens_slope()` should return a specific β). This is a prerequisite for the repository to be considered "ready for future extensions." |
| **Estimated effort** | 4–8 hours (writing tests + establishing test data fixtures) |
| **Resolution status** | Accepted Technical Debt |
| **Rationale** | Unit test coverage was not part of the original project scope. The current state is appropriate for a single-dataset research pipeline. Tests become important before any collaborative development or codebase extension and should be added at that point. |

---

### L-2

| Field | Detail |
|---|---|
| **ID** | L-2 |
| **Severity** | Low |
| **Description** | No CI/CD configuration exists. The `.github/` directory is absent. There are no GitHub Actions workflows, no Travis CI, and no other automated testing on push or pull request. |
| **Impact on production use** | No impact on current results. A future contributor could break the pipeline without any automated detection. |
| **Risk level** | Low for current state; Medium for collaborative development |
| **Recommended fix** | Add a minimal GitHub Actions workflow (`.github/workflows/smoke_test.yml`) that runs `pip install -r requirements.txt` and executes the pipeline against the committed test CSV as a smoke test. Estimated runtime is approximately 5 minutes on a standard GitHub runner. This should be implemented after L-1 (unit tests) so the workflow has tests to run. |
| **Estimated effort** | 2–4 hours (workflow YAML + runner configuration + first successful run) |
| **Resolution status** | Accepted Technical Debt |
| **Rationale** | CI/CD was not part of the original project scope. For a single-researcher pipeline operating on a fixed dataset, manual verification is sufficient. It becomes important before collaborative development and should be implemented alongside or after L-1. |

---

### L-3

| Field | Detail |
|---|---|
| **ID** | L-3 |
| **Severity** | Low |
| **Description** | `pyproject.toml` is absent. There is also no `setup.py` or `setup.cfg`. The repository has no formal package metadata: no `python_requires` specification, no declared optional-extras for `statsmodels`, `pyproj`, or `pyshp`, and no mechanism for `pip install .` installation. |
| **Impact on production use** | No impact on current use. The repository is operated as a script collection, not an installable package. Dependency information is provided in `requirements.txt`. |
| **Risk level** | Low |
| **Recommended fix** | Add a minimal `pyproject.toml` with a `[project]` section including `name`, `version`, and `python_requires = ">=3.7"`. Declare optional dependencies under `[project.optional-dependencies]` with an `extended` extra covering `statsmodels>=0.13` and a `spatial` extra covering `pyproj` and `pyshp`. This was identified as Priority-3 in REPRODUCIBILITY_AUDIT.md. |
| **Estimated effort** | 1–2 hours |
| **Resolution status** | Accepted Technical Debt |
| **Rationale** | The absence of `pyproject.toml` does not affect any current workflow. Adding it is a packaging best-practice improvement that would benefit future users attempting to install the `rta` package in other projects. It is appropriate to address this when the codebase is prepared for broader distribution or for extension as a reusable library. |

---

### L-4

| Field | Detail |
|---|---|
| **ID** | L-4 |
| **Severity** | Low |
| **Description** | `rainfall_trend_analysis_v5.py` is present in the repository root but is not mentioned in `CLAUDE.md`, `README.md`, or `CHANGELOG.md`. It is described in `REPRODUCIBILITY_AUDIT.md §12` as a "development version." The script requires a `boundaries/` directory that is not committed to the repository. |
| **Impact on production use** | No impact. The primary analysis scripts are `rainfall_trend_analysis_v3.py` and `rainfall_trend_analysis_v4.py` (v4 is current). A collaborator encountering v5 has no guidance on its status, whether it supersedes v4, or how to use it. |
| **Risk level** | Low |
| **Recommended fix** | Either (a) add a note to `CLAUDE.md` and `README.md` stating that v5 is a development version not yet production-ready, with v4 remaining the current publication version, or (b) move `rainfall_trend_analysis_v5.py` to a `dev/` branch until it is ready to replace v4. Option (a) is the lower-effort path. |
| **Estimated effort** | 30 minutes (documentation update) or 1 hour (branch management) |
| **Resolution status** | Accepted Technical Debt |
| **Rationale** | The presence of an undocumented development script is low-consequence for the current single-researcher workflow. Documentation is the appropriate remedy and is deferred until v5 development is further along. |

---

### L-5

| Field | Detail |
|---|---|
| **ID** | L-5 |
| **Severity** | Low |
| **Description** | `calval_split.py` is a standalone bias-correction utility that requires three input Excel files from the ACCESS-ESM1-5 climate model output. These files are not in the repository and are not publicly available. Running `calval_split.py` on a clean machine raises `FileNotFoundError` pointing to `data/calval/`. The Priority-1 remediation (commit ede43b2) replaced hardcoded `/mnt/user-data/` paths with relative paths and added a `__main__` guard, so the failure is now clean and informative rather than cryptic. |
| **Impact on production use** | No impact on the trend analysis pipeline. `calval_split.py` is explicitly out of scope for the primary analysis. It is a convenience utility for a separate bias-correction workflow that uses different input data. |
| **Risk level** | Low |
| **Recommended fix** | Add a data availability note in the `calval_split.py` module docstring explaining that the three required input files come from ACCESS-ESM1-5 climate model output and are available from [source] upon request. Consider moving the script to a `scripts/bias_correction/` subdirectory with a short README to clearly signal it is not part of the primary pipeline. |
| **Estimated effort** | 30 minutes (docstring + optional file move) |
| **Resolution status** | Out of Scope |
| **Rationale** | This utility addresses a separate scientific workflow (climate model bias correction) that is outside the scope of the Phetchaburi–Prachuap Khiri Khan trend analysis. Its input data cannot be committed to the repository because it is climate model output from an external source. The script is retained as a reference implementation but is not maintained as part of this project. No action is required to support journal submission or future extensions of the trend analysis pipeline. |

---

## Resolved Issues (not counted above)

The following issues from `REPRODUCIBILITY_AUDIT.md` were fully resolved in the Priority-1 remediation commit **ede43b2** and are recorded here for traceability. None of these items are open.

| ID | Original severity | Resolution |
|---|---|---|
| HP-1 | Blocking | `generate_trend_comparison_analysis.py`: hardcoded WB4 path replaced with environment-variable lookup and `data/reference/` relative fallback |
| HP-2 | Blocking | `generate_trend_comparison.py`: same path fix as HP-1 |
| HP-3 | Blocking | `calval_split.py`: `/mnt/user-data/` absolute paths replaced with relative paths; `main()` guard added |
| DEP-1 | High | `requirements.txt` created with tested package versions |
| MG-1 | High | `calval_split.py` `__main__` guard added (resolved as part of HP-3) |
| MG-2 | High | Confirmed no other scripts with bare module-level execution side effects in the primary pipeline |

---

*This register covers all items open as of 2026-05-29. It should be updated when items are resolved or when new debt is identified. Blocking and High issues from the pre-ede43b2 state are documented in REPRODUCIBILITY_AUDIT.md for historical reference.*
