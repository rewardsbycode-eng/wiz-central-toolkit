"""codeguardwiz CLI: watch / severity / explain / scaffold / fix / scan.
Network is blocked for every test; audit/fix results are canned where needed."""
import json
import subprocess
import sys
import types
import urllib.request

import pytest

from wiz_central_toolkit.codeguardwiz import cli as cgcli
from wiz_central_toolkit.codeguardwiz.cli import main


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def boom(*a, **k):
        raise OSError("network blocked in tests")

    monkeypatch.setattr(urllib.request, "urlopen", boom)
    monkeypatch.delenv("CODEGUARD_AUDIT_MODEL", raising=False)
    monkeypatch.delenv("CODEGUARD_FIX_MODEL", raising=False)


def _run(monkeypatch, *argv):
    monkeypatch.setattr(sys, "argv", ["codeguardwiz", *argv])
    return main()


def _file(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text)
    return p


def _issue(sev, title="T", lines="1-2"):
    return {"severity": sev, "title": title, "line_range": lines,
            "description": "because"}


def _result(*issues):
    counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for i in issues:
        counts[i["severity"]] += 1
    return {"status": "OK", "filepath": "f", "language": "python", "model": "m",
            "issues_count": counts, "audit": {"score": 70, "issues": list(issues)}}


FAILED = {"status": "FAILED", "reason": "daemon down"}


# ---------- watch ----------

