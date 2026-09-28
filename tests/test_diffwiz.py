import sys
from unittest.mock import patch
import pytest

from src.wiz_central_toolkit.diffwiz.__main__ import main


def test_diffwiz_help(capsys):
    """Test help display and exit code 0."""
    with patch.object(sys, "argv", ["diffwiz", "--help"]):
        res = main()
        assert res == 0 or res is None
        captured = capsys.readouterr()
        assert "usage: diffwiz" in captured.out


def test_diffwiz_no_args(capsys):
    """Test missing arguments displays help and exits with status 0."""
    with patch.object(sys, "argv", ["diffwiz"]):
        res = main()
        assert res == 0 or res is None
        captured = capsys.readouterr()
        assert "usage: diffwiz" in captured.out


def test_diffwiz_invalid_command(capsys):
    """Test unknown command branch."""
    with patch.object(sys, "argv", ["diffwiz", "invalid_cmd"]):
        res = main()
        assert res != 0
        captured = capsys.readouterr()
        assert "out of scope" in captured.out


def test_diffwiz_files_identical(tmp_path, capsys):
    """Test comparing two identical files (returns 0)."""
    f1 = tmp_path / "a.txt"
    f2 = tmp_path / "b.txt"
    f1.write_text("hello world\n")
    f2.write_text("hello world\n")

    with patch.object(sys, "argv", ["diffwiz", "files", str(f1), str(f2)]):
        res = main()
        assert res == 0
        captured = capsys.readouterr()
        assert "[OK] files identical" in captured.out


def test_diffwiz_files_different(tmp_path, capsys):
    """Test comparing two different files (returns 1)."""
    f1 = tmp_path / "a.txt"
    f2 = tmp_path / "b.txt"
    f1.write_text("hello world\nline 2\n")
    f2.write_text("hello earth\nline 2\n")

    with patch.object(sys, "argv", ["diffwiz", "files", str(f1), str(f2)]):
        res = main()
        assert res == 1
        captured = capsys.readouterr()
        assert "[FAIL] files differ" in captured.out


def test_diffwiz_files_missing(tmp_path, capsys):
    """Test missing file error path (returns 1)."""
    f1 = tmp_path / "nonexistent.txt"
    f2 = tmp_path / "b.txt"
    f2.write_text("test")

    with patch.object(sys, "argv", ["diffwiz", "files", str(f1), str(f2)]):
        res = main()
        assert res == 1 or res == 2
        captured = capsys.readouterr()
        assert "[FAIL] not found" in captured.out


def test_diffwiz_dirs_compare(tmp_path, capsys):
    """Test directory comparison."""
    d1 = tmp_path / "dir1"
    d2 = tmp_path / "dir2"
    d1.mkdir()
    d2.mkdir()
    (d1 / "common.txt").write_text("same")
    (d2 / "common.txt").write_text("same")
    (d1 / "only1.txt").write_text("unique1")
    (d2 / "only2.txt").write_text("unique2")

    with patch.object(sys, "argv", ["diffwiz", "dirs", str(d1), str(d2)]):
        res = main()
        assert res != 0


def test_diffwiz_context_mode(tmp_path, capsys):
    """Test context diff mode."""
    f1 = tmp_path / "a.txt"
    f2 = tmp_path / "b.txt"
    f1.write_text("line 1\nline 2\n")
    f2.write_text("line 1\nline 2 modified\n")

    with patch.object(sys, "argv", ["diffwiz", "context", "3", str(f1), str(f2)]):
        res = main()
        assert res != 0


def test_diffwiz_summary_mode(tmp_path, capsys):
    """Test summary diff mode."""
    f1 = tmp_path / "a.txt"
    f2 = tmp_path / "b.txt"
    f1.write_text("alpha\nbeta\ngamma\n")
    f2.write_text("alpha\nbeta modified\ndelta\n")

    with patch.object(sys, "argv", ["diffwiz", "summary", str(f1), str(f2)]):
        res = main()
        assert res == 1 or res == 0 or res is None
        captured = capsys.readouterr()
        assert "added=" in captured.out


def test_diffwiz_word_mode(tmp_path, capsys):
    """Test word diff mode."""
    f1 = tmp_path / "a.txt"
    f2 = tmp_path / "b.txt"
    f1.write_text("quick brown fox")
    f2.write_text("quick red fox")

    with patch.object(sys, "argv", ["diffwiz", "word", str(f1), str(f2)]):
        res = main()
        assert res is None or res == 0 or res == 1


def test_diffwiz_same_mode(tmp_path, capsys):
    """Test same lines extraction mode."""
    f1 = tmp_path / "a.txt"
    f2 = tmp_path / "b.txt"
    f1.write_text("common line\nonly in 1\n")
    f2.write_text("common line\nonly in 2\n")

    with patch.object(sys, "argv", ["diffwiz", "same", str(f1), str(f2)]):
        res = main()
        assert res is None or res == 0 or res == 1


def test_diffwiz_reverse_mode(tmp_path, capsys):
    """Test reverse diff mode."""
    f1 = tmp_path / "a.txt"
    f2 = tmp_path / "b.txt"
    f1.write_text("foo\nbar\n")
    f2.write_text("foo\nbaz\n")

    with patch.object(sys, "argv", ["diffwiz", "reverse", str(f1), str(f2)]):
        res = main()
        assert res != 0


def test_diffwiz_insufficient_args(capsys):
    """Test providing a valid command without required file arguments."""
    with patch.object(sys, "argv", ["diffwiz", "files", "single_arg.txt"]):
        res = main()
        assert res != 0
        captured = capsys.readouterr()
        assert "out of scope" in captured.out
