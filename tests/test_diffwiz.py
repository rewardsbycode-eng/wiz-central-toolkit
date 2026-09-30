"""Tests for diffwiz."""

from wiz_central_toolkit.diffwiz.lib.cli import main
from wiz_central_toolkit.diffwiz.lib.diff_wizard import DiffWizard


def test_help_and_no_args(capsys):
    assert main(["--help"]) == 0
    assert "usage: diffwiz" in capsys.readouterr().out

    assert main([]) == 0
    assert "usage: diffwiz" in capsys.readouterr().out


def test_files_same_and_different(tmp_path, capsys):
    a, b = tmp_path / "a.txt", tmp_path / "b.txt"
    a.write_text("same\n")
    b.write_text("same\n")

    assert main(["files", str(a), str(b)]) == 0
    assert "files identical" in capsys.readouterr().out

    b.write_text("changed\n")
    assert main(["files", str(a), str(b)]) == 1
    assert "[FAIL] files differ" in capsys.readouterr().out


def test_files_bad_args_and_missing_file(tmp_path, capsys):
    assert main(["files"]) == 2
    assert "out of scope" in capsys.readouterr().out

    existing = tmp_path / "exists.txt"
    existing.write_text("content")
    missing = tmp_path / "missing.txt"

    assert main(["files", str(existing), str(missing)]) == 1
    assert "not found" in capsys.readouterr().out


def test_dirs_identical_and_different(tmp_path, capsys):
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()
    (a / "same.txt").write_text("same")
    (b / "same.txt").write_text("same")

    assert main(["dirs", str(a), str(b)]) == 0
    assert "trees identical" in capsys.readouterr().out

    (a / "only-a.txt").write_text("a")
    (b / "only-b.txt").write_text("b")
    (b / "same.txt").write_text("changed")

    assert main(["dirs", str(a), str(b)]) == 1
    output = capsys.readouterr().out
    assert "only in" in output
    assert "differing: same.txt" in output
    assert "differences" in output


def test_dirs_bad_args_and_non_directories(tmp_path, capsys):
    assert main(["dirs"]) == 2
    assert "out of scope" in capsys.readouterr().out

    file_path = tmp_path / "file.txt"
    file_path.write_text("content")

    assert main(["dirs", str(file_path), str(tmp_path)]) == 1
    assert "not a directory" in capsys.readouterr().out


def test_context_command(tmp_path, capsys):
    a, b = tmp_path / "a.txt", tmp_path / "b.txt"
    a.write_text("before\nold\n")
    b.write_text("before\nnew\n")

    assert main(["context", "1", str(a), str(b)]) == 1
    output = capsys.readouterr().out
    assert "-old" in output
    assert "+new" in output

    assert main(["context", "1", str(a), str(a)]) == 0
    assert "files identical" in capsys.readouterr().out


def test_context_bad_args_and_missing_file(tmp_path, capsys):
    assert main(["context"]) == 2
    assert "context requires" in capsys.readouterr().out

    existing = tmp_path / "existing.txt"
    existing.write_text("content")
    missing = tmp_path / "missing.txt"

    assert main(["context", "2", str(existing), str(missing)]) == 1
    assert "not found" in capsys.readouterr().out


def test_context_invalid_number(tmp_path):
    file_path = tmp_path / "file.txt"
    file_path.write_text("content")

    try:
        main(["context", "not-a-number", str(file_path), str(file_path)])
    except ValueError:
        pass
    else:
        raise AssertionError("Expected invalid context value to raise ValueError")


def test_summary_file_and_directory_commands(tmp_path, capsys):
    a, b = tmp_path / "a.txt", tmp_path / "b.txt"
    a.write_text("old\\n")
    b.write_text("new\\n")

    assert main(["summary", str(a), str(b)]) == 1
    assert "added=" in capsys.readouterr().out

    assert main(["summary", str(a), str(a)]) == 0
    assert "identical" in capsys.readouterr().out

    da, db = tmp_path / "da", tmp_path / "db"
    da.mkdir()
    db.mkdir()
    (da / "old.txt").write_text("old")
    (db / "new.txt").write_text("new")

    assert main(["summary", str(da), str(db)]) == 1
    assert "not a file" in capsys.readouterr().out


def test_summary_bad_args_and_missing_file(tmp_path, capsys):
    assert main(["summary"]) == 2
    assert "out of scope" in capsys.readouterr().out

    existing = tmp_path / "existing.txt"
    existing.write_text("content")
    missing = tmp_path / "missing.txt"

    assert main(["summary", str(existing), str(missing)]) == 1
    assert "not found" in capsys.readouterr().out


def test_word_command(tmp_path, capsys):
    a, b = tmp_path / "a.txt", tmp_path / "b.txt"
    a.write_text("one two")
    b.write_text("one three")

    assert main(["word", str(a), str(b)]) == 0
    output = capsys.readouterr().out
    assert "<del>two</del>" in output
    assert "<ins>three</ins>" in output


def test_word_bad_args_and_missing_file(tmp_path, capsys):
    assert main(["word"]) == 2
    assert "out of scope" in capsys.readouterr().out

    existing = tmp_path / "existing.txt"
    existing.write_text("content")
    missing = tmp_path / "missing.txt"

    assert main(["word", str(existing), str(missing)]) == 1
    assert "not found" in capsys.readouterr().out


def test_same_command(tmp_path, capsys):
    a, b = tmp_path / "a.txt", tmp_path / "b.txt"
    a.write_text("same")
    b.write_text("same")

    assert main(["same", str(a), str(b)]) == 0
    assert capsys.readouterr().out == ""

    b.write_text("different")
    assert main(["same", str(a), str(b)]) == 1

    assert main(["same"]) == 2
    assert "out of scope" in capsys.readouterr().out