def test_watch_ok(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(cgcli, "audit", lambda p: _result(_issue("HIGH")))
    p = _file(tmp_path, "a.py", "x = 1\n")
    assert _run(monkeypatch, "watch", str(p)) == 0
    assert "score=70" in capsys.readouterr().out


def test_watch_missing_file(monkeypatch, capsys, tmp_path):
    assert _run(monkeypatch, "watch", str(tmp_path / "nope.py")) == 1
    assert "[FAIL] not a file" in capsys.readouterr().out


def test_watch_audit_failed(monkeypatch, tmp_path):
    monkeypatch.setattr(cgcli, "audit", lambda p: FAILED)
    p = _file(tmp_path, "a.py", "x = 1\n")
    assert _run(monkeypatch, "watch", str(p)) == 1


# ---------- severity ----------

def _sev_issues():
    return _result(_issue("CRITICAL", "Crit"), _issue("HIGH", "Hi"),
                   _issue("MEDIUM", "Med"), _issue("LOW", "Lo"))


def test_severity_default_high_includes_critical(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(cgcli, "audit", lambda p: _sev_issues())
    p = _file(tmp_path, "a.py", "x = 1\n")
    assert _run(monkeypatch, "severity", str(p)) == 1
    out = capsys.readouterr().out
    assert "HIGH+ severity: 2 findings" in out
    assert "Crit" in out and "Hi" in out
    assert "Med" not in out


def test_severity_medium_includes_high_and_critical(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(cgcli, "audit", lambda p: _sev_issues())
    p = _file(tmp_path, "a.py", "x = 1\n")
    assert _run(monkeypatch, "severity", str(p), "--threshold", "MEDIUM") == 1
    out = capsys.readouterr().out
    assert "MEDIUM+ severity: 3 findings" in out
    assert "Lo" not in out.replace("Lo\n", "", 0) or "[LOW]" not in out


def test_severity_critical_only(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(cgcli, "audit", lambda p: _sev_issues())
    p = _file(tmp_path, "a.py", "x = 1\n")
    assert _run(monkeypatch, "severity", str(p), "--threshold", "CRITICAL") == 1
    assert "CRITICAL+ severity: 1 findings" in capsys.readouterr().out


def test_severity_clean_returns_zero(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(cgcli, "audit", lambda p: _result(_issue("LOW")))
    p = _file(tmp_path, "a.py", "x = 1\n")
    assert _run(monkeypatch, "severity", str(p)) == 0
    assert "0 findings" in capsys.readouterr().out


def test_severity_failed_audit_is_not_reported_clean(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(cgcli, "audit", lambda p: FAILED)
    p = _file(tmp_path, "a.py", "x = 1\n")
    assert _run(monkeypatch, "severity", str(p)) == 1
    assert "[FAIL]" in capsys.readouterr().out


def test_severity_missing_file(monkeypatch, capsys, tmp_path):
    assert _run(monkeypatch, "severity", str(tmp_path / "nope.py")) == 1
    assert "[FAIL] not a file" in capsys.readouterr().out


# ---------- explain ----------

def test_explain_line_inside_range(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(cgcli, "audit", lambda p: _result(_issue("HIGH", "Bad", "10-12")))
    p = _file(tmp_path, "a.py", "x = 1\n")
    assert _run(monkeypatch, "explain", str(p), "11") == 0
    out = capsys.readouterr().out
    assert "Title: Bad" in out and "Message: because" in out


def test_explain_single_line_range(monkeypatch, tmp_path):
    monkeypatch.setattr(cgcli, "audit", lambda p: _result(_issue("HIGH", "Bad", "5")))
    p = _file(tmp_path, "a.py", "x = 1\n")
    assert _run(monkeypatch, "explain", str(p), "5") == 0


def test_explain_does_not_match_by_substring(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(cgcli, "audit", lambda p: _result(_issue("HIGH", "Bad", "10-12")))
    p = _file(tmp_path, "a.py", "x = 1\n")
    assert _run(monkeypatch, "explain", str(p), "1") == 1
    assert "no issue found at line 1" in capsys.readouterr().out


def test_explain_no_issues(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(cgcli, "audit", lambda p: _result())
    p = _file(tmp_path, "a.py", "x = 1\n")
    assert _run(monkeypatch, "explain", str(p), "3") == 1


def test_explain_missing_file(monkeypatch, capsys, tmp_path):
    assert _run(monkeypatch, "explain", str(tmp_path / "nope.py"), "3") == 1
    assert "[FAIL] not a file" in capsys.readouterr().out


# ---------- scaffold ----------

def test_scaffold_lists_public_defs_and_writes_nothing(monkeypatch, capsys, tmp_path):
    src = "def public():\n    pass\n\ndef _private():\n    pass\n\nclass Thing:\n    pass\n"
    p = _file(tmp_path, "a.py", src)
    assert _run(monkeypatch, "scaffold", str(p)) == 0
    out = capsys.readouterr().out
    assert "def test_public_exists" in out
    assert "def test_Thing_importable" in out
    assert "test__private" not in out
    assert "functions: 1, classes: 1" in out
    assert sorted(x.name for x in tmp_path.iterdir()) == ["a.py"]


def test_scaffold_empty_file(monkeypatch, capsys, tmp_path):
    p = _file(tmp_path, "a.py", "")
    assert _run(monkeypatch, "scaffold", str(p)) == 0
    assert "no public top-level defs" in capsys.readouterr().out


def test_scaffold_syntax_error(monkeypatch, capsys, tmp_path):
    p = _file(tmp_path, "a.py", "def broken(:\n")
    assert _run(monkeypatch, "scaffold", str(p)) == 1
    assert "[FAIL] cannot parse" in capsys.readouterr().out


def test_scaffold_missing_file(monkeypatch, capsys, tmp_path):
    assert _run(monkeypatch, "scaffold", str(tmp_path / "nope.py")) == 1
    assert "[FAIL] not a file" in capsys.readouterr().out


# ---------- fix ----------

FIXED = {"status": "OK", "issues_fixed": 1, "fix_model": "m", "fixed_code": "NEW\n"}


def test_fix_missing_file(monkeypatch, capsys, tmp_path):
    assert _run(monkeypatch, "fix", str(tmp_path / "nope.py")) == 1
    assert "[FAIL] not a file" in capsys.readouterr().out


def test_fix_failure_is_reported(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(cgcli, "fix", lambda p: {"status": "FAILED", "reason": "nope"})
    p = _file(tmp_path, "a.js", "OLD\n")
    assert _run(monkeypatch, "fix", str(p)) == 1
    assert "[FAIL] nope" in capsys.readouterr().out


def test_fix_nothing_to_fix(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(cgcli, "fix", lambda p: {
        "status": "OK", "issues_fixed": 0, "message": "no issues to fix"})
    p = _file(tmp_path, "a.js", "OLD\n")
    assert _run(monkeypatch, "fix", str(p)) == 0
    assert "[OK] no issues to fix" in capsys.readouterr().out


def test_fix_preview_leaves_disk_untouched(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(cgcli, "fix", lambda p: FIXED)
    p = _file(tmp_path, "a.js", "OLD\n")
    assert _run(monkeypatch, "fix", str(p)) == 0
    out = capsys.readouterr().out
    assert "preview only" in out and "NEW" in out
    assert p.read_text() == "OLD\n"


def test_fix_write_non_python(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(cgcli, "fix", lambda p: FIXED)
    p = _file(tmp_path, "a.js", "OLD\n")
    assert _run(monkeypatch, "fix", str(p), "--write") == 0
    assert p.read_text() == "NEW\n"
    assert "[OK] written" in capsys.readouterr().out


def test_fix_out_path_keeps_original(monkeypatch, tmp_path):
    monkeypatch.setattr(cgcli, "fix", lambda p: FIXED)
    p = _file(tmp_path, "a.js", "OLD\n")
    out = tmp_path / "b.js"
    assert _run(monkeypatch, "fix", str(p), "--out", str(out)) == 0
    assert out.read_text() == "NEW\n"
    assert p.read_text() == "OLD\n"


def test_fix_python_gate_passes_and_uses_this_interpreter(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(cgcli, "fix", lambda p: FIXED)
    seen = {}

    def fake_run(cmd, **kw):
        seen["cmd"] = cmd
        return types.SimpleNamespace(returncode=0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    p = _file(tmp_path, "a.py", "OLD\n")
    assert _run(monkeypatch, "fix", str(p), "--write") == 0
    assert seen["cmd"][0] == sys.executable
    assert "wiz_central_toolkit.pythonwiz" in seen["cmd"]
    assert p.read_text() == "NEW\n"
    assert "gate passed" in capsys.readouterr().out


def test_fix_python_gate_rejection_writes_nothing(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(cgcli, "fix", lambda p: FIXED)
    monkeypatch.setattr(subprocess, "run",
                        lambda cmd, **kw: types.SimpleNamespace(returncode=1))
    p = _file(tmp_path, "a.py", "OLD\n")
    assert _run(monkeypatch, "fix", str(p), "--write") == 1
    assert p.read_text() == "OLD\n"
    assert "rejected" in capsys.readouterr().out


# ---------- scan ----------

def test_scan_failed_audits_are_not_reported_clean(monkeypatch, capsys, tmp_path):
    _file(tmp_path, "a.py", "x = 1\n")
    assert _run(monkeypatch, "scan", str(tmp_path)) == 1
    assert "could not be audited" in capsys.readouterr().out


def test_scan_lists_findings_and_fails(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(cgcli, "audit", lambda p: _result(_issue("HIGH")))
    _file(tmp_path, "a.py", "x = 1\n")
    assert _run(monkeypatch, "scan", str(tmp_path)) == 1
    out = capsys.readouterr().out
    assert "HIGH=1" in out and "a.py: C=0 H=1" in out


def test_scan_json_output(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(cgcli, "audit", lambda p: _result())
    _file(tmp_path, "a.py", "x = 1\n")
    assert _run(monkeypatch, "scan", str(tmp_path), "--json") == 0
    data = json.loads(capsys.readouterr().out)
    assert data == {"files_scanned": 1, "failed": 0, "findings": []}


def test_python_gate_really_rejects_broken_code(monkeypatch, capsys, tmp_path):
    """No subprocess mock: the real pythonwiz gate must reject a syntax error."""
    monkeypatch.setattr(cgcli, "fix", lambda p: {
        "status": "OK", "issues_fixed": 1, "fix_model": "m",
        "fixed_code": "def broken(:\n"})
    p = _file(tmp_path, "a.py", "OLD\n")
    assert _run(monkeypatch, "fix", str(p), "--write") == 1
    assert p.read_text() == "OLD\n"
