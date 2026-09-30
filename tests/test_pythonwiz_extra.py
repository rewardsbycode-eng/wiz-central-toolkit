"""Extra PythonWizard coverage (restores cases lost in the test rewrite)."""
import sys

import pytest

from wiz_central_toolkit.pythonwiz.lib.python_wizard import PythonWizard


@pytest.fixture
def wiz():
    return PythonWizard()


def _write(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text)
    return p


def test_check_file_missing_returns_failure(wiz, tmp_path):
    r = wiz.check_file(tmp_path / "nope.py")
    assert r["valid"] is False
    assert r["error"] == "file not found"


def test_check_file_invalid_reports_line(wiz, tmp_path):
    r = wiz.check_file(_write(tmp_path, "bad.py", "def broken(:\n"))
    assert r["valid"] is False
    assert r["line"] == 1
    assert r["error"]


def test_check_dir_recurses_and_skips_ignored_dirs(wiz, tmp_path):
    _write(tmp_path, "top.py", "x = 1\n")
    sub = tmp_path / "sub"
    sub.mkdir()
    _write(sub, "nested.py", "y = 2\n")
    cache = tmp_path / "__pycache__"
    cache.mkdir()
    _write(cache, "junk.py", "broken(:\n")
    results = wiz.check_dir(tmp_path)
    assert len(results) == 2
    assert all(r["valid"] for r in results)


def test_check_entry_missing(wiz, tmp_path):
    assert wiz.check_entry(tmp_path / "nope.py")["error"] == "file not found"


def test_check_entry_no_shebang(wiz, tmp_path):
    assert wiz.check_entry(_write(tmp_path, "a.py", "x = 1\n"))["error"] == "no shebang line"
    assert wiz.check_entry(_write(tmp_path, "empty.py", ""))["error"] == "no shebang line"


def test_check_entry_bad_interpreter(wiz, tmp_path):
    r = wiz.check_entry(_write(tmp_path, "a.py", "#!/nonexistent/python\n"))
    assert r["valid"] is False
    assert r["error"].startswith("interpreter missing")


def test_check_entry_valid(wiz, tmp_path):
    r = wiz.check_entry(_write(tmp_path, "a.py", "#!" + sys.executable + "\n"))
    assert r["valid"] is True
    assert r["interpreter"] == sys.executable


def test_outline(wiz, tmp_path):
    p = _write(tmp_path, "m.py", "class A:\n    def m(self):\n        pass\n\ndef f():\n    pass\n")
    assert wiz.outline(p) == [("class", "A", 1), ("def", "A.m", 2), ("def", "f", 5)]


def test_imports_of(wiz, tmp_path):
    _write(tmp_path, "helper.py", "")
    p = _write(tmp_path, "mod.py",
               "import os\nimport requests\nimport helper\n"
               "from . import x\nfrom .pkg import y\nfrom collections import OrderedDict\n")
    r = wiz.imports_of(p)
    assert r["stdlib"] == ["collections", "os"]
    assert r["third_party"] == ["requests"]
    assert r["local"] == ["helper"]
    assert r["relative"] == [".", ".pkg"]


def test_todos_of(wiz, tmp_path):
    p = _write(tmp_path, "t.py", "x = 1  # TODO: fix this\n# fixme later\ny = 2\n")
    assert wiz.todos_of(p) == [(1, "TODO", "fix this"), (2, "FIXME", "later")]


def test_secrets_scan(wiz, tmp_path):
    p = _write(tmp_path, "s.py", 'password = "hunter2xyz"\nx = 1\n')
    assert wiz.secrets_scan(p) == [(1, 'password = "hunter2xyz"')]


def test_bare_excepts(wiz, tmp_path):
    p = _write(tmp_path, "e.py", "try:\n    pass\nexcept:\n    pass\n")
    assert wiz.bare_excepts(p) == [(3, "bare", True)]


def test_health_score_clean_file(wiz, tmp_path):
    p = _write(tmp_path, "h.py", 'def f():\n    """Doc."""\n    return 1\n')
    assert wiz.health_score(p)["score"] == 100


def test_health_score_penalizes_missing_docstring(wiz, tmp_path):
    p = _write(tmp_path, "h.py", "def f():\n    return 1\n")
    r = wiz.health_score(p)
    assert r["docstrings_missing"] == 1
    assert r["score"] == 95


def test_health_score_invalid_file(wiz, tmp_path):
    r = wiz.health_score(_write(tmp_path, "h.py", "def broken(:\n"))
    assert r["score"] == 0


def test_loc_stats(wiz, tmp_path):
    p = _write(tmp_path, "l.py", "# c\n\nx = 1\n")
    r = wiz.loc_stats(p)
    assert (r["lines"], r["code"], r["blank"], r["comment"]) == (3, 1, 1, 1)
    assert r["functions"] == 0 and r["classes"] == 0


def test_main_guard(wiz, tmp_path):
    assert wiz.main_guard(_write(tmp_path, "a.py", "if __name__ == '__main__':\n    pass\n"))["has_main_guard"] is True
    assert wiz.main_guard(_write(tmp_path, "b.py", "x = 1\n"))["has_main_guard"] is False