def test_same_missing_file(tmp_path, capsys):
    existing = tmp_path / "existing.txt"
    existing.write_text("content")
    missing = tmp_path / "missing.txt"

    assert main(["same", str(existing), str(missing)]) == 1
    assert "not found" in capsys.readouterr().out


def test_reverse_command(tmp_path, capsys):
    a, b = tmp_path / "a.txt", tmp_path / "b.txt"
    a.write_text("first\n")
    b.write_text("second\n")

    assert main(["reverse", str(a), str(b)]) == 1
    output = capsys.readouterr().out
    assert "-second" in output
    assert "+first" in output

    assert main(["reverse", str(a), str(a)]) == 0
    assert "files identical" in capsys.readouterr().out


def test_reverse_bad_args_and_missing_file(tmp_path, capsys):
    assert main(["reverse"]) == 2
    assert "out of scope" in capsys.readouterr().out

    existing = tmp_path / "existing.txt"
    existing.write_text("content")
    missing = tmp_path / "missing.txt"

    assert main(["reverse", str(existing), str(missing)]) == 1
    assert "not found" in capsys.readouterr().out


def test_unknown_command(capsys):
    assert main(["unknown"]) == 2
    assert "out of scope" in capsys.readouterr().out


def test_diffwizard_file_methods(tmp_path):
    wiz = DiffWizard()
    a, b = tmp_path / "a.txt", tmp_path / "b.txt"
    a.write_text("alpha\nold\n")
    b.write_text("alpha\nnew\n")

    diff = wiz.diff_files(a, b)
    assert isinstance(diff, str)
    assert "-old" in diff
    assert "+new" in diff

    context_diff = wiz.diff_files_context(a, b, context=1)
    assert isinstance(context_diff, str)
    assert "-old" in context_diff
    assert "+new" in context_diff

    assert wiz.files_identical(a, b) is False

    reverse_diff = wiz.diff_files_reverse(a, b)
    assert isinstance(reverse_diff, str)
    assert "-new" in reverse_diff
    assert "+old" in reverse_diff

    b.write_text(a.read_text())
    assert wiz.diff_files(a, b) == ""
    assert wiz.diff_files_context(a, b) == ""
    assert wiz.files_identical(a, b) is True
    assert wiz.diff_files_reverse(a, b) == ""


def test_diffwizard_directory_methods_and_skipped_dirs(tmp_path):
    wiz = DiffWizard()
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()

    (a / "only-a.txt").write_text("a")
    (b / "only-b.txt").write_text("b")
    (a / "changed.txt").write_text("old")
    (b / "changed.txt").write_text("new")

    (a / ".git").mkdir()
    (a / ".git" / "ignored.txt").write_text("ignored")
    (b / "node_modules").mkdir()
    (b / "node_modules" / "ignored.txt").write_text("ignored")

    assert wiz.diff_dirs(a, b) == {
        "only_a": ["only-a.txt"],
        "only_b": ["only-b.txt"],
        "differing": ["changed.txt"],
    }

    assert wiz.diff_summary(a, b) == {
        "identical": False,
        "added_lines": 2,
        "removed_lines": 2,
        "hunks": 3,
    }

    empty_a, empty_b = tmp_path / "empty-a", tmp_path / "empty-b"
    empty_a.mkdir()
    empty_b.mkdir()
    assert wiz.diff_summary(empty_a, empty_b) == {"identical": True}


def test_diffwizard_file_summary(tmp_path):
    wiz = DiffWizard()
    a, b = tmp_path / "a.txt", tmp_path / "b.txt"
    a.write_text("old\nkeep\n")
    b.write_text("new\nkeep\nadded\n")

    result = wiz.diff_summary(a, b)
    assert result == {
        "identical": False,
        "added_lines": 2,
        "removed_lines": 1,
        "hunks": 1,
    }

    b.write_text(a.read_text())
    assert wiz.diff_summary(a, b) == {"identical": True}


def test_diffwizard_word_level_all_change_types(tmp_path):
    wiz = DiffWizard()
    a, b = tmp_path / "a.txt", tmp_path / "b.txt"

    a.write_text("keep remove")
    b.write_text("keep insert")
    assert wiz.diff_word_level(a, b) == (
        "keep\n<del>remove</del><ins>insert</ins>"
    )

    a.write_text("remove")
    b.write_text("")
    assert wiz.diff_word_level(a, b) == "<del>remove</del>"

    a.write_text("")
    b.write_text("insert")
    assert wiz.diff_word_level(a, b) == "<ins>insert</ins>"

    a.write_text("same words")
    b.write_text("same words")
    assert wiz.diff_word_level(a, b) == "same words"


def test_diffwizard_word_level_delete_and_insert(tmp_path):
    wiz = DiffWizard()
    a, b = tmp_path / "a.txt", tmp_path / "b.txt"
    a.write_text("alpha beta")
    b.write_text("alpha")

    assert wiz.diff_word_level(a, b) == "alpha\n<del>beta</del>"

    a.write_text("alpha")
    b.write_text("alpha beta")

    assert wiz.diff_word_level(a, b) == "alpha\n<ins>beta</ins>"


def test_diffwizard_word_level_insert_after_equal(tmp_path):
    wiz = DiffWizard()
    a, b = tmp_path / "a.txt", tmp_path / "b.txt"
    a.write_text("alpha")
    b.write_text("alpha beta")

    assert wiz.diff_word_level(a, b) == "alpha\n<ins>beta</ins>"
