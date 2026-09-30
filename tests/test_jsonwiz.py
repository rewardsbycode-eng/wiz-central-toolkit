"""Tests for jsonwiz — ported from wizard_central's json-wizard."""
import sys

import pytest

from wiz_central_toolkit.jsonwiz import __main__ as jsonwiz_main
from wiz_central_toolkit.jsonwiz.lib.json_wizard import JsonWizard

# ---------- JsonWizard brain unit tests ----------

class TestValidate:
    def test_valid_object(self):
        wiz = JsonWizard()
        r = wiz.validate('{"a": 1}')
        assert r["valid"] is True
        assert r["type"] == "dict"

    def test_invalid_json(self):
        wiz = JsonWizard()
        r = wiz.validate('{"a": }')
        assert r["valid"] is False
        assert "line" in r and "col" in r


class TestPrettyCompact:
    def test_pretty(self):
        wiz = JsonWizard()
        out = wiz.pretty('{"a":1}')
        assert '"a": 1' in out

    def test_compact(self):
        wiz = JsonWizard()
        out = wiz.compact('{"a": 1, "b": 2}')
        assert out == '{"a":1,"b":2}'


class TestInspectKeys:
    def test_inspect_summarizes_lists(self):
        wiz = JsonWizard()
        r = wiz.inspect('{"a": [1,2,3]}')
        assert r["a"] == {"_list_len": 3}

    def test_keys_on_object(self):
        wiz = JsonWizard()
        assert wiz.keys('{"a": 1, "b": 2}') == ["a", "b"]

    def test_keys_on_non_object(self):
        wiz = JsonWizard()
        assert wiz.keys('[1,2,3]') == []


class TestGet:
    def test_get_dict_path(self):
        wiz = JsonWizard()
        assert wiz.get('{"a": {"b": 5}}', "a.b") == 5

    def test_get_list_index(self):
        wiz = JsonWizard()
        assert wiz.get('{"a": [10, 20, 30]}', "a.1") == 20

    def test_get_missing_key_raises(self):
        wiz = JsonWizard()
        with pytest.raises(KeyError):
            wiz.get('{"a": 1}', "b")

    def test_get_out_of_range_raises(self):
        wiz = JsonWizard()
        with pytest.raises(IndexError):
            wiz.get('{"a": [1]}', "a.5")


class TestDiff:
    def test_diff_changed_value(self):
        wiz = JsonWizard()
        changes = wiz.diff('{"a": 1}', '{"a": 2}')
        assert changes == [("changed", ["a"], 1, 2)]

    def test_diff_identical(self):
        wiz = JsonWizard()
        assert wiz.diff('{"a": 1}', '{"a": 1}') == []

    def test_diff_added_removed(self):
        wiz = JsonWizard()
        changes = wiz.diff('{"a": 1}', '{"b": 2}')
        kinds = {c[0] for c in changes}
        assert kinds == {"added", "removed"}


class TestStats:
    def test_stats_counts_types(self):
        wiz = JsonWizard()
        r = wiz.stats('{"a": 1, "b": "x", "c": [1, 2]}')
        assert r["root_type"] == "dict"
        assert r["dict"] == 1
        assert r["list"] == 1
        assert r["number"] == 3
        assert r["str"] == 1


class TestMerge:
    def test_merge_b_wins_scalar(self):
        wiz = JsonWizard()
        assert wiz.merge('{"a": 1}', '{"a": 2}') == {"a": 2}

    def test_merge_deep(self):
        wiz = JsonWizard()
        r = wiz.merge('{"a": {"x": 1}}', '{"a": {"y": 2}}')
        assert r == {"a": {"x": 1, "y": 2}}

    def test_merge_requires_objects(self):
        wiz = JsonWizard()
        with pytest.raises(TypeError):
            wiz.merge('[1,2]', '[3,4]')


# ---------- CLI dispatch tests ----------

def _write(tmp_path, name, content):
    p = tmp_path / name
    p.write_text(content)
    return str(p)


