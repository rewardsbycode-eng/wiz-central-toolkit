"""python-wizard CLI front-end."""
import json
import sys
from pathlib import Path

from .python_wizard import PythonWizard

HELP = """pythonwiz - standalone Python doctor (parse only, never executes)
usage: pythonwiz <command> <target>

  check <file|dir>     syntax validation (the fleet gate)
  entry <file>         shebang + interpreter validation
  outline <file>       symbol map: classes/functions + line numbers
  imports <file>       stdlib/third_party/local/relative inventory
  todos <file>         TODO/FIXME/XXX/BUG/HACK markers
  deadcode <file>      defined-but-unreferenced candidates (heuristic)
  complexity <file>    branch count per function, hottest first
  loc <file>           lines/code/blank/comment/function stats
  docstrings <file>    defs missing docstrings
  explain <file>       syntax error with source lines shown
  shebangs <dir>       sweep tree, validate every shebang
  deps <file>          third-party imports as requirements list
  callmap <file>       who-calls-whom per function
  longest <file>       functions ranked by length
  excepts <file>       bare/broad except handlers + swallows
  secrets <file>       hardcoded credential patterns
  mainguard <file>     has __main__ guard?
  globals <file>       module-level mutable state audit
  magic <file>         suspicious numeric literals
  compare <a> <b>      structural symbol diff of two files
  tree <dir>           directory aggregate summary
  score <file>         composite health score 0-100"""

def _file(arg: str):
    p = Path(arg)
    if not p.exists():
        print(f"[FAIL] not found: {arg}")
        return None
    return p

