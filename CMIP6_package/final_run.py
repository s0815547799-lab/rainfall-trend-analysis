"""
final_run.py — reproducible end-to-end run with versioned, QC-gated release.

Pipeline: data → validation → ensemble → rainfall → 3-level results → publication
tables → GIS figures → Figure QC. Writes a timestamped RELEASE_YYYYMMDD_HHMMSS
directory (never overwrites); only if QC passes does CURRENT_RELEASE point to it.
"""
from __future__ import annotations

import logging
import shutil
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from main import run
from src.figures.make import generate_all
from src.tables.results import (level1_station_model, level2_station_mme,
                                 level3_area_summary, publication_tables)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("final_run")


# ---------------------------------------------------------------------------
# Figure QC
# ---------------------------------------------------------------------------

def _qc_raster(path: Path, target_dpi: int = 600, min_width_px: int = 1000
               ) -> dict:
    """Open a raster image and return QC metrics.

    Pillow reads DPI from the pHYs (PNG) or JFIF/EXIF (TIFF) metadata chunk.
    Returns a dict with keys: figure, format, width_px, height_px, dpi, dpi_ok, size_ok.
    """
    from PIL import Image
    im = Image.open(path)
    raw_dpi = im.info.get("dpi", (0, 0))
    # dpi may be a float tuple or a single value
    dpi_x = raw_dpi[0] if isinstance(raw_dpi, (tuple, list)) else raw_dpi
    dpi_val = int(round(float(dpi_x))) if dpi_x else 0
    return {
        "figure":   path.name,
        "format":   path.suffix.lstrip(".").upper(),
        "width_px": im.size[0],
        "height_px": im.size[1],
        "dpi":      dpi_val,
        "dpi_ok":   dpi_val == target_dpi,
        "size_ok":  im.size[0] >= min_width_px,
    }


def figure_qc(fig_dir: Path,
              target_dpi: int = 600,
              min_width_px: int = 1000) -> tuple[pd.DataFrame, bool]:
    """Check DPI and minimum width for all PNG and TIFF publication figures.

    PDF is skipped (cannot be reliably DPI-checked via Pillow without rasterising).
    A separate PDF existence check is performed to confirm files were written.
    """
    rows = []
    for fmt in ("*.png", "*.tiff", "*.tif"):
        for p in sorted(fig_dir.glob(fmt)):
            try:
                rows.append(_qc_raster(p, target_dpi, min_width_px))
            except Exception as exc:
                log.warning("QC: could not open %s — %s", p.name, exc)
                rows.append({
                    "figure": p.name, "format": p.suffix.lstrip(".").upper(),
                    "width_px": 0, "height_px": 0,
                    "dpi": 0, "dpi_ok": False, "size_ok": False,
                })

    # PDF existence check (presence only)
    pdfs = list(fig_dir.glob("*.pdf"))
    pdf_ok = len(pdfs) > 0

    qc = pd.DataFrame(rows)
    if qc.empty:
        passed = False
    else:
        passed = bool(qc.dpi_ok.all() and qc.size_ok.all() and pdf_ok)
    return qc, passed


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    t0    = time.time()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    root  = Path("outputs")
    rel   = root / f"RELEASE_{stamp}"
    for sub in ["station_model", "station_mme", "area_summary",
                "publication_tables", "publication_figures", "release", "logs"]:
        (rel / sub).mkdir(parents=True, exist_ok=True)

    # 1) end-to-end compute
    d   = run()
    cfg = d["cfg"]
    f0, f1 = cfg["periods"]["near_future"]

    # 2) 3-level results
    level1_station_model(d["per"], rel)
    _, station_mme = level2_station_mme(
        d["bc_mme"], d["raw_mme"], d["vm"], d["change"], rel, f0, f1)
    _, area = level3_area_summary(d["obs"], d["bc_mme"], d["change"], rel, f0, f1)

    # 3) publication tables
    publication_tables(d["meta"], d["vm"], d["change"], d["per"], station_mme, rel)

    # 4) figures
    cfg_fig = dict(cfg)
    cfg_fig["paths"] = dict(cfg["paths"])
    cfg_fig["paths"]["outputs"] = str(rel)
    (rel / "figures").mkdir(exist_ok=True)
    saved = generate_all(d, cfg_fig)

    # move figures → publication_figures
    figdir = rel / "figures"
    for f in figdir.glob("*"):
        shutil.move(str(f), rel / "publication_figures" / f.name)
    if figdir.exists():
        figdir.rmdir()

    # 5) Figure QC (PNG + TIFF DPI check; PDF existence check)
    qc, passed = figure_qc(rel / "publication_figures",
                           target_dpi=cfg["figures"]["dpi"])
    qc.to_excel(rel / "release" / "FIGURE_QC.xlsx", index=False)

    pdf_count = len(list((rel / "publication_figures").glob("*.pdf")))
    with open(rel / "FIGURE_QC_REPORT.md", "w") as f:
        f.write(f"# FIGURE_QC_REPORT — {stamp}\n\n")
        f.write(
            f"Raster files checked: {len(qc)} | "
            f"DPI {cfg['figures']['dpi']}: {qc.dpi_ok.all() if not qc.empty else 'N/A'} | "
            f"Size OK: {qc.size_ok.all() if not qc.empty else 'N/A'} | "
            f"PDFs present: {pdf_count}\n\n"
        )
        if not qc.empty:
            f.write(qc.to_markdown(index=False))
        f.write(f"\n\n**Journal readiness: {'PASS ✓' if passed else 'FAIL ✗'}**\n")

    # 6) Runtime summary
    runtime = time.time() - t0
    pd.DataFrame([{
        "stamp":        stamp,
        "runtime_s":    round(runtime, 1),
        "figures_checked": len(qc),
        "pdfs_present": pdf_count,
        "qc_pass":      passed,
    }]).to_excel(rel / "release" / "RUNTIME_SUMMARY.xlsx", index=False)

    log.info("RELEASE %s | raster_files=%d | PDFs=%d | QC=%s | %.1fs",
             stamp, len(qc), pdf_count, "PASS" if passed else "FAIL", runtime)

    # 7) CURRENT_RELEASE symlink (only if QC passes)
    if passed:
        cur = root / "CURRENT_RELEASE"
        if cur.exists() or cur.is_symlink():
            cur.unlink()
        try:
            cur.symlink_to(rel.name)
        except OSError:
            (root / "CURRENT_RELEASE.txt").write_text(rel.name)
        log.info("CURRENT_RELEASE → %s", rel.name)
    else:
        log.error("QC FAILED — CURRENT_RELEASE not updated. See %s", rel / "FIGURE_QC_REPORT.md")

    return rel, passed


if __name__ == "__main__":
    main()
