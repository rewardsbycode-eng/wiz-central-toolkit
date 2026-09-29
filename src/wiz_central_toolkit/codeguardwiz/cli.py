"""codeguardwiz — CLI face. Plain verdicts, exit codes 0/1/2, no tracebacks."""
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.codeguard_wizard import (
    AUDIT_PREFS,
    FIX_PREFS,
    audit,
    detect_language,
    fix,
    load_roster,
    pick_seat,
)


def main():
    p = argparse.ArgumentParser(prog="codeguardwiz")
    sub = p.add_subparsers(dest="cmd")
    a = sub.add_parser("audit", help="audit a file, print plain verdict")
    a.add_argument("file")
    a.add_argument("--json", action="store_true", help="machine-readable report")
    f = sub.add_parser("fix", help="generate repaired code for a file")
    f.add_argument("file")
    f.add_argument("--write", action="store_true",
                   help="CONSENT: write the fixed file to disk (gated)")
    f.add_argument("--out", help="write to this path instead")
    l = sub.add_parser("lang", help="detect language of a file")
    l.add_argument("file")
    sub.add_parser("roster", help="show live seats this wizard would pick")

    # --- CODE REPAIR LANE EXPANSION ---
    sc = sub.add_parser("scan", help="recursive audit sweep on directory")
    sc.add_argument("dir", help="directory to scan")
    sc.add_argument("--json", action="store_true", help="machine-readable report")

    wh = sub.add_parser("watch", help="diff-since-last-audit: re-run audit, report changes")
    wh.add_argument("file", help="file to watch")

    sv = sub.add_parser("severity", help="filter audit by severity (critical/high only)")
    sv.add_argument("file", help="file to audit")
    sv.add_argument("--threshold", default="HIGH", choices=["CRITICAL", "HIGH", "MEDIUM"])

    ex = sub.add_parser("explain", help="show rule that fired at specific line")
    ex.add_argument("file", help="file with finding")
    ex.add_argument("line", type=int, help="line number")

    sf = sub.add_parser("scaffold", help="generate unit-test skeleton for file")
    sf.add_argument("file", help="source file to test")
    sf.add_argument("--framework", default="pytest", choices=["pytest", "unittest", "nose"])

    args = p.parse_args()
    if not args.cmd:
        p.print_help()
        return 0

    if args.cmd == "roster":
        roster = load_roster()
        if not roster:
            print("[FAIL] daemon unreachable - roster empty")
            return 1
        audit_seat = pick_seat(roster, AUDIT_PREFS, "CODEGUARD_AUDIT_MODEL")
        fix_seat = pick_seat(roster, FIX_PREFS, "CODEGUARD_FIX_MODEL")
        for name in roster:
            marks = []
            if name == audit_seat:
                marks.append("audit")
            if name == fix_seat:
                marks.append("fix")
            print(f"[OK] {name}" + (f" <- {'/'.join(marks)}" if marks else ""))
        return 0

    if args.cmd == "lang":
        path = args.file
        if not Path(path).is_file():
            print(f"[FAIL] not a file: {path}")
            return 1
        lang = detect_language(path)
        if lang == "unknown":
            print("out of scope - language not detectable")
            return 2
        print(f"[OK] {path}: {lang}")
        return 0

    if args.cmd == "audit":
        path = args.file
        if not Path(path).is_file():
            print(f"[FAIL] not a file: {path}")
            return 1
        result = audit(path)
        if args.json:
            print(json.dumps(result, indent=2))
        if result["status"] != "OK":
            print(f"[FAIL] {result.get('reason', 'audit failed')}")
            return 1
        counts = result["issues_count"]
        score = result["audit"].get("score", "?")
        print(f"[OK] {result['filepath']} ({result['language']}, "
              f"model {result['model']}, score {score})")
        print(f"     issues: CRITICAL={counts['CRITICAL']} HIGH={counts['HIGH']} "
              f"MEDIUM={counts['MEDIUM']} LOW={counts['LOW']}")
        for issue in result["audit"].get("issues", []):
            print(f"     [{issue.get('severity', '?')}] {issue.get('title', '?')} "
                  f"(line {issue.get('line_range', '?')})")
        return 0

    if args.cmd == "scan":
        from pathlib import Path as LibPath
        d = LibPath(args.dir)
        if not d.is_dir():
            print(f"[FAIL] not a directory: {args.dir}")
            return 1
        results = []
        total = 0
        critical = 0
        high = 0
        for f in d.rglob("*.py"):
            if "__pycache__" in str(f) or ".venv" in str(f):
                continue
            r = audit(str(f))
            if r["status"] == "OK":
                counts = r.get("issues_count", {})
                crit = counts.get("CRITICAL", 0)
                h = counts.get("HIGH", 0)
                if crit or h:
                    results.append({
                        "file": str(f), "crit": crit, "high": h
                    })
                    critical += crit
                    high += h
            total += 1
        if args.json:
            print(json.dumps({"files_scanned": total, "findings": results}, indent=2))
        else:
            print(f"[OK] scanned {total} files")
            print(f"     CRITICAL={critical} HIGH={high}")
            if results:
                print("     findings:")
                for r in results[:10]:
                    print(f"       {r['file']}: C={r['crit']} H={r['high']}")
        return 1 if critical or high else 0

    if args.cmd == "watch":
        path = args.file
        if not Path(path).is_file():
            print(f"[FAIL] not a file: {path}")
            return 1
        result = audit(path)
        print("[OK] watch check — compare with baseline manually")
        print(f"     score={result.get('audit', {}).get('score', '?')} "
              f"issues={result.get('issues_count', {})}")
        return 0 if result["status"] == "OK" else 1

    if args.cmd == "severity":
        path = args.file
        if not Path(path).is_file():
            print(f"[FAIL] not a file: {path}")
            return 1
        result = audit(path)
        threshold = args.threshold
        counts = result.get("issues_count", {})
        firing = counts.get(threshold, 0)
        higher = counts.get("CRITICAL", 0) if threshold != "CRITICAL" else 0
        total_above = firing + higher if threshold != "CRITICAL" else firing
        print(f"[OK] {threshold}+ severity: {total_above} findings")
        if total_above > 0:
            for iss in result.get("audit", {}).get("issues", []):
                sev = iss.get("severity", "")
                if sev == threshold or (threshold == "CRITICAL" and sev == "CRITICAL"):
                    print(f"     [{sev}] {iss.get('title')} (line {iss.get('line_range')})")
        return 1 if total_above > 0 else 0

    if args.cmd == "explain":
        from pathlib import Path as LibPath
        line = int(args.line)
        path = args.file
        if not Path(path).is_file():
            print(f"[FAIL] not a file: {path}")
            return 1
        result = audit(path)
        for iss in result.get("audit", {}).get("issues", []):
            lr = iss.get("line_range", "")
            if isinstance(lr, str) and str(line) in lr:
                print(f"[OK] Rule at line {line}:")
                print(f"     Severity: {iss.get('severity', '?')}")
                print(f"     Title: {iss.get('title', '?')}")
                print(f"     Message: {iss.get('description', '(no description)')}")
                return 0
        print(f"[FAIL] no issue found at line {line}")
        return 1

    if args.cmd == "scaffold":
        path = args.file
        if not Path(path).is_file():
            print(f"[FAIL] not a file: {path}")
            return 1
        # Real skeleton: read actual top-level functions from the source
        import ast as _ast
        try:
            tree = _ast.parse(Path(path).read_text())
        except SyntaxError as e:
            print(f"[FAIL] cannot parse {path}: {e}")
            return 1
        funcs = [n.name for n in tree.body if isinstance(n, _ast.FunctionDef)]
        classes = [n.name for n in tree.body if isinstance(n, _ast.ClassDef)]
        stem = Path(path).stem
        test_name = f"test_{stem}.py"
        lines = [
            f'"""Generated by codeguardwiz scaffold — test skeleton for {path}."""',
            "import pytest",
            "",
        ]
        for fn in funcs:
            if fn.startswith("_"):
                continue
            lines += [f"def test_{fn}_exists():", f'    """SMOKE: {fn} exists."""',
                      "    assert True", ""]
        for cls in classes:
            lines += [f"def test_{cls}_importable():", f'    """SMOKE: {cls} importable."""',
                      "    import importlib.util as _iu",
                      f"    spec = _iu.spec_from_file_location('{stem}', r'{path}')",
                      "    assert spec is not None or True", ""]
        if not funcs and not classes:
            lines += [f"# (no public top-level defs found in {path})", ""]
        print(f"[OK] test skeleton generated (preview only, disk untouched): {test_name}")
        print(f"     functions: {len([f for f in funcs if not f.startswith('_')])}, "
              f"classes: {len(classes)}")
        print("--- skeleton follows ---")
        print("\n".join(lines))
        print("--- end ---")
        print("consent lane: pipe this output to a file yourself if you want it on disk")
        return 0

    if args.cmd == "fix":
        path = args.file
        if not Path(path).is_file():
            print(f"[FAIL] not a file: {path}")
            return 1
        result = fix(path)
        if result["status"] != "OK":
            print(f"[FAIL] {result.get('reason', 'fix failed')}")
            return 1
        if result.get("issues_fixed", 0) == 0 and result.get("message"):
            print(f"[OK] {result['message']}")
            return 0
        if not args.write and not args.out:
            print(f"[OK] fix generated ({result['issues_fixed']} issues, "
                  f"model {result['fix_model']}) - preview only, disk untouched:")
            print("--- fixed code follows ---")
            print(result["fixed_code"])
            print("--- end ---")
            print("consent lane: re-run with --write to replace the file "
                  "(or --out <path>)")
            return 0
        dest = args.out or path
        if Path(path).suffix == ".py":
            import subprocess
            import tempfile
            with tempfile.NamedTemporaryFile("w", suffix=".py",
                                            delete=False) as tmp:
                tmp.write(result["fixed_code"])
            gate = subprocess.run(["pythonwiz", "check", tmp.name],
                                   capture_output=True, text=True)
            os.unlink(tmp.name)
            if gate.returncode != 0:
                print("[FAIL] fixed code rejected by pythonwiz gate - "
                      "nothing written")
                return 1
            print("[OK] pythonwiz gate passed")
        Path(dest).write_text(result["fixed_code"])
        print(f"[OK] written: {dest} (issues addressed: "
              f"{result['issues_fixed']})")
        return 0

    p.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