def main() -> int:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(HELP)
        return 0

    cmd = args[0]
    wiz = PythonWizard()

    # ---- existing ----
    if cmd == "check":
        if len(args) < 2:
            print("out of scope")
            return 2
        target = _file(args[1])
        if target is None:
            return 1
        if target.is_dir():
            results = wiz.check_dir(target)
            if not results:
                print(f"[FAIL] no .py files found under {target}")
                return 1
            bad = 0
            for r in results:
                if r["valid"]:
                    print(f"[OK]   {r['file']}")
                else:
                    bad += 1
                    print(f"[FAIL] {r['file']} line {r.get('line')}, col {r.get('col')}: {r['error']}")
            print(f"\n{len(results) - bad}/{len(results)} valid, {bad} invalid")
            return 1 if bad else 0
        r = wiz.check_file(target)
        print(f"[OK] {target}" if r["valid"]
              else f"[FAIL] {target} line {r['line']}, col {r['col']}: {r['error']}")
        return 0 if r["valid"] else 1

    if cmd == "entry":
        if len(args) < 2:
            print("out of scope")
            return 2
        r = wiz.check_entry(_file(args[1]))
        print(f"[OK] shebang valid: {r.get('interpreter')}" if r["valid"]
              else f"[FAIL] {r['error']}")
        return 0 if r["valid"] else 1

    # ---- two-file commands ----
    if cmd == "compare":
        if len(args) < 3:
            print("out of scope")
            return 2
        a, b = _file(args[1]), _file(args[2])
        if a is None or b is None:
            return 1
        r = wiz.compare_symbols(a, b)
        if "error" in r:
            print(f"[FAIL] unparseable file: {r['error']}")
            return 1
        if not r["only_a"] and not r["only_b"]:
            print("[OK] identical symbol sets")
            return 0
        for kind, n in r["only_a"]:
            print(f"only in {args[1]}: {kind} {n}")
        for kind, n in r["only_b"]:
            print(f"only in {args[2]}: {kind} {n}")
        print(f"[DIFF] {len(r['only_a'])} only-a, {len(r['only_b'])} only-b, "
              f"{len(r['common'])} common")
        return 1

    # ---- dir commands ----
    if cmd in ("shebangs", "tree"):
        if len(args) < 2:
            print("out of scope")
            return 2
        d = Path(args[1])
        if not d.is_dir():
            print(f"[FAIL] not a directory: {d}")
            return 1
        if cmd == "shebangs":
            results = wiz.shebangs_dir(d)
            if not results:
                print("[FAIL] no shebang-bearing .py files found")
                return 1
            bad = 0
            for p, interp, ok in results:
                if ok:
                    print(f"[OK]   {p} -> {interp}")
                else:
                    bad += 1
                    print(f"[FAIL] {p} -> {interp}")
            print(f"\n{len(results) - bad}/{len(results)} valid, {bad} invalid")
            return 1 if bad else 0
        print(json.dumps(wiz.tree_summary(d), indent=2))
        return 0

    # ---- single-file commands ----
    single = ("outline", "imports", "todos", "deadcode", "complexity", "loc",
              "docstrings", "explain", "deps", "callmap", "longest",
              "excepts", "secrets", "mainguard", "globals", "magic", "score")
    if cmd in single:
        if len(args) < 2:
            print("out of scope")
            return 2
        p = _file(args[1])
        if p is None:
            return 1

        if cmd == "outline":
            rows = wiz.outline(p)
            print("\n".join(f"L{ln:4d} {kind:5s} {name}"
                            for kind, name, ln in rows) or "[FAIL] no symbols")
            return 0
        if cmd == "imports":
            print(json.dumps(wiz.imports_of(p), indent=2))
            return 0
        if cmd == "todos":
            rows = wiz.todos_of(p)
            print("\n".join(f"L{ln:4d} [{tag}] {msg}" for ln, tag, msg in rows)
                  or "[OK] no markers found")
            return 1 if rows else 0
        if cmd == "deadcode":
            rows = wiz.deadcode(p)
            print("[hint] candidates only — attribute-called methods may false-positive")
            print("\n".join(f"L{ln:4d} {name}" for name, ln in rows)
                  or "[OK] no dead code candidates")
            return 1 if rows else 0
        if cmd == "complexity":
            print("\n".join(f"{c:3d} branches  L{ln:4d} {name}"
                            for name, ln, c in wiz.complexity(p))
                  or "[FAIL] no functions")
            return 0
        if cmd == "loc":
            print(json.dumps(wiz.loc_stats(p), indent=2))
            return 0
        if cmd == "docstrings":
            rows = wiz.docstring_report(p)
            print("\n".join(f"L{ln:4d} {name} — no docstring" for ln, name in rows)
                  or "[OK] all documented")
            return 1 if rows else 0
        if cmd == "explain":
            r = wiz.explain_error(p)
            if r["valid"]:
                print(f"[OK] {p} parses clean — nothing to explain")
                return 0
            print(f"[FAIL] {p} line {r['line']}, col {r['col']}: {r['error']}")
            print("\n".join(r["context"]))
            return 1
        if cmd == "deps":
            deps = wiz.deps(p)
            print("\n".join(deps) or "[OK] stdlib-only — zero third-party deps")
            return 0
        if cmd == "callmap":
            print(json.dumps(wiz.call_map(p), indent=2))
            return 0
        if cmd == "longest":
            print("\n".join(f"{length:4d} lines  L{ln:4d} {name}"
                            for name, ln, length in wiz.longest_functions(p))
                  or "[FAIL] no functions")
            return 0
        if cmd == "excepts":
            rows = wiz.bare_excepts(p)
            print("\n".join(f"L{ln:4d} {kind} except{' + swallow' if swallow else ''}"
                            for ln, kind, swallow in rows)
                  or "[OK] no bare/broad excepts")
            return 1 if rows else 0
        if cmd == "secrets":
            rows = wiz.secrets_scan(p)
            print("\n".join(f"L{ln:4d} {line}" for ln, line in rows)
                  or "[OK] no credential patterns found")
            return 1 if rows else 0
        if cmd == "mainguard":
            r = wiz.main_guard(p)
            print("[OK] __main__ guard present" if r["has_main_guard"]
                  else "[FAIL] no __main__ guard")
            return 0 if r["has_main_guard"] else 1
        if cmd == "globals":
            rows = wiz.globals_audit(p)
            print("\n".join(f"L{ln:4d} {names} ({mut})" for ln, names, mut in rows)
                  or "[OK] no module-level assignments")
            mutables = [r for r in rows if r[2] == "mutable"]
            return 1 if mutables else 0
        if cmd == "magic":
            rows = wiz.magic_numbers(p)
            print("\n".join(f"L{ln:4d} {val}" for ln, val in rows)
                  or "[OK] no suspicious literals")
            return 0
        if cmd == "score":
            print(json.dumps(wiz.health_score(p), indent=2))
            return 0

    print("out of scope")
    return 2

if __name__ == "__main__":
    sys.exit(main())