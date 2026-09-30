"""json-wizard CLI front-end."""
import sys
import json as jsonlib
from pathlib import Path
from .lib.json_wizard import JsonWizard

def _read_source(arg: str):
    if arg == "-":
        return sys.stdin.read()
    p = Path(arg)
    if not p.exists():
        print(f"[FAIL] file not found: {arg}")
        return None
    return p.read_text()

def main() -> int:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("jsonwiz - standalone JSON doctor")
        print("usage: jsonwiz <command> [args]")
        print("  validate <file|->      check JSON validity with line/col on failure")
        print("  pretty <file|->        pretty-print to stdout")
        print("  compact <file|->       minify to one line")
        print("  inspect <file|->       structural summary")
        print("  keys <file|->          top-level keys")
        print("  get <file|-> <path>    dotted-path value lookup (a.b.0.c)")
        print("  diff <a> <b>           structural diff of two JSON docs")
        print("  stats <file|->         type census: depths, counts")
        print("  merge <a> <b>          deep merge (b wins) to stdout")
        return 0

    cmd = args[0]
    wiz = JsonWizard()

    if cmd in ("validate", "pretty", "compact", "inspect", "keys", "get", "stats"):
        if len(args) < 2:
            print("out of scope")
            return 2
        source = _read_source(args[1])
        if source is None:
            return 1

        if cmd == "validate":
            result = wiz.validate(source)
            if result["valid"]:
                print(f"[OK] valid JSON (root type: {result['type']})")
                return 0
            print(f"[FAIL] invalid JSON at line {result['line']}, col {result['col']}: {result['error']}")
            return 1
        if cmd == "pretty":
            try:
                print(wiz.pretty(source))
                return 0
            except jsonlib.JSONDecodeError as e:
                print(f"[FAIL] invalid JSON: {e}")
                return 1
        if cmd == "compact":
            try:
                print(wiz.compact(source))
                return 0
            except jsonlib.JSONDecodeError as e:
                print(f"[FAIL] invalid JSON: {e}")
                return 1
        if cmd == "inspect":
            try:
                print(jsonlib.dumps(wiz.inspect(source), indent=2))
                return 0
            except jsonlib.JSONDecodeError as e:
                print(f"[FAIL] invalid JSON: {e}")
                return 1
        if cmd == "keys":
            try:
                keys = wiz.keys(source)
                print("\n".join(keys) or "[FAIL] root is not an object")
                return 0
            except jsonlib.JSONDecodeError as e:
                print(f"[FAIL] invalid JSON: {e}")
                return 1
        if cmd == "get":
            if len(args) < 3:
                print("out of scope - get requires a path")
                return 2
            try:
                value = wiz.get(source, args[2])
                if isinstance(value, (dict, list)):
                    print(jsonlib.dumps(value, indent=2))
                else:
                    print(jsonlib.dumps(value))
                return 0
            except (KeyError, IndexError) as e:
                print(f"[FAIL] path not found: {e}")
                return 1
            except jsonlib.JSONDecodeError as e:
                print(f"[FAIL] invalid JSON: {e}")
                return 1
        if cmd == "stats":
            try:
                print(jsonlib.dumps(wiz.stats(source), indent=2))
                return 0
            except jsonlib.JSONDecodeError as e:
                print(f"[FAIL] invalid JSON: {e}")
                return 1

    if cmd in ("diff", "merge"):
        if len(args) < 3:
            print(f"out of scope - {cmd} requires two files")
            return 2
        sa = _read_source(args[1])
        sb = _read_source(args[2])
        if sa is None or sb is None:
            return 1
        try:
            if cmd == "diff":
                changes = wiz.diff(sa, sb)
                if not changes:
                    print("[OK] identical structure and values")
                    return 0
                for kind, path, old, new in changes:
                    loc = ".".join(str(p) for p in path)
                    print(f"[DIFF] {kind} at {loc}")
                    if kind == "changed":
                        print(f"       a: {jsonlib.dumps(old)}")
                        print(f"       b: {jsonlib.dumps(new)}")
                    elif kind == "added":
                        print(f"       b: {jsonlib.dumps(new)}")
                    else:
                        print(f"       a: {jsonlib.dumps(old)}")
                return 1
            if cmd == "merge":
                print(jsonlib.dumps(wiz.merge(sa, sb), indent=2))
                return 0
        except (jsonlib.JSONDecodeError, TypeError) as e:
            print(f"[FAIL] {e}")
            return 1

    print("out of scope")
    return 2