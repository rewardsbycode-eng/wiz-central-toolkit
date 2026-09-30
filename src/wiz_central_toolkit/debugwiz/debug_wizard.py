"""debug-wizard brain — the diagnosis oracle. Never mutates; only proposes."""

import ast
import builtins
import json
from collections import Counter
from pathlib import Path

HOME = Path.home()
BANK = HOME / ".debug-wizard"
IGNORE_LIST = BANK / "ignored.json"

DEBUG_LAW = """DEBUG LAW (debug-wizard, the diagnosis oracle)
1. Diagnose freely: autopsy tracebacks, classify errors, count hotspots, report facts.
2. Never mutate: no writes, no patches, no fixes applied — only proposals staged for writewiz.
3. Consent wall: any fix suggestion goes through writewiz propose; Governor consents.
4. Plain verdicts: [OK]/[FAIL]/out of scope, exit 0/1/2, no tracebacks.
5. Truth first: run pythonwiz check or python -m py_compile before analysis.
6. Ignore list amends only by Governor decree; protected paths stay ignored.
"""

def _ensure_bank():
    BANK.mkdir(parents=True, exist_ok=True)
    if not IGNORE_LIST.exists():
        IGNORE_LIST.write_text("[]")

def load_ignored() -> list[str]:
    _ensure_bank()
    try:
        return json.loads(IGNORE_LIST.read_text())
    except (json.JSONDecodeError, OSError):
        return []

def add_ignore(path_str: str) -> dict:
    target = Path(path_str).expanduser().resolve()
    ign = load_ignored()
    if str(target) in ign:
        return {"ok": False, "error": f"already ignored: {target}"}
    ign.append(str(target))
    IGNORE_LIST.write_text(json.dumps(ign, indent=2))
    return {"ok": True, "ignored": str(target)}

def remove_ignore(path_str: str) -> dict:
    target = Path(path_str).expanduser().resolve()
    ign = load_ignored()
    if str(target) not in ign:
        return {"ok": False, "error": f"not ignored: {target}"}
    ign.remove(str(target))
    IGNORE_LIST.write_text(json.dumps(ign, indent=2))
    return {"ok": True, "unignored": str(target)}

def _walk_py_files(root: Path):
    root = Path(root)
    if not root.exists():
        return
    if root.is_file() and root.suffix == ".py":
        yield root
        return

    ignored = [Path(p) for p in load_ignored()]
    for p in sorted(root.rglob("*.py")):
        if any(part in {".venv", ".git", "__pycache__"} for part in p.parts):
            continue
        resolved = p.resolve()
        if any(resolved == item or item in resolved.parents for item in ignored):
            continue
        yield p

def _compile_errors(file: Path) -> list[dict]:
    """Return list of compilation errors without tracebacks."""
    errors = []
    try:
        with file.open("r", encoding="utf-8", errors="replace") as f:
            source = f.read()
        ast.parse(source)
    except SyntaxError as e:
        errors.append({
            "line": e.lineno or 1,
            "type": "SyntaxError",
            "message": e.msg or "invalid syntax",
            "col": e.offset or 0,
            "snippet": e.text.strip() if e.text else ""
        })
    except Exception as e:
        errors.append({"line": 0, "type": type(e).__name__, "message": str(e)})
    return errors

def _classify(errors: list[dict]) -> dict[str, int]:
    counts = Counter(e["type"] for e in errors)
    return dict(counts)

_MODULE_DUNDERS = frozenset(
    {"__file__", "__name__", "__doc__", "__package__", "__spec__",
     "__loader__", "__builtins__", "__path__", "__cached__"}
)


def _missing_imports(file: Path) -> list[str]:
    """Names read but never bound anywhere in the file (likely missing imports)."""
    try:
        tree = ast.parse(file.read_text(encoding="utf-8", errors="replace"))
    except (SyntaxError, ValueError, OSError):
        return []
    bound: set[str] = set(dir(builtins)) | _MODULE_DUNDERS
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and any(a.name == "*" for a in node.names):
            return []  # star import: cannot know what it defines
        if isinstance(node, ast.Import):
            for alias in node.names:
                bound.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                bound.add(alias.asname or alias.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            bound.add(node.name)
        elif isinstance(node, ast.arg):
            bound.add(node.arg)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            bound.add(node.id)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            bound.add(node.name)
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            bound.update(node.names)
        elif isinstance(node, (ast.MatchAs, ast.MatchStar)) and node.name:
            bound.add(node.name)
        elif isinstance(node, ast.MatchMapping) and node.rest:
            bound.add(node.rest)
        elif type(node).__name__ in ("TypeVar", "ParamSpec", "TypeVarTuple"):
            bound.add(str(getattr(node, "name", "")))
    used = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
    }
    return sorted(used - bound)


