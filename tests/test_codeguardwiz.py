"""codeguardwiz tests. urlopen is stubbed for every test: no real daemon is touched."""
import json
import sys
import urllib.request

import pytest

from wiz_central_toolkit.codeguardwiz import codeguard_wizard as cg
from wiz_central_toolkit.codeguardwiz.cli import main

GOOD_AUDIT = json.dumps({
    "score": 80,
    "issues": [{"severity": "HIGH", "title": "Bad thing", "line_range": "1-2"}],
})


class _Resp:
    def __init__(self, payload):
        self._body = json.dumps(payload).encode()

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


@pytest.fixture(autouse=True)
def ollama(monkeypatch):
    """Fake daemon. Tests tweak the returned dict to change behavior."""
    state = {"models": ["m"], "reply": "", "tags_fail": False, "gen_fail": False}

    def fake_urlopen(req, timeout=None):
        url = getattr(req, "full_url", req)
        if url.endswith("/api/tags"):
            if state["tags_fail"]:
                raise OSError("daemon down")
            return _Resp({"models": [{"name": n} for n in state["models"]]})
        if url.endswith("/api/generate"):
            if state["gen_fail"]:
                raise OSError("daemon down")
            return _Resp({"response": state["reply"]})
        raise AssertionError(f"unexpected url {url}")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    monkeypatch.delenv("CODEGUARD_AUDIT_MODEL", raising=False)
    monkeypatch.delenv("CODEGUARD_FIX_MODEL", raising=False)
    return state


def _file(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text)
    return p


def _run(monkeypatch, *argv):
    monkeypatch.setattr(sys, "argv", ["codeguardwiz", *argv])
    return main()


# ---------- pick_seat ----------

def test_pick_seat_override_in_roster(monkeypatch):
    monkeypatch.setenv("X_SEAT", "b")
    assert cg.pick_seat(["a", "b"], ["a"], "X_SEAT") == "b"


def test_pick_seat_override_not_served(monkeypatch):
    monkeypatch.setenv("X_SEAT", "zzz")
    assert cg.pick_seat(["a", "b"], ["a"], "X_SEAT") is None


def test_pick_seat_override_with_empty_roster(monkeypatch):
    monkeypatch.setenv("X_SEAT", "zzz")
    assert cg.pick_seat([], ["a"], "X_SEAT") == "zzz"


def test_pick_seat_preference_matches_family(monkeypatch):
    monkeypatch.delenv("X_SEAT", raising=False)
    roster = ["llama3:8b", "qwen2.5-coder:3b"]
    assert cg.pick_seat(roster, ["qwen2.5-coder:7b"], "X_SEAT") == "qwen2.5-coder:3b"


def test_pick_seat_no_match(monkeypatch):
    monkeypatch.delenv("X_SEAT", raising=False)
    assert cg.pick_seat(["llama3:8b"], ["qwen2.5-coder:7b"], "X_SEAT") is None


# ---------- load_roster ----------

def test_load_roster_sorted(ollama):
    ollama["models"] = ["z", "a"]
    assert cg.load_roster() == ["a", "z"]


def test_load_roster_unreachable(ollama):
    ollama["tags_fail"] = True
    assert cg.load_roster() == []


# ---------- detect_language / helpers ----------

def test_detect_language_by_extension(tmp_path):
    assert cg.detect_language(str(_file(tmp_path, "a.py", "x = 1\n"))) == "python"


def test_detect_language_dockerfile(tmp_path):
    assert cg.detect_language(str(_file(tmp_path, "Dockerfile", "FROM x\n"))) == "dockerfile"


def test_detect_language_shebang(tmp_path):
    p = _file(tmp_path, "script", "#!/usr/bin/env python3\nprint('hi')\n")
    assert cg.detect_language(str(p)) == "python"


def test_detect_language_content_sniff(tmp_path):
    p = _file(tmp_path, "noext", "def a():\n    import os\n    print(1)\n")
    assert cg.detect_language(str(p)) == "python"


def test_detect_language_unknown(tmp_path):
    assert cg.detect_language(str(_file(tmp_path, "notes", "hello there\n"))) == "unknown"


def test_try_parse_json_plain():
    assert cg._try_parse_json('{"a": 1}') == {"a": 1}


def test_try_parse_json_embedded_in_prose():
    assert cg._try_parse_json('Sure! Here it is: {"a": 1} hope that helps') == {"a": 1}


def test_try_parse_json_garbage():
    assert cg._try_parse_json("no json here") is None


def test_read_code_missing_returns_none(tmp_path):
    assert cg.read_code(str(tmp_path / "nope.py")) is None


# ---------- audit ----------

def test_audit_unreadable_file(tmp_path):
    r = cg.audit(str(tmp_path / "nope.py"))
    assert r == {"status": "FAILED", "reason": "cannot read file"}


def test_audit_unknown_language(tmp_path):
    r = cg.audit(str(_file(tmp_path, "notes", "hello there\n")))
    assert r["status"] == "FAILED"
    assert r["reason"] == "cannot detect language"


def test_audit_ok(tmp_path, ollama):
    ollama["reply"] = GOOD_AUDIT
    r = cg.audit(str(_file(tmp_path, "a.py", "x = 1\n")), model="m")
    assert r["status"] == "OK"
    assert r["language"] == "python"
    assert r["model"] == "m"
    assert r["issues_count"]["HIGH"] == 1
    assert r["audit"]["score"] == 80


