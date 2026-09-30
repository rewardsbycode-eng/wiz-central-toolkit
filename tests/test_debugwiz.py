"""Tests for debugwiz — ported from wizard_central's debug-wizard.
Isolates BANK/IGNORE_LIST to a tmp dir so tests never touch the real ~/.debug-wizard/."""
import pytest

from wiz_central_toolkit.debugwiz import __main__ as debugwiz_main
from wiz_central_toolkit.debugwiz import debug_wizard


@pytest.fixture(autouse=True)
def isolate_debug_wizard_bank(tmp_path, monkeypatch):
    bank = tmp_path / ".debug-wizard"
    monkeypatch.setattr(debug_wizard, "BANK", bank)
    monkeypatch.setattr(debug_wizard, "IGNORE_LIST", bank / "ignored.json")


def _write(tmp_path, name, content):
    p = tmp_path / name
    p.write_text(content)
    return p


# ---------- brain-level tests ----------

class TestTraceClassify:
    def test_trace_valid_file(self, tmp_path):
        f = _write(tmp_path, "good.py", 'print("hi")')
        r = debug_wizard.trace(f)
        assert r["ok"] is True
        assert r["errors"] == []

    def test_trace_syntax_error(self, tmp_path):
        f = _write(tmp_path, "bad.py", "def f(:")
        r = debug_wizard.trace(f)
        assert r["ok"] is False
        assert r["errors"][0]["type"] == "SyntaxError"

    def test_classify_counts_types(self, tmp_path):
        f = _write(tmp_path, "bad.py", "def f(:")
        r = debug_wizard.classify_file(f)
        assert r["total"] == 1
        assert "SyntaxError" in r["classification"]


class TestLocate:
    def test_locate_finds_matching_pattern(self, tmp_path):
        _write(tmp_path, "bad.py", "def f(:")
        _write(tmp_path, "good.py", "print(1)")
        hits = debug_wizard.locate(tmp_path, "SyntaxError")
        assert len(hits) == 1
        assert hits[0].endswith("bad.py")

    def test_locate_no_match(self, tmp_path):
        _write(tmp_path, "good.py", "print(1)")
        hits = debug_wizard.locate(tmp_path, "SyntaxError")
        assert hits == []


class TestCountHotspotTimeline:
    def test_count_dir(self, tmp_path):
        _write(tmp_path, "bad.py", "def f(:")
        r = debug_wizard.count_dir(tmp_path)
        assert r["files_checked"] == 1
        assert r["totals"]["SyntaxError"] == 1

    def test_hotspot_ranks_by_error_count(self, tmp_path):
        _write(tmp_path, "bad.py", "def f(:")
        hits = debug_wizard.hotspot(tmp_path)
        assert len(hits) == 1
        assert hits[0][0].endswith("bad.py")

    def test_timeline_lists_errored_files(self, tmp_path):
        _write(tmp_path, "bad.py", "def f(:")
        data = debug_wizard.timeline(tmp_path)
        assert len(data) == 1
        assert data[0]["errors"] == 1


class TestAuditReport:
    def test_audit_dir_healthy(self, tmp_path):
        _write(tmp_path, "good.py", "print(1)")
        r = debug_wizard.audit_dir(tmp_path)
        assert r["healthy"] == 1
        assert r["unhealthy"] == 0
        assert r["health_pct"] == 100.0

    def test_audit_dir_unhealthy(self, tmp_path):
        _write(tmp_path, "bad.py", "def f(:")
        r = debug_wizard.audit_dir(tmp_path)
        assert r["unhealthy"] == 1
        assert r["health_pct"] == 0.0

    def test_report_json_is_valid_json(self, tmp_path):
        import json
        _write(tmp_path, "good.py", "print(1)")
        out = debug_wizard.report_json(str(tmp_path))
        parsed = json.loads(out)
        assert "audit" in parsed


