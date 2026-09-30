from pathlib import Path

from wiz_central_toolkit.pythonwiz.lib.python_wizard import PythonWizard


def test_valid_syntax(tmp_path):
    path = tmp_path / "valid.py"
    path.write_text("def hello():\n    pass\n")
    assert PythonWizard().check_file(path)["valid"] is True


def test_invalid_syntax(tmp_path):
    path = tmp_path / "invalid.py"
    path.write_text("def broken(:")
    result = PythonWizard().check_file(path)
    assert result["valid"] is False
    assert result["error"]


def test_directory_scan(tmp_path):
    (tmp_path / "good.py").write_text("x = 1\n")
    (tmp_path / "bad.py").write_text("broken(:")
    results = PythonWizard().check_dir(tmp_path)
    assert len(results) == 2
    assert sum(result["valid"] for result in results) == 1
    assert sum(not result["valid"] for result in results) == 1


def test_empty_directory(tmp_path):
    assert PythonWizard().check_dir(tmp_path) == []
