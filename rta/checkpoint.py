"""
rta.checkpoint — Lightweight pickle-based checkpoint / resume system.

Usage
-----
    from rta.checkpoint import save, load, list_steps, prompt_resume

    # save after a heavy computation
    save("03_trends", {"trend_df": df}, cp_dir)

    # load on resume
    data = load("03_trends", cp_dir)
    if data:
        trend_df = data["trend_df"]
"""

import pickle
from pathlib import Path

__all__ = ["save", "load", "list_steps", "prompt_resume", "STEP_ORDER"]

# Canonical step names in pipeline order
STEP_ORDER = [
    "01_qc",
    "02_aggregation",
    "03_acf",
    "04_trends",
    "05_comparison",
    "06_field_sig",
]


def save(name: str, data, cp_dir: Path) -> None:
    """Pickle *data* to cp_dir/ckpt_{name}.pkl."""
    cp_dir = Path(cp_dir)
    cp_dir.mkdir(parents=True, exist_ok=True)
    path = cp_dir / f"ckpt_{name}.pkl"
    with open(path, "wb") as fh:
        pickle.dump(data, fh, protocol=pickle.HIGHEST_PROTOCOL)


def load(name: str, cp_dir: Path):
    """
    Return unpickled data from cp_dir/ckpt_{name}.pkl.

    Returns None if the file does not exist.
    """
    path = Path(cp_dir) / f"ckpt_{name}.pkl"
    if not path.exists():
        return None
    with open(path, "rb") as fh:
        return pickle.load(fh)


def list_steps(cp_dir: Path) -> list:
    """
    Return sorted list of checkpoint step names found in cp_dir.

    E.g. ['01_qc', '02_aggregation', '04_trends']
    """
    cp_dir = Path(cp_dir)
    if not cp_dir.exists():
        return []
    return sorted(
        p.stem[len("ckpt_"):]
        for p in cp_dir.glob("ckpt_*.pkl")
    )


def prompt_resume(cp_dir: Path, no_resume: bool = False) -> int:
    """
    Scan for existing checkpoints and prompt the user to resume.

    Parameters
    ----------
    cp_dir     : Path — directory containing ckpt_*.pkl files
    no_resume  : bool — if True, skip the prompt and return 0 (fresh run)

    Returns
    -------
    int — step number to resume FROM (0 = fresh run).
          e.g. if latest checkpoint is step 3, returns 3 so the caller
          skips steps 1-3 and starts at step 4.
    """
    if no_resume:
        return 0

    found = list_steps(cp_dir)
    if not found:
        return 0

    step_index = {name: i + 1 for i, name in enumerate(STEP_ORDER)}
    latest = max((step_index.get(n, 0) for n in found), default=0)
    if latest == 0:
        return 0

    latest_name = STEP_ORDER[latest - 1]
    print(f"\n  ⚡ Checkpoint found: step {latest} ({latest_name})")
    try:
        ans = input(f"     Resume from step {latest + 1}? [Y/n]: ").strip().lower()
    except (EOFError, OSError):
        # Non-interactive environment — skip resume
        ans = "n"

    if ans in ("", "y", "yes"):
        print(f"  → Resuming from step {latest + 1}\n")
        return latest
    print("  → Starting fresh\n")
    return 0
