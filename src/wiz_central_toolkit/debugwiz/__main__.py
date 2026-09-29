"""debugwiz — the diagnosis oracle. Ported from wizard_central's debug-wizard (with the locate-dispatch fix applied)."""
import sys
from pathlib import Path

from .debug_wizard import (
    DEBUG_LAW, add_ignore, remove_ignore, load_ignored, trace, classify_file,
    locate, count_dir, hotspot, timeline, imports, names, signatures,
    suggest_fix, audit_dir, report_json, stats_fleet)

USAGE = """debugwiz - the diagnosis oracle
usage: debugwiz law                     print the DEBUG LAW alone
       debugwiz trace <file>            traceback autopsy
       debugwiz locate <dir> <pattern>  find files with error pattern
       debugwiz classify <file>         error type breakdown
       debugwiz stack <file>            stack/recursion analysis (stub)
       debugwiz count <dir>             errors by category
       debugwiz hotspot <dir>           files with most errors
       debugwiz timeline <dir>          error frequency by mtime
       debugwiz imports <file>          missing import detection
       debugwiz names <file>            undefined name detection
       debugwiz signatures <file>       signature mismatch detection
       debugwiz suggest <file>          heuristic fix suggestion
       debugwiz propose <file>          stage fix via writewiz
       debugwiz preview <file>          show staged proposal
       debugwiz explain <file>          human-readable explanation
       debugwiz audit <dir>             full error census
       debugwiz report <dir>            JSON report for CI/CD
       debugwiz log <dir>               write error log (staged via writewiz)
       debugwiz ignore <path>           add to ignore list
       debugwiz ignored                 show ignored paths
       debugwiz stats                   fleet-wide statistics
       debugwiz versions                law/version drift detection
exit codes: 0 ok | 1 failed | 2 out of scope"""

CMDS = ("law", "trace", "locate", "classify", "stack", "count", "hotspot",
        "timeline", "imports", "names", "signatures", "suggest", "propose",
        "preview", "explain", "audit", "report", "log", "ignore", "ignored",
        "stats", "versions")


def main(argv=None) -> int:
    try:
        return _dispatch(argv)
    except Exception as e:
        print(f"[FAIL] {type(e).__name__}: {e}")
        return 1


def _dispatch(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] in ("-h", "--help"):
        print(USAGE)
        return 0
    if not args:
        print(USAGE)
        return 0
    if args[0] not in CMDS:
        print(USAGE)
        return 2

    cmd = args[0]

    if cmd == "law":
        print(DEBUG_LAW)
        return 0
    if cmd == "versions":
        import hashlib
        print("debug_law_sha256:", hashlib.sha256(DEBUG_LAW.encode()).hexdigest())
        return 0
    if cmd == "ignored":
        ign = load_ignored()
        if not ign:
            print("(nothing ignored)")
            return 0
        for p in ign:
            print(f"[IGNORED] {p}")
        return 0
    if cmd == "ignore":
        if len(args) < 2:
            return 2
        r = add_ignore(args[1])
        if r["ok"]:
            print(f"[OK] ignored: {r['ignored']}")
            return 0
        print(f"[FAIL] {r['error']}")
        return 1
    if cmd == "stats":
        for path, r in stats_fleet().items():
            healthy = r.get("healthy", "?")
            checked = r.get("files_checked", "?")
            pct = r.get("health_pct", "?")
            print(f"{path}: {healthy}/{checked} healthy ({pct}%)")
        return 0

    # --- locate: two args (dir, pattern) ---
    if cmd == "locate":
        if len(args) < 3:
            print("[FAIL] locate requires a directory and a pattern")
            return 2
        d = Path(args[1]).expanduser()
        pattern = args[2]
        hits = locate(d, pattern)
        if not hits:
            print(f"(no files matching {pattern!r})")
            return 0
        for f in hits:
            print(f"[MATCH] {f}")
        return 1

    # --- path-taking commands ---
    if len(args) < 2:
        print(f"[FAIL] {cmd} requires a path")
        return 2
    p = Path(args[1]).expanduser()

    if cmd == "trace":
        r = trace(p)
        if r["ok"]:
            print(f"[OK] {p}: no errors")
            return 0
        for e in r["errors"]:
            print(f"[ERR] line {e['line']}: {e['type']} — {e['message']}")
        return 1
    if cmd == "classify":
        r = classify_file(p)
        print(f"[SUMMARY] {r['total']} errors")
        for t, c in r["classification"].items():
            print(f"  {t}: {c}")
        return 1 if r["total"] else 0
    if cmd == "count":
        r = count_dir(p)
        print(f"files={r['files_checked']} total_errors={r['totals']}")
        return 0
    if cmd == "hotspot":
        hits = hotspot(p)
        if not hits:
            print("(all files healthy)")
            return 0
        for f, cnt in hits:
            print(f"[HOT] {cnt} errors  {f}")
        return 1 if hits else 0
    if cmd == "timeline":
        data = timeline(p)
        for entry in data[:10]:
            print(f"{entry['errors']} errors  {entry['mtime']}  {entry['file']}")
        return 0
    if cmd == "imports":
        r = imports(p)
        print(f"[IMPORTS] {p}")
        if not r["likely_missing"]:
            print("(no likely missing imports)")
            return 0
        for m in r["likely_missing"]:
            print(f"  ? {m}")
        return 1 if r["likely_missing"] else 0
    if cmd == "names":
        r = names(p)
        if not r:
            print("(no undefined names)")
            return 0
        for n in r:
            print(f"  ? {n}")
        return 1
    if cmd == "signatures":
        iss = signatures(p)
        if not iss:
            print("(no signature issues)")
            return 0
        for i in iss:
            print(f"[WARN] line {i['line']}: {i['message']}")
        return 1
    if cmd == "suggest":
        print(suggest_fix(p))
        return 0
    if cmd == "explain":
        print(suggest_fix(p))
        return 0
    if cmd == "audit":
        r = audit_dir(p)
        print(f"[HEALTH] {r['healthy']}/{r['files_checked']} ({r['health_pct']}%)")
        if r["unhealthy"]:
            print(f"[FAIL] {r['unhealthy']} files with errors")
            return 1
        print("[OK] all files healthy")
        return 0
    if cmd == "report":
        print(report_json(str(p)))
        return 0
    if cmd == "log":
        # writewiz is not yet ported in this toolkit. Deliberately refuse
        # rather than risk resolving a same-named binary on PATH from an
        # unrelated project (this happened during porting — see commit history).
        print("[FAIL] 'log' requires writewiz, which is not yet available in this toolkit")
        return 1
    if cmd == "stack":
        print("(stack analysis not implemented — stub for future)")
        return 0
    if cmd == "propose":
        content = suggest_fix(p)
        print(f"[STAGED] echo '{content[:500]}' | writewiz propose ~/.debug-wizard/fix_{p.stem}.txt")
        return 0
    if cmd == "preview":
        print("(no staged proposal — use debugwiz propose first)")
        return 0

    print("out of scope")
    return 2


if __name__ == "__main__":
    sys.exit(main())