class TestIgnoreList:
    def test_add_ignore(self, tmp_path):
        r = debug_wizard.add_ignore(str(tmp_path))
        assert r["ok"] is True

    def test_add_ignore_duplicate_fails(self, tmp_path):
        debug_wizard.add_ignore(str(tmp_path))
        r = debug_wizard.add_ignore(str(tmp_path))
        assert r["ok"] is False

    def test_remove_ignore(self, tmp_path):
        debug_wizard.add_ignore(str(tmp_path))
        r = debug_wizard.remove_ignore(str(tmp_path))
        assert r["ok"] is True

    def test_remove_ignore_not_present_fails(self, tmp_path):
        r = debug_wizard.remove_ignore(str(tmp_path))
        assert r["ok"] is False

    def test_load_ignored_empty_by_default(self):
        assert debug_wizard.load_ignored() == []


class TestSuggestFix:
    def test_suggest_fix_ok_file(self, tmp_path):
        f = _write(tmp_path, "good.py", "print(1)")
        out = debug_wizard.suggest_fix(f)
        assert "[OK]" in out

    def test_suggest_fix_broken_file(self, tmp_path):
        f = _write(tmp_path, "bad.py", "def f(:")
        out = debug_wizard.suggest_fix(f)
        assert "[ISSUE]" in out


# ---------- CLI dispatch tests ----------

