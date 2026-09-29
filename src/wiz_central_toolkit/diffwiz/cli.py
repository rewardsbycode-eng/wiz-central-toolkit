"""diff-wizard CLI front-end."""
import sys
from pathlib import Path

from .diff_wizard import DiffWizard


def main() -> int:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("diffwiz - standalone change-truth doctor")
        print("usage: diffwiz <command> [args]")
        print("  files <a> <b>             unified diff of two files")
        print("  dirs <a> <b>              compare directory trees")
        print("  context <N> <a> <b>       unified diff with N context lines")
        print("  summary <a> <b>           diff statistics without full output")
        print("  word <a> <b>              word-level diff")
        print("  same <a> <b>              exit 0 if identical, 1 if different (silent)")
        print("  reverse <a> <b>           diff b -> a (swap sides)")
        return 0

    wiz = DiffWizard()

    # --- existing commands ---
    if args[0] == "files":
        if len(args) < 3:
            print("out of scope")
            return 2
        a, b = Path(args[1]), Path(args[2])
        for p in (a, b):
            if not p.exists():
                print(f"[FAIL] not found: {p}")
                return 1
        text = wiz.diff_files(a, b)
        if not text:
            print("[OK] files identical")
            return 0
        print(text)
        print("[FAIL] files differ")
        return 1
    if args[0] == "dirs":
        if len(args) < 3:
            print("out of scope")
            return 2
        da, db = Path(args[1]), Path(args[2])
        for p in (da, db):
            if not p.is_dir():
                print(f"[FAIL] not a directory: {p}")
                return 1
        r = wiz.diff_dirs(da, db)
        count = len(r["only_a"]) + len(r["only_b"]) + len(r["differing"])
        for rel in r["only_a"]:
            print(f"only in {args[1]}: {rel}")
        for rel in r["only_b"]:
            print(f"only in {args[2]}: {rel}")
        for rel in r["differing"]:
            print(f"differing: {rel}")
        if count == 0:
            print("[OK] trees identical")
            return 0
        print(f"[FAIL] {count} differences")
        return 1

    # --- new commands ---
    if args[0] == "context":
        if len(args) < 4:
            print("out of scope - context requires N a b")
            return 2
        n = int(args[1])
        a, b = Path(args[2]), Path(args[3])
        for p in (a, b):
            if not p.exists():
                print(f"[FAIL] not found: {p}")
                return 1
        text = wiz.diff_files_context(a, b, n)
        if not text:
            print("[OK] files identical")
            return 0
        print(text)
        print("[FAIL] files differ")
        return 1
    if args[0] == "summary":
        if len(args) < 3:
            print("out of scope")
            return 2
        a, b = Path(args[1]), Path(args[2])
        for p in (a, b):
            if not p.exists():
                print(f"[FAIL] not found: {p}")
                return 1
        r = wiz.diff_summary(a, b)
        if r["identical"]:
            print("[OK] identical")
            return 0
        print(f"added={r['added_lines']} removed={r['removed_lines']} hunks={r['hunks']}")
        return 1
    if args[0] == "word":
        if len(args) < 3:
            print("out of scope")
            return 2
        a, b = Path(args[1]), Path(args[2])
        for p in (a, b):
            if not p.exists():
                print(f"[FAIL] not found: {p}")
                return 1
        print(wiz.diff_word_level(a, b))
        return 0
    if args[0] == "same":
        if len(args) < 3:
            print("out of scope")
            return 2
        a, b = Path(args[1]), Path(args[2])
        for p in (a, b):
            if not p.exists():
                print(f"[FAIL] not found: {p}")
                return 1
        return 0 if wiz.files_identical(a, b) else 1
    if args[0] == "reverse":
        if len(args) < 3:
            print("out of scope")
            return 2
        a, b = Path(args[1]), Path(args[2])
        for p in (a, b):
            if not p.exists():
                print(f"[FAIL] not found: {p}")
                return 1
        text = wiz.diff_files_reverse(a, b)
        if not text:
            print("[OK] files identical")
            return 0
        print(text)
        print("[FAIL] files differ")
        return 1

    print("out of scope")
    return 2