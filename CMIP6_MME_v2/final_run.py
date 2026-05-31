"""
final_run.py — Reproducible end-to-end run with versioned, QC-gated release.

Pipeline:
  data → validation → ensemble → seasonal rainfall → 3-level results →
  publication tables → figures (7 figures × single/double × 3 formats) →
  Figure QC gate → CURRENT_RELEASE symlink (only if QC passes).

Each run writes a timestamped RELEASE_YYYYMMDD_HHMMSS directory that is
never overwritten. CURRENT_RELEASE points to the latest QC-passing release.

วิธีรัน:
  python final_run.py                      # ใช้ config/config.yaml
  python final_run.py --cfg path/to/config.yaml
"""
from __future__ import annotations

import argparse
import logging
import shutil
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from main import run
from src.figures.make  import generate_all
from src.tables.results import (level1_station_model, level2_station_mme,
                                  level3_area_summary, publication_tables)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("final_run")


# ── Figure QC ─────────────────────────────────────────────────────────────────

def _qc_raster(path: Path, target_dpi: int, min_width_px: int) -> dict:
    """Open a raster image and return QC metrics."""
    from PIL import Image
    im  = Image.open(path)
    raw = im.info.get("dpi", (0, 0))
    dpi_x   = raw[0] if isinstance(raw, (tuple, list)) else raw
    dpi_val = int(round(float(dpi_x))) if dpi_x else 0
    return {
        "figure":    path.name,
        "format":    path.suffix.lstrip(".").upper(),
        "width_px":  im.size[0],
        "height_px": im.size[1],
        "dpi":       dpi_val,
        "dpi_ok":    dpi_val == target_dpi,
        "size_ok":   im.size[0] >= min_width_px,
    }


def figure_qc(fig_dir: Path,
              target_dpi: int = 600,
              min_width_px: int = 1000) -> tuple[pd.DataFrame, bool]:
    """Check DPI and minimum width for all PNG and TIFF publication figures.

    PDF existence is checked separately (Pillow cannot reliably read PDF DPI
    without rasterising). A QC PASS requires:
      • At least one raster file checked
      • All PNG and TIFF files at target_dpi and ≥ min_width_px
      • At least one PDF present
    """
    rows = []
    for glob in ("*.png", "*.tiff", "*.tif"):
        for p in sorted(fig_dir.glob(glob)):
            try:
                rows.append(_qc_raster(p, target_dpi, min_width_px))
            except Exception as exc:
                log.warning("QC: cannot open %s — %s", p.name, exc)
                rows.append({
                    "figure": p.name, "format": p.suffix.lstrip(".").upper(),
                    "width_px": 0, "height_px": 0,
                    "dpi": 0, "dpi_ok": False, "size_ok": False,
                })

    pdf_count = len(list(fig_dir.glob("*.pdf")))
    qc        = pd.DataFrame(rows)
    passed    = bool(
        not qc.empty
        and bool(qc.dpi_ok.all())
        and bool(qc.size_ok.all())
        and pdf_count > 0
    )
    return qc, passed


# ── Release builder ───────────────────────────────────────────────────────────

def main(cfg_path: str = "config/config.yaml") -> tuple[Path, bool]:
    t0    = time.time()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 1. Run full pipeline
    d   = run(cfg_path)
    cfg = d["cfg"]
    f0, f1    = cfg["periods"]["near_future"]
    area_code = cfg["study_area"]["province_code"]

    # 2. Timestamped release directory
    root = Path(cfg["paths"]["outputs"])
    rel  = root / f"RELEASE_{area_code}_{stamp}"
    for sub in ["station_model", "station_mme", "area_summary",
                "publication_tables", "publication_figures", "release", "logs"]:
        (rel / sub).mkdir(parents=True, exist_ok=True)

    # 3. 3-level results
    level1_station_model(d["per"], rel)
    _, station_mme = level2_station_mme(
        d["bc_mme"], d["raw_mme"], d["vm"], d["change"],
        rel, f0, f1,
    )
    level3_area_summary(
        d["obs"], d["bc_mme"], d["change"], rel, f0, f1,
        scenarios=cfg["scenarios"],
    )

    # 4. Publication tables
    publication_tables(d["meta"], d["vm"], d["change"], d["per"], station_mme, rel)

    # 5. Figures
    cfg_fig = dict(cfg)
    cfg_fig["paths"] = dict(cfg["paths"])
    cfg_fig["paths"]["outputs"] = str(rel)
    (rel / "figures").mkdir(exist_ok=True)
    saved = generate_all(d, cfg_fig)

    # Move figures → publication_figures
    figdir = rel / "figures"
    for f in figdir.glob("*"):
        shutil.move(str(f), rel / "publication_figures" / f.name)
    if figdir.exists():
        figdir.rmdir()

    # 6. Figure QC
    dpi = cfg["figures"]["dpi"]
    qc, passed = figure_qc(rel / "publication_figures", target_dpi=dpi)
    qc.to_excel(rel / "release" / "FIGURE_QC.xlsx", index=False)

    pdf_count = len(list((rel / "publication_figures").glob("*.pdf")))
    with open(rel / "FIGURE_QC_REPORT.md", "w") as fh:
        fh.write(f"# FIGURE QC REPORT\n")
        fh.write(f"Study area : **{cfg['study_area']['name']}**\n")
        fh.write(f"Timestamp  : {stamp}\n\n")
        fh.write(
            f"Raster files: {len(qc)} | "
            f"DPI {dpi} OK: {bool(qc.dpi_ok.all()) if not qc.empty else 'N/A'} | "
            f"Size OK: {bool(qc.size_ok.all()) if not qc.empty else 'N/A'} | "
            f"PDFs: {pdf_count}\n\n"
        )
        if not qc.empty:
            fh.write(qc.to_markdown(index=False))
        fh.write(f"\n\n**Journal readiness: {'PASS ✓' if passed else 'FAIL ✗'}**\n")

    # 7. Runtime summary
    runtime = time.time() - t0
    pd.DataFrame([{
        "study_area":      cfg["study_area"]["name"],
        "stamp":           stamp,
        "runtime_s":       round(runtime, 1),
        "figures_checked": len(qc),
        "pdfs_present":    pdf_count,
        "qc_pass":         passed,
    }]).to_excel(rel / "release" / "RUNTIME_SUMMARY.xlsx", index=False)

    log.info("RELEASE %s_%s | raster=%d | PDF=%d | QC=%s | %.1fs",
             area_code, stamp, len(qc), pdf_count,
             "PASS" if passed else "FAIL", runtime)

    # 8. CURRENT_RELEASE symlink (only if QC passes)
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
        log.error("QC FAILED — CURRENT_RELEASE not updated. See %s",
                  rel / "FIGURE_QC_REPORT.md")

    return rel, passed


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="CMIP6 MME Rainfall — full publication pipeline with QC gate")
    parser.add_argument("--cfg", default="config/config.yaml",
                        help="Path to config YAML (default: config/config.yaml)")
    args   = parser.parse_args()
    rel, ok = main(args.cfg)
    print(f"\nRelease directory : {rel}")
    print(f"QC pass           : {ok}")