class TestCLI:
    def test_help_no_args(self, capsys):
        rc = debugwiz_main.main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "usage: debugwiz" in out

    def test_law(self, capsys):
        rc = debugwiz_main.main(["law"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "DEBUG LAW" in out

    def test_versions(self, capsys):
        rc = debugwiz_main.main(["versions"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "debug_law_sha256" in out

    def test_trace_ok(self, tmp_path, capsys):
        f = _write(tmp_path, "good.py", "print(1)")
        rc = debugwiz_main.main(["trace", str(f)])
        out = capsys.readouterr().out
        assert rc == 0
        assert "[OK]" in out

    def test_trace_fail(self, tmp_path, capsys):
        f = _write(tmp_path, "bad.py", "def f(:")
        rc = debugwiz_main.main(["trace", str(f)])
        out = capsys.readouterr().out
        assert rc == 1
        assert "[ERR]" in out

    def test_locate_dispatches_for_real(self, tmp_path, capsys):
        """Regression test for the bug where locate was documented but never dispatched."""
        _write(tmp_path, "bad.py", "def f(:")
        rc = debugwiz_main.main(["locate", str(tmp_path), "SyntaxError"])
        out = capsys.readouterr().out
        assert rc == 1
        assert "[MATCH]" in out
        assert "out of scope" not in out

    def test_locate_requires_two_args(self, capsys):
        rc = debugwiz_main.main(["locate", "/tmp"])
        assert rc == 2

    def test_classify(self, tmp_path, capsys):
        f = _write(tmp_path, "bad.py", "def f(:")
        rc = debugwiz_main.main(["classify", str(f)])
        out = capsys.readouterr().out
        assert rc == 1
        assert "SyntaxError" in out

    def test_count(self, tmp_path, capsys):
        _write(tmp_path, "bad.py", "def f(:")
        rc = debugwiz_main.main(["count", str(tmp_path)])
        out = capsys.readouterr().out
        assert rc == 0
        assert "files=" in out

    def test_hotspot(self, tmp_path, capsys):
        _write(tmp_path, "bad.py", "def f(:")
        rc = debugwiz_main.main(["hotspot", str(tmp_path)])
        out = capsys.readouterr().out
        assert rc == 1
        assert "[HOT]" in out

    def test_hotspot_all_healthy(self, tmp_path, capsys):
        _write(tmp_path, "good.py", "print(1)")
        rc = debugwiz_main.main(["hotspot", str(tmp_path)])
        out = capsys.readouterr().out
        assert rc == 0
        assert "all files healthy" in out

    def test_timeline(self, tmp_path, capsys):
        _write(tmp_path, "bad.py", "def f(:")
        rc = debugwiz_main.main(["timeline", str(tmp_path)])
        out = capsys.readouterr().out
        assert rc == 0

    def test_audit_healthy(self, tmp_path, capsys):
        _write(tmp_path, "good.py", "print(1)")
        rc = debugwiz_main.main(["audit", str(tmp_path)])
        out = capsys.readouterr().out
        assert rc == 0
        assert "[OK] all files healthy" in out

    def test_audit_unhealthy(self, tmp_path, capsys):
        _write(tmp_path, "bad.py", "def f(:")
        rc = debugwiz_main.main(["audit", str(tmp_path)])
        out = capsys.readouterr().out
        assert rc == 1

    def test_report(self, tmp_path, capsys):
        _write(tmp_path, "good.py", "print(1)")
        rc = debugwiz_main.main(["report", str(tmp_path)])
        out = capsys.readouterr().out
        assert rc == 0
        assert '"audit"' in out

    def test_log_fails_cleanly_no_writewiz(self, tmp_path, capsys):
        """Regression test: log must never shell out to a same-named PATH binary."""
        rc = debugwiz_main.main(["log", str(tmp_path)])
        out = capsys.readouterr().out
        assert rc == 1
        assert "not yet available" in out

    def test_ignore_and_ignored(self, tmp_path, capsys):
        rc = debugwiz_main.main(["ignore", str(tmp_path)])
        out = capsys.readouterr().out
        assert rc == 0
        assert "[OK] ignored" in out

        rc = debugwiz_main.main(["ignored"])
        out = capsys.readouterr().out
        assert rc == 0
        assert str(tmp_path) in out

    def test_stack_stub(self, tmp_path, capsys):
        f = _write(tmp_path, "good.py", "print(1)")
        rc = debugwiz_main.main(["stack", str(f)])
        out = capsys.readouterr().out
        assert rc == 0
        assert "not implemented" in out

    def test_preview_no_staged(self, tmp_path, capsys):
        f = _write(tmp_path, "good.py", "print(1)")
        rc = debugwiz_main.main(["preview", str(f)])
        out = capsys.readouterr().out
        assert rc == 0

    def test_unknown_command(self, capsys):
        rc = debugwiz_main.main(["bogus"])
        assert rc == 2

    def test_stats_no_real_paths(self, capsys):
        """stats_fleet checks hardcoded paths (~/tools etc.) — should degrade gracefully."""
        rc = debugwiz_main.main(["stats"])
        assert rc == 0


class TestAnalysisCommands:
    def test_imports_finds_undefined_name(self, tmp_path, capsys):
        f = _write(tmp_path, "missing.py", "print(missing_name)")
        rc = debugwiz_main.main(["imports", str(f)])
        out = capsys.readouterr().out
        assert rc == 1
        assert "missing_name" in out

    def test_names_reports_no_undefined_names(self, tmp_path, capsys):
        f = _write(tmp_path, "good.py", "print('hello')")
        rc = debugwiz_main.main(["names", str(f)])
        out = capsys.readouterr().out
        assert rc == 0
        assert "no undefined names" in out

    def test_signatures_finds_argument_mismatch(self, tmp_path, capsys):
        f = _write(
            tmp_path,
            "mismatch.py",
            "def greet(name):\n    return name\ngreet()\n",
        )
        rc = debugwiz_main.main(["signatures", str(f)])
        out = capsys.readouterr().out
        assert rc == 1
        assert "greet def=1 args, call=0" in out


def test_walk_does_not_prefix_match_ignored_paths(tmp_path):
    ignored = tmp_path / "foo"
    sibling = tmp_path / "foobar"
    ignored.mkdir()
    sibling.mkdir()
    _write(ignored, "hidden.py", "print('hidden')")
    visible = _write(sibling, "visible.py", "print('visible')")

    assert debug_wizard.add_ignore(str(ignored))["ok"] is True
    files = list(debug_wizard._walk_py_files(tmp_path))
    assert files == [visible]


def test_names_handles_imports_args_and_exception_names(tmp_path):
    f = _write(
        tmp_path,
        "bound_names.py",
        "import os.path\n"
        "from pathlib import Path as P\n"
        "def read(item):\n"
        "    try:\n"
        "        return P(item), os.path\n"
        "    except Exception as err:\n"
        "        return err\n",
    )

    assert debug_wizard.names(f) == []


def test_load_ignored_recovers_from_invalid_json():
    debug_wizard.BANK.mkdir(parents=True, exist_ok=True)
    debug_wizard.IGNORE_LIST.write_text("{not valid json")

    assert debug_wizard.load_ignored() == []
