"""rust-wizard: honest Rust validator. No tracebacks, verdicts only."""
import subprocess
import tempfile
from pathlib import Path


class RustWizard:
    NAME = "rustwiz"

    def check(self, targets):
        files = []
        for target in targets:
            t = Path(target).expanduser()
            if t.is_dir():
                files.extend(sorted(t.rglob("*.rs")))
            elif t.suffix == ".rs" and t.is_file():
                files.append(t)
            else:
                print(f"out of scope - not a .rs file or directory: {target}")
                return 2
        if not files:
            print("[FAIL] no .rs files found")
            return 1
        bad = 0
        for f in files:
            with tempfile.TemporaryDirectory() as tmp:
                r = subprocess.run(
                    ["rustc", "--edition", "2021", "-A", "warnings",
                     "--crate-type", "lib", "--emit=metadata",
                     "--out-dir", tmp, str(f)],
                    capture_output=True, text=True, timeout=120)
            if r.returncode == 0:
                print(f"[OK]   {f}")
            else:
                bad += 1
                print(f"[FAIL] {f}")
                first = (r.stderr or "").strip().splitlines()
                for line in first[:5]:
                    print(f"       {line}")
        print(f"{len(files) - bad}/{len(files)} valid, {bad} invalid")
        return 1 if bad else 0

    def build(self, crate_dir):
        d = Path(crate_dir).expanduser()
        if not (d / "Cargo.toml").is_file():
            print(f"[FAIL] no Cargo.toml in {d}")
            return 1
        r = subprocess.run(["cargo", "check", "--quiet"], cwd=str(d),
                          capture_output=True, text=True, timeout=300)
        if r.returncode == 0:
            print(f"[OK]   cargo check passed: {d}")
            return 0
        print(f"[FAIL] cargo check failed: {d}")
        for line in (r.stderr or "").strip().splitlines()[:8]:
            print(f"       {line}")
        return 1
