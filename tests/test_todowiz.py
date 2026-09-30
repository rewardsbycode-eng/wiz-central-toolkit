"""Tests for todowiz — ported from wizard_central's todo-wizard. Uses an isolated bank dir."""
import pytest

from wiz_central_toolkit.todowiz.lib.todo_wizard import TodoWizard


@pytest.fixture
def wiz(tmp_path):
    return TodoWizard(project_dir=str(tmp_path), bank=tmp_path / "bank")


class TestAddListComplete:
    def test_add_creates_item(self, wiz):
        item = wiz.add("buy milk")
        assert item["text"] == "buy milk"
        assert item["done"] is False
        assert item["id"] == 1

    def test_add_increments_id(self, wiz):
        wiz.add("first")
        second = wiz.add("second")
        assert second["id"] == 2

    def test_list_returns_all(self, wiz):
        wiz.add("a")
        wiz.add("b")
        assert len(wiz.list_todos()) == 2

    def test_list_pending_only(self, wiz):
        a = wiz.add("a")
        wiz.add("b")
        wiz.complete(a["id"])
        pending = wiz.list_todos(pending_only=True)
        assert len(pending) == 1
        assert pending[0]["text"] == "b"

    def test_complete_marks_done(self, wiz):
        item = wiz.add("task")
        ok = wiz.complete(item["id"])
        assert ok is True
        assert wiz.list_todos()[0]["done"] is True

    def test_complete_nonexistent_fails(self, wiz):
        assert wiz.complete(999) is False

    def test_complete_already_done_fails(self, wiz):
        item = wiz.add("task")
        wiz.complete(item["id"])
        assert wiz.complete(item["id"]) is False


class TestUndoNote:
    def test_undo_reopens(self, wiz):
        item = wiz.add("task")
        wiz.complete(item["id"])
        ok = wiz.undo_complete(item["id"])
        assert ok is True
        assert wiz.list_todos()[0]["done"] is False

    def test_undo_on_pending_fails(self, wiz):
        item = wiz.add("task")
        assert wiz.undo_complete(item["id"]) is False

    def test_note_appends(self, wiz):
        item = wiz.add("task")
        ok = wiz.note(item["id"], "made progress")
        assert ok is True
        assert wiz.list_todos()[0]["notes"][0]["text"] == "made progress"

    def test_note_on_missing_fails(self, wiz):
        assert wiz.note(999, "x") is False


class TestOldestOverdue:
    def test_oldest_empty(self, wiz):
        assert wiz.oldest() is None

    def test_oldest_returns_earliest(self, wiz):
        wiz.add("first")
        wiz.add("second")
        oldest = wiz.oldest()
        assert oldest["text"] == "first"

    def test_overdue_empty_when_recent(self, wiz):
        wiz.add("fresh task")
        assert wiz.overdue(days=7) == []

    def test_overdue_zero_days_flags_everything(self, wiz):
        wiz.add("task")
        results = wiz.overdue(days=0)
        assert len(results) == 1


class TestArchiveRemove:
    def test_archive_done_moves_completed(self, wiz):
        item = wiz.add("task")
        wiz.complete(item["id"])
        moved = wiz.archive_done()
        assert moved == 1
        assert wiz.list_todos() == []

    def test_archive_done_none_pending(self, wiz):
        wiz.add("task")
        assert wiz.archive_done() == 0

    def test_remove_deletes(self, wiz):
        item = wiz.add("task")
        ok = wiz.remove(item["id"])
        assert ok is True
        assert wiz.list_todos() == []

    def test_remove_nonexistent_fails(self, wiz):
        assert wiz.remove(999) is False


class TestStats:
    def test_stats_counts(self, wiz):
        a = wiz.add("a")
        wiz.add("b")
        wiz.complete(a["id"])
        s = wiz.stats()
        assert s == {"total": 2, "done": 1, "pending": 1}


# ---------- CLI dispatch tests ----------

from wiz_central_toolkit.todowiz import __main__ as todowiz_main


@pytest.fixture
def cli_env(tmp_path, monkeypatch):
    """Isolate the CLI's TodoWizard() constructor to a tmp project+bank."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(todowiz_main.TodoWizard, "BANK", tmp_path / "bank")
    return tmp_path


class TestCLI:
    def test_help_no_args(self, capsys):
        rc = todowiz_main.main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "usage: todowiz" in out

    def test_add_and_list(self, cli_env, capsys):
        rc = todowiz_main.main(["add", "buy", "milk"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "[+] #1 buy milk" in out

        rc = todowiz_main.main(["list"])
        out = capsys.readouterr().out
        assert "buy milk" in out

    def test_done_and_fail(self, cli_env, capsys):
        todowiz_main.main(["add", "task"])
        capsys.readouterr()
        rc = todowiz_main.main(["done", "1"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "[OK] completed" in out

        rc = todowiz_main.main(["done", "999"])
        out = capsys.readouterr().out
        assert rc == 1
        assert "[FAIL]" in out

    def test_undo(self, cli_env, capsys):
        todowiz_main.main(["add", "task"])
        todowiz_main.main(["done", "1"])
        capsys.readouterr()
        rc = todowiz_main.main(["undo", "1"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "[OK] reopened" in out

    def test_note(self, cli_env, capsys):
        todowiz_main.main(["add", "task"])
        capsys.readouterr()
        rc = todowiz_main.main(["note", "1", "making", "progress"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "[OK] noted" in out

    def test_note_requires_args(self, cli_env, capsys):
        rc = todowiz_main.main(["note", "1"])
        assert rc == 2

    def test_oldest_empty(self, cli_env, capsys):
        rc = todowiz_main.main(["oldest"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "no pending tasks" in out

    def test_overdue(self, cli_env, capsys):
        todowiz_main.main(["add", "task"])
        capsys.readouterr()
        rc = todowiz_main.main(["overdue", "0"])
        out = capsys.readouterr().out
        assert rc == 1
        assert "days old" in out

    def test_archive_done(self, cli_env, capsys):
        todowiz_main.main(["add", "task"])
        todowiz_main.main(["done", "1"])
        capsys.readouterr()
        rc = todowiz_main.main(["archive-done"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "[OK] archived" in out

    def test_rm(self, cli_env, capsys):
        todowiz_main.main(["add", "task"])
        capsys.readouterr()
        rc = todowiz_main.main(["rm", "1"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "[OK] removed" in out

    def test_stats(self, cli_env, capsys):
        todowiz_main.main(["add", "task"])
        capsys.readouterr()
        rc = todowiz_main.main(["stats"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "total" in out

    def test_export(self, cli_env, capsys):
        todowiz_main.main(["add", "task"])
        capsys.readouterr()
        rc = todowiz_main.main(["export"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "task" in out

    def test_unknown_command(self, capsys):
        rc = todowiz_main.main(["bogus"])
        assert rc == 2
