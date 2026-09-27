"""commandline-wizard core: declared test suites, executed, reported."""
import os
import re
import subprocess
import shutil
from datetime import datetime
from pathlib import Path

REPORTS_DIR = Path.home() / "wizard_central" / "commandline-wizard" / "reports"

# Suite: fleet census baseline (extend freely - name, argv, timeout)
FLEET_SUITE = [
    ("pythonwiz on PATH",      ["pythonwiz", "check", str(Path.home() / "wizard_central")], 120),
    ("truthwiz law",           ["truthwiz", "law"],                                          10),
    ("truthwiz inject",        ["truthwiz", "inject", str(Path.home() / "micro_runners")],   10),
    ("diffwiz null test",      ["diffwiz", "files", "" + os.path.expanduser("~") + "/micro_runners/config.py",
                                "" + os.path.expanduser("~") + "/micro_runners/config.py"],                       30),
    ("ollamawiz ps",           ["ollamawiz", "ps"],                                          15),
    ("todowiz stats",          ["todowiz", "stats"],                                         15),
    ("jsonwiz self-test",      ["jsonwiz", "validate", "" + os.path.expanduser("~") + "/wizard_central/commandline-wizard/tests/fixture.json"], 15),
    ("git wizard_central",     ["git", "-C", "" + os.path.expanduser("~") + "/wizard_central", "status", "-sb"],  15),
    ("git micro_runners",      ["git", "-C", "" + os.path.expanduser("~") + "/micro_runners", "status", "-sb"],   15),
    ("ollama daemon alive",    ["curl", "-s", "http://localhost:11434/api/version"],         10),
    # --- full census extension: every citizen counted ---
    ("bannerwiz present",        ["bash", "-lc", "command -v bannerwiz"],                       10),
    ("bashwiz present",          ["bash", "-lc", "command -v bashwiz"],                         10),
    ("bootstrapwiz present",     ["bash", "-lc", "command -v bootstrapwiz"],                    10),
    ("benchwiz present",         ["bash", "-lc", "command -v benchwiz"],                        10),
    ("codeguardwiz present",     ["bash", "-lc", "command -v codeguardwiz"],                    10),
    ("daemonwiz present",        ["bash", "-lc", "command -v daemonwiz"],                       10),
    ("dotfilewiz present",       ["bash", "-lc", "command -v dotfilewiz"],                       10),
    ("helpwiz present",          ["bash", "-lc", "command -v helpwiz"],                          10),
    ("manualwiz present",        ["bash", "-lc", "command -v manualwiz"],                        10),
    ("modelfilewiz present",     ["bash", "-lc", "command -v modelfilewiz"],                    10),
    ("mode-manifestingwiz present", ["bash", "-lc", "command -v mode-manifestingwiz"],          10),
    ("probewiz present",         ["bash", "-lc", "command -v probewiz"],                         10),
    ("readwiz present",          ["bash", "-lc", "command -v readwiz"],                          10),
    ("repl-managerwiz present",  ["bash", "-lc", "command -v repl-managerwiz"],                 10),
    ("rustwiz present",          ["bash", "-lc", "command -v rustwiz"],                          10),
    ("voicewiz present",         ["bash", "-lc", "command -v voicewiz"],                        10),
    ("writewiz present",         ["bash", "-lc", "command -v writewiz"],                         10),
    ("truthd heartbeat",         ["bash", "-lc", "truthdwiz ping | grep -q OK"],                15),
    ("truthd systemd active",    ["systemctl", "--user", "is-active", "truthd"],                10),
]

DANGER_PATTERNS = [
    ("rm -rf on home/root paths", r"rm\s+-rf\s+[~/]"),
    ("piped curl to shell",       r"curl[^|]*\|\s*(ba)?sh"),
    ("chmod 777",                r"chmod\s+777"),
    ("sudo force/remove",        r"sudo\s+\S*(remove|purge|dd)"),
    ("dd to device",             r"dd\s+.*of=/dev/"),
]

class CommandLineWizard:
    """Runs declared checks; verdicts only, never opinions."""


    def analyze_history(self, history_path, top_n=15):
        try:
            lines = Path(history_path).read_text(errors="replace").splitlines()
        except OSError:
            return None
        cmds = {}
        dangers = []
        for i, ln in enumerate(lines, 1):
            s = ln.strip()
            if not s or s.startswith("#"):
                continue
            head = s.split()[0]
            if head in ("sudo", "git", "pip3", "python3", "ollama", "ollamawiz"):
                parts = s.split()
                head = " ".join(parts[:2]) if len(parts) > 1 else head
            cmds[head] = cmds.get(head, 0) + 1
            for label, pat in DANGER_PATTERNS:
                if re.search(pat, s):
                    dangers.append((i, label, s[:120]))
        top = sorted(cmds.items(), key=lambda kv: -kv[1])[:top_n]
        return {"total_lines": len(lines), "unique_commands": len(cmds),
                "top": top, "dangerous": dangers}


    def analyze_sessions(self, sessions_dir):
        findings = []
        for fp in sorted(Path(sessions_dir).glob("*.json")):
            blob = fp.read_text(errors="replace")
            tools = blob.count("TOOL:")
            fabs = [phrase for phrase in
                    ("Here is the output of", "output of the command", "output of `")
                    if phrase in blob]
            findings.append({
                "file": fp.name,
                "tool_requests": tools,
                "fab_count": len(fabs),
            })
        return findings

    def run_suite(self, suite):
        results = []
        for name, argv, timeout in suite:
            missing = shutil.which(argv[0]) is None
            if missing:
                results.append({"name": name, "verdict": "[FAIL]", "detail": f"binary not on PATH: {argv[0]}"})
                continue
            try:
                r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
                ok = r.returncode == 0
                detail = (r.stdout.strip() or r.stderr.strip())[:400]
                results.append({"name": name, "verdict": "[OK]" if ok else "[FAIL]", "detail": detail})
            except subprocess.TimeoutExpired:
                results.append({"name": name, "verdict": "[FAIL]", "detail": f"timeout after {timeout}s"})
            except Exception as e:
                results.append({"name": name, "verdict": "[FAIL]", "detail": str(e)[:400]})
        return results

    def write_report(self, results, label):
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        path = REPORTS_DIR / f"census-{label}-{ts}.txt"
        lines = [f"commandline-wizard census: {label} @ {ts}", "=" * 50]
        for r in results:
            lines.append(f"{r['verdict']} {r['name']}")
            if r["verdict"] == "[FAIL]":
                lines.append(f"       {r['detail']}")
        passed = sum(1 for r in results if r["verdict"] == "[OK]")
        lines.append("=" * 50)
        lines.append(f"{passed}/{len(results)} passed")
        path.write_text("\n".join(lines) + "\n")
        return path, passed, len(results)
