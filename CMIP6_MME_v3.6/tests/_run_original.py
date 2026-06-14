"""_run_original — execute the original test_all_fixes.py / test_pipeline_smoke.py
classes in an environment WITHOUT pytest.

Provides a minimal `pytest` shim (fixture / raises / approx) and a tiny
collector that resolves no-arg fixtures and `tmp_path`.  Tests whose bodies
import optional heavy deps (geopandas/matplotlib-GIS) are reported as SKIP
rather than counted as failures, since those deps are unrelated to the
scientific fixes and are absent in this minimal sandbox.
"""
from __future__ import annotations
import sys, os, types, inspect, tempfile, traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# ── Minimal pytest shim ───────────────────────────────────────────────────────
pt = types.ModuleType("pytest")
def fixture(*a, **k):
    def deco(fn): fn._is_fixture = True; return fn
    if a and callable(a[0]): return deco(a[0])
    return deco
class _Raises:
    def __init__(self, exc, match=None): self.exc = exc; self.match = match
    def __enter__(self): return self
    def __exit__(self, et, ev, tb): return et is not None and issubclass(et, self.exc)
def raises(exc, match=None, **k): return _Raises(exc, match)
class _Approx:
    def __init__(self, v, rel=1e-6, abs=1e-12): self.v=v; self.rel=rel; self.abs=abs
    def __eq__(self, o): return abs(o-self.v) <= max(self.abs, self.rel*abs(self.v))
def approx(v, rel=1e-6, abs=1e-12): return _Approx(v, rel, abs)
pt.fixture = fixture; pt.raises = raises; pt.approx = approx
class _Skipped(Exception): pass
def _skip(reason=""): raise _Skipped(reason)
pt.skip = _skip
pt.mark = types.SimpleNamespace(parametrize=lambda *a, **k: (lambda f: f),
                                skip=lambda *a, **k: (lambda f: f))
sys.modules["pytest"] = pt

SKIP_DEP_HINTS = ("geopandas", "shapely", "No module named 'matplotlib'",
                  "cartopy", "fiona", "pyproj")

def run_module(modname):
    passed = skipped = failed = 0
    try:
        mod = __import__(modname, fromlist=["*"])
    except Exception as e:
        print(f"  module import failed: {e}")
        return 0, 0, 1
    classes = [c for _, c in inspect.getmembers(mod, inspect.isclass)
               if c.__module__ == mod.__name__]
    for cls in classes:
        inst = cls()
        fixtures = {n: getattr(inst, n) for n, f in inspect.getmembers(inst, inspect.ismethod)
                    if getattr(f, "_is_fixture", False)}
        tests = [n for n, _ in inspect.getmembers(inst, inspect.ismethod) if n.startswith("test_")]

        def _resolve(name):
            f = fixtures[name]
            fkw = {}
            for pp in inspect.signature(f).parameters:
                if pp == "tmp_path":
                    fkw[pp] = Path(tempfile.mkdtemp())
                elif pp == "tmp_path_factory":
                    class _F:
                        def mktemp(self, *_a, **_k): return Path(tempfile.mkdtemp())
                    fkw[pp] = _F()
                elif pp in fixtures:
                    fkw[pp] = _resolve(pp)
            return f(**fkw)

        for tn in tests:
            fn = getattr(inst, tn)
            sig = inspect.signature(fn)
            kwargs = {}
            tmp = None
            try:
                for p in sig.parameters:
                    if p == "tmp_path":
                        tmp = tempfile.mkdtemp(); kwargs[p] = Path(tmp)
                    elif p == "tmp_path_factory":
                        class _F2:
                            def mktemp(self, *_a, **_k): return Path(tempfile.mkdtemp())
                        kwargs[p] = _F2()
                    elif p in fixtures:
                        kwargs[p] = _resolve(p)
                fn(**kwargs)
                passed += 1; print(f"  PASS  {cls.__name__}.{tn}")
            except Exception as e:
                msg = "".join(traceback.format_exception_only(type(e), e))
                if isinstance(e, _Skipped) or any(h in msg for h in SKIP_DEP_HINTS):
                    skipped += 1; print(f"  SKIP  {cls.__name__}.{tn}  (optional dep / skip)")
                else:
                    failed += 1; print(f"  FAIL  {cls.__name__}.{tn}\n        {msg.strip()}")
    return passed, skipped, failed

if __name__ == "__main__":
    tot_p = tot_s = tot_f = 0
    for m in ["tests.test_all_fixes", "tests.test_pipeline_smoke"]:
        print(f"\n=== {m} ===")
        p, s, f = run_module(m)
        tot_p += p; tot_s += s; tot_f += f
    print(f"\n{'='*55}\nORIGINAL SUITE: {tot_p} passed, {tot_s} skipped (optional deps), {tot_f} failed")
    sys.exit(1 if tot_f else 0)