def test_audit_call_failed(tmp_path, ollama):
    ollama["gen_fail"] = True
    r = cg.audit(str(_file(tmp_path, "a.py", "x = 1\n")), model="m")
    assert r["status"] == "FAILED"
    assert r["reason"] == "ollama audit call failed"


def test_audit_unparseable_response(tmp_path, ollama):
    ollama["reply"] = "totally not json"
    r = cg.audit(str(_file(tmp_path, "a.py", "x = 1\n")), model="m")
    assert r["status"] == "FAILED"
    assert r["reason"] == "unparseable audit response"


def test_audit_no_seat_when_daemon_down(tmp_path, ollama):
    ollama["tags_fail"] = True
    r = cg.audit(str(_file(tmp_path, "a.py", "x = 1\n")))
    assert r["status"] == "FAILED"
    assert "no audit seat" in r["reason"]
    assert r["roster_size"] == 0


# ---------- fix ----------

def test_fix_unreadable_file(tmp_path):
    assert cg.fix(str(tmp_path / "nope.py"))["reason"] == "cannot read file"


def test_fix_with_no_issues_returns_original(tmp_path):
    p = _file(tmp_path, "a.py", "x = 1\n")
    r = cg.fix(str(p), audit_result={"language": "python", "audit": {"issues": []}})
    assert r["status"] == "OK"
    assert r["issues_fixed"] == 0
    assert r["fixed_code"] == "x = 1\n"


def test_fix_strips_markdown_fences(tmp_path, ollama):
    ollama["reply"] = "```python\nx = 1\n```"
    p = _file(tmp_path, "a.py", "x=1\n")
    r = cg.fix(str(p), audit_result={"language": "python",
                                     "audit": {"issues": [{"severity": "HIGH"}]}},
               model="m")
    assert r["status"] == "OK"
    assert r["fixed_code"] == "x = 1"


def test_fix_call_failed(tmp_path, ollama):
    ollama["gen_fail"] = True
    p = _file(tmp_path, "a.py", "x=1\n")
    r = cg.fix(str(p), audit_result={"language": "python",
                                     "audit": {"issues": [{"severity": "HIGH"}]}},
               model="m")
    assert r == {"status": "FAILED", "reason": "ollama fix call failed"}


# ---------- CLI ----------

def test_cli_no_args_prints_help(monkeypatch, capsys):
    assert _run(monkeypatch) == 0
    assert "usage" in capsys.readouterr().out.lower()


def test_cli_roster(monkeypatch, capsys, ollama):
    ollama["models"] = ["qwen2.5-coder:3b", "llama3:8b"]
    assert _run(monkeypatch, "roster") == 0
    out = capsys.readouterr().out
    assert "[OK] llama3:8b" in out
    assert "qwen2.5-coder:3b" in out


def test_cli_roster_empty(monkeypatch, capsys, ollama):
    ollama["tags_fail"] = True
    assert _run(monkeypatch, "roster") == 1
    assert "[FAIL] daemon unreachable" in capsys.readouterr().out


def test_cli_lang_ok(monkeypatch, capsys, tmp_path):
    p = _file(tmp_path, "a.py", "x = 1\n")
    assert _run(monkeypatch, "lang", str(p)) == 0
    assert "python" in capsys.readouterr().out


def test_cli_lang_missing_file(monkeypatch, capsys, tmp_path):
    assert _run(monkeypatch, "lang", str(tmp_path / "nope.py")) == 1
    assert "[FAIL] not a file" in capsys.readouterr().out


def test_cli_lang_undetectable(monkeypatch, capsys, tmp_path):
    p = _file(tmp_path, "notes", "hello there\n")
    assert _run(monkeypatch, "lang", str(p)) == 2
    assert "out of scope" in capsys.readouterr().out


def test_cli_audit_missing_file(monkeypatch, capsys, tmp_path):
    assert _run(monkeypatch, "audit", str(tmp_path / "nope.py")) == 1
    assert "[FAIL] not a file" in capsys.readouterr().out


def test_cli_audit_ok(monkeypatch, capsys, tmp_path, ollama):
    monkeypatch.setenv("CODEGUARD_AUDIT_MODEL", "m")
    ollama["reply"] = GOOD_AUDIT
    p = _file(tmp_path, "a.py", "x = 1\n")
    assert _run(monkeypatch, "audit", str(p)) == 0
    out = capsys.readouterr().out
    assert "[OK]" in out
    assert "HIGH=1" in out
    assert "Bad thing" in out


def test_cli_scan_not_a_directory(monkeypatch, capsys, tmp_path):
    assert _run(monkeypatch, "scan", str(tmp_path / "nope")) == 1
    assert "[FAIL] not a directory" in capsys.readouterr().out


def test_cli_scan_ok(monkeypatch, capsys, tmp_path, ollama):
    monkeypatch.setenv("CODEGUARD_AUDIT_MODEL", "m")
    ollama["reply"] = GOOD_AUDIT
    _file(tmp_path, "a.py", "x = 1\n")
    _run(monkeypatch, "scan", str(tmp_path))
    out = capsys.readouterr().out
    assert "scanned 1 files" in out
    assert "HIGH=1" in out