class TestCLI:
    def test_help_no_args(self, capsys):
        rc = jsonwiz_main.main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "usage: jsonwiz" in out

    def test_validate_valid_file(self, tmp_path, capsys):
        f = _write(tmp_path, "good.json", '{"a": 1}')
        rc = jsonwiz_main.main(["validate", f])
        out = capsys.readouterr().out
        assert rc == 0
        assert "[OK]" in out

    def test_validate_invalid_file(self, tmp_path, capsys):
        f = _write(tmp_path, "bad.json", '{"a": }')
        rc = jsonwiz_main.main(["validate", f])
        out = capsys.readouterr().out
        assert rc == 1
        assert "[FAIL]" in out

    def test_validate_missing_file(self, tmp_path, capsys):
        rc = jsonwiz_main.main(["validate", str(tmp_path / "nope.json")])
        out = capsys.readouterr().out
        assert rc == 1
        assert "not found" in out

    def test_validate_stdin(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "stdin", __import__("io").StringIO('{"a": 1}'))
        rc = jsonwiz_main.main(["validate", "-"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "[OK]" in out

    def test_pretty(self, tmp_path, capsys):
        f = _write(tmp_path, "x.json", '{"a":1}')
        rc = jsonwiz_main.main(["pretty", f])
        out = capsys.readouterr().out
        assert rc == 0
        assert '"a": 1' in out

    def test_compact(self, tmp_path, capsys):
        f = _write(tmp_path, "x.json", '{"a": 1}')
        rc = jsonwiz_main.main(["compact", f])
        out = capsys.readouterr().out
        assert rc == 0
        assert out.strip() == '{"a":1}'

    def test_inspect(self, tmp_path, capsys):
        f = _write(tmp_path, "x.json", '{"a": [1,2]}')
        rc = jsonwiz_main.main(["inspect", f])
        out = capsys.readouterr().out
        assert rc == 0
        assert "_list_len" in out

    def test_keys(self, tmp_path, capsys):
        f = _write(tmp_path, "x.json", '{"a": 1, "b": 2}')
        rc = jsonwiz_main.main(["keys", f])
        out = capsys.readouterr().out
        assert rc == 0
        assert out.strip().splitlines() == ["a", "b"]

    def test_get_valid_path(self, tmp_path, capsys):
        f = _write(tmp_path, "x.json", '{"a": {"b": 5}}')
        rc = jsonwiz_main.main(["get", f, "a.b"])
        out = capsys.readouterr().out
        assert rc == 0
        assert out.strip() == "5"

    def test_get_missing_path(self, tmp_path, capsys):
        f = _write(tmp_path, "x.json", '{"a": 1}')
        rc = jsonwiz_main.main(["get", f, "z"])
        out = capsys.readouterr().out
        assert rc == 1
        assert "path not found" in out

    def test_get_no_path_arg(self, tmp_path, capsys):
        f = _write(tmp_path, "x.json", '{"a": 1}')
        rc = jsonwiz_main.main(["get", f])
        assert rc == 2

    def test_stats(self, tmp_path, capsys):
        f = _write(tmp_path, "x.json", '{"a": 1}')
        rc = jsonwiz_main.main(["stats", f])
        out = capsys.readouterr().out
        assert rc == 0
        assert "root_type" in out

    def test_diff_files(self, tmp_path, capsys):
        a = _write(tmp_path, "a.json", '{"v": 1}')
        b = _write(tmp_path, "b.json", '{"v": 2}')
        rc = jsonwiz_main.main(["diff", a, b])
        out = capsys.readouterr().out
        assert rc == 1
        assert "[DIFF]" in out

    def test_diff_identical(self, tmp_path, capsys):
        a = _write(tmp_path, "a.json", '{"v": 1}')
        b = _write(tmp_path, "b.json", '{"v": 1}')
        rc = jsonwiz_main.main(["diff", a, b])
        out = capsys.readouterr().out
        assert rc == 0
        assert "[OK]" in out

    def test_merge(self, tmp_path, capsys):
        a = _write(tmp_path, "a.json", '{"v": 1}')
        b = _write(tmp_path, "b.json", '{"v": 2}')
        rc = jsonwiz_main.main(["merge", a, b])
        out = capsys.readouterr().out
        assert rc == 0
        assert '"v": 2' in out

    def test_unknown_command(self, capsys):
        rc = jsonwiz_main.main(["bogus"])
        out = capsys.readouterr().out
        assert rc == 2
        assert "out of scope" in out

    def test_diff_requires_two_files(self, tmp_path, capsys):
        a = _write(tmp_path, "a.json", '{"v": 1}')
        rc = jsonwiz_main.main(["diff", a])
        assert rc == 2

    def test_validate_no_file_arg(self, capsys):
        rc = jsonwiz_main.main(["validate"])
        assert rc == 2
