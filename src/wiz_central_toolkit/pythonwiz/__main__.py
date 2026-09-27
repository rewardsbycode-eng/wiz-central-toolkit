"""pythonwiz — Python syntax checker and analyzer."""

import ast
import sys
from pathlib import Path


def check_file(filepath: str) -> tuple[str, str]:
    """Validate a single Python file.
    
    Returns: (verdict, reason)
    """
    path = Path(filepath)
    if not path.exists():
        return "FAIL", f"file not found: {filepath}"
    
    if not path.suffix == ".py":
        return "FAIL", f"not a .py file: {filepath}"
    
    try:
        content = path.read_text(encoding="utf-8")
        ast.parse(content)
        return "OK", f"{filepath}: valid syntax"
    except SyntaxError as e:
        return "FAIL", f"{filepath}:{e.lineno}: {e.msg}"
    except Exception as e:
        return "FAIL", f"{filepath}: {e}"


def check_directory(dirpath: str) -> dict:
    """Scan all .py files in a directory recursively.
    
    Returns summary dict with pass/fail counts and details.
    """
    path = Path(dirpath)
    if not path.is_dir():
        return {"status": "FAIL", "reason": f"not a directory: {dirpath}"}
    
    py_files = list(path.rglob("*.py"))
    if not py_files:
        return {"status": "OK", "reason": "no .py files found", "count": 0}
    
    results = []
    passed = 0
    failed = 0
    
    for py_file in py_files:
        verdict, reason = check_file(str(py_file))
        results.append({"file": str(py_file), "verdict": verdict})
        if verdict == "OK":
            passed += 1
        else:
            failed += 1
    
    return {
        "status": "OK" if failed == 0 else "FAIL",
        "total": len(py_files),
        "passed": passed,
        "failed": failed,
        "results": results
    }


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        print("usage: pythonwiz check <file.py|directory>")
        print("")
        print("subcommands:")
        print("  check <path>    validate Python syntax")
        print("  --version       show version")
        print("")
        print("examples:")
        print('  pythonwiz check main.py')
        print('  pythonwiz check ./src/')
        print("  pythonwiz check .")
        return 0
    
    if args[0] == "--version":
        print("pythonwiz v1.0-public")
        return 0
    
    if args[0] != "check":
        print(f"error: unknown command '{args[0]}'", file=sys.stderr)
        print("use: pythonwiz check <file.py|directory>")
        return 2
    
    if len(args) < 2:
        print("error: check requires a path argument", file=sys.stderr)
        return 2
    
    target = args[1]
    path = Path(target)
    
    if path.is_file():
        verdict, reason = check_file(target)
    elif path.is_dir():
        result = check_directory(target)
        verdict = result["status"]
        reason = f"{result['passed']}/{result['total']} files valid"
        
        # Print details for directory scans
        for entry in result.get("results", []):
            status = "[OK]" if entry["verdict"] == "OK" else "[FAIL]"
            print(f"{status} {entry['file']}")
    else:
        verdict = "FAIL"
        reason = f"path not found: {target}"
    
    if verdict == "OK":
        print(f"[OK] {reason}")
        return 0
    else:
        print(f"[FAIL] {reason}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