def _signature_issues(file: Path) -> list[dict]:
    """Detect call vs definition mismatches."""
    issues = []
    try:
        tree = ast.parse(file.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return [{"line": 0, "type": "SyntaxError", "message": "file unparseable"}]
    
    defs = {node.name: {"args": len(node.args.args), "lineno": node.lineno}
            for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    calls = [(node.func.id, len(node.args), node.lineno)
             for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)]
    
    for func_name, call_args, lineno in calls:
        if func_name in defs and defs[func_name]["args"] != call_args:
            issues.append({"line": lineno, "type": "SignatureMismatch",
                          "message": f"{func_name} def={defs[func_name]['args']} args, call={call_args}"})
    return issues

def trace(file: Path) -> dict:
    """Autopsy one file's compilation errors."""
    errors = _compile_errors(file)
    return {"file": str(file), "errors": errors, "ok": len(errors) == 0}

def classify_file(file: Path) -> dict:
    """Error type breakdown."""
    errors = _compile_errors(file)
    return {"file": str(file), "classification": _classify(errors), "total": len(errors)}

def locate(root: Path, pattern: str) -> list[str]:
    """Find files with given error pattern."""
    hits = []
    for f in _walk_py_files(root):
        err = trace(f)
        for e in err.get("errors", []):
            if pattern.lower() in e["message"].lower() or pattern in e["type"]:
                hits.append(str(f))
                break
    return hits

def count_dir(root: Path) -> dict:
    """Errors by category."""
    all_errors = []
    for f in _walk_py_files(root):
        all_errors.extend(_compile_errors(f))
    return {"totals": _classify(all_errors), "files_checked": sum(1 for _ in _walk_py_files(root))}

def hotspot(root: Path) -> list[tuple[str, int]]:
    """Files with most errors, ranked."""
    scores = []
    for f in _walk_py_files(root):
        err_count = len(_compile_errors(f))
        if err_count > 0:
            scores.append((str(f), err_count))
    return sorted(scores, key=lambda x: -x[1])[:10]

def timeline(root: Path) -> list[dict]:
    """Error frequency by modification time."""
    data = []
    for f in _walk_py_files(root):
        err_count = len(_compile_errors(f))
        if err_count > 0:
            data.append({
                "file": str(f),
                "errors": err_count,
                "mtime": f.stat().st_mtime
            })
    data.sort(key=lambda x: -x["mtime"])
    return data

def imports(file: Path) -> dict:
    """Missing import detection."""
    missing = _missing_imports(file)
    return {"file": str(file), "likely_missing": missing}

def names(file: Path) -> list[str]:
    """Undefined names."""
    return _missing_imports(file)

def signatures(file: Path) -> list[dict]:
    """Function signature issues."""
    return _signature_issues(file)

def suggest_fix(file: Path) -> str:
    """Human-readable fix suggestion (no AI — heuristic)."""
    errs = trace(file)
    if errs["ok"]:
        return f"[OK] {file}: no compilation errors"
    lines = [f"[ISSUE] {file}"]
    for e in errs["errors"][:5]:
        lines.append(f"  Line {e['line']}: {e['type']} — {e['message']}")
    if errs["errors"][5:]:
        lines.append(f"  ... and {len(errs['errors']) - 5} more errors")
    return "\n".join(lines)

def audit_dir(root: Path) -> dict:
    """Full error census."""
    files = list(_walk_py_files(root))
    healthy = 0
    unhealthy = 0
    total_errors = 0
    for f in files:
        err = trace(f)
        if err["ok"]:
            healthy += 1
        else:
            unhealthy += 1
            total_errors += len(err["errors"])
    return {"healthy": healthy, "unhealthy": unhealthy, "total_errors": total_errors,
            "files_checked": len(files), "health_pct": round(healthy / max(len(files), 1) * 100, 1)}

def report_json(root: Path) -> str:
    """JSON report for CI/CD."""
    data = {"timestamp": "now", "root": str(root),
            "audit": audit_dir(root),
            "hotspots": [{"file": f, "errors": e} for f, e in hotspot(root)]}
    return json.dumps(data, indent=2)

def stats_fleet() -> dict:
    """Aggregate stats across multiple common paths."""
    paths = ["~/tools", "~/wizard_central", "~/BASE", "~/micro_runners"]
    results = {}
    for p in paths:
        root = Path(p).expanduser()
        if not root.exists():
            results[p] = {"files_checked": 0, "healthy": 0, "unhealthy": 0,
                          "total_errors": 0, "health_pct": "n/a (absent)"}
            continue
        results[p] = audit_dir(root)
    return results
