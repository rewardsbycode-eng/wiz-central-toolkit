"""Tests for pythonwiz syntax checker."""

from wiz_central_toolkit.pythonwiz.__main__ import check_directory, check_file


class TestCheckFile:
    def test_valid_syntax(self, tmp_path):
        test_file = tmp_path / "valid.py"
        test_file.write_text("def hello():\n    pass\n")
        verdict, reason = check_file(str(test_file))
        assert verdict == "OK"
        assert "valid syntax" in reason
    
    def test_invalid_syntax(self, tmp_path):
        test_file = tmp_path / "invalid.py"
        test_file.write_text("def broken(:")
        verdict, reason = check_file(str(test_file))
        assert verdict == "FAIL"
        assert "SyntaxError" in reason or ":" in reason
    
    def test_file_not_found(self):
        verdict, reason = check_file("/nonexistent/path/file.py")
        assert verdict == "FAIL"
        assert "not found" in reason
    
    def test_wrong_extension(self, tmp_path):
        test_file = tmp_path / "notpython.txt"
        test_file.write_text("x = 1")
        verdict, reason = check_file(str(test_file))
        assert verdict == "FAIL"
        assert "not a .py file" in reason


class TestCheckDirectory:
    def test_empty_directory(self, tmp_path):
        result = check_directory(str(tmp_path))
        assert result["status"] == "OK"
        assert result["count"] == 0
    
    def test_all_valid(self, tmp_path):
        (tmp_path / "a.py").write_text("x = 1\n")
        (tmp_path / "b.py").write_text("y = 2\n")
        result = check_directory(str(tmp_path))
        assert result["status"] == "OK"
        assert result["passed"] == 2
        assert result["failed"] == 0
    
    def test_mixed_results(self, tmp_path):
        (tmp_path / "good.py").write_text("z = 3\n")
        (tmp_path / "bad.py").write_text("broken(:")
        result = check_directory(str(tmp_path))
        assert result["status"] == "FAIL"
        assert result["passed"] == 1
        assert result["failed"] == 1
    def test_subdirectory_scan(self, tmp_path):
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (tmp_path / "top.py").write_text("x = 1\n")
        (subdir / "nested.py").write_text("y = 2\n")
        result = check_directory(str(tmp_path))
        assert result["total"] == 2
        assert result["passed"] == 2
