"""commandline-wizard CLI front-end."""
import sys
from .commandline_wizard import FLEET_SUITE, CommandLineWizard

def main() -> int:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("cmdwiz - declared test-suite runner for the command center")
        print("usage: cmdwiz run [label]   run fleet census, write timestamped report")
        print("       cmdwiz list          show declared checks")
        return 0
    wiz = CommandLineWizard()
    if args[0] == "list":
        for name, argv, _ in FLEET_SUITE:
            print(f"{' '.join(argv)}   # {name}")
        return 0
    if args[0] == "history":
        from pathlib import Path as _P
        hp = args[1] if len(args) > 1 else str(_P.home() / ".bash_history")
        res = wiz.analyze_history(hp)
        if res is None:
            print(f"[FAIL] cannot read {hp}")
            return 1
        print(f"history: {hp} - {res['total_lines']} lines, {res['unique_commands']} unique commands")
        print("-- top commands --")
        for cmd, n in res["top"]:
            print(f"{n:5d}  {cmd}")
        print("-- danger scan --")
        if not res["dangerous"]:
            print("[OK] no dangerous patterns found")
            return 0
        for ln_no, label, excerpt in res["dangerous"]:
            print(f"[FAIL] line {ln_no}: {label}  ->  {excerpt}")
        return 1

    if args[0] == "sessions":
        from pathlib import Path as _P
        sd = args[1] if len(args) > 1 else str(_P.home() / "micro_runners" / "data" / "sessions")
        res = wiz.analyze_sessions(sd)
        if not res:
            print("[OK] no session files found")
            return 0
        for r in res:
            mark = "!" if r["fab_count"] > 0 else " "
            print(f"{mark} {r['file']}: tool_requests={r['tool_requests']}, fabrication_flags={r['fab_count']}")
        suspects = sum(1 for r in res if r["fab_count"] > 0)
        verdict = "[OK]" if suspects == 0 else "[FAIL]"
        print(f"{verdict} {len(res)} sessions scanned, {suspects} with fabrication fingerprints")
        return 0 if suspects == 0 else 1

    if args[0] == "run":
        label = args[1] if len(args) > 1 else "baseline"
        results = wiz.run_suite(FLEET_SUITE)
        path, passed, total = wiz.write_report(results, label)
        for r in results:
            print(f"{r['verdict']} {r['name']}")
        print(f"[{'OK' if passed == total else 'FAIL'}] {passed}/{total} checks passed - report: {path}")
        return 0 if passed == total else 1
    print("out of scope")
    return 2
