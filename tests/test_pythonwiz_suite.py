"""The full pythonwiz analysis suite is reachable through the registered entry point."""
import sys

from wiz_central_toolkit.pythonwiz.__main__ import main


def _write(tmp_path, source):
    f = tmp_path / "m.py"
    f.write_text(source)
    return f


def test_outline_lists_symbols(tmp_path, capsys):
    f = _write(tmp_path, "def alpha():\n    return 1\n\nclass Beta:\n    pass\n")
    assert main(["outline", str(f)]) == 0
    out = capsys.readouterr().out
    assert "alpha" in out and "Beta" in out


def test_secrets_flags_hardcoded_password(tmp_path):
    assert main(["secrets", str(_write(tmp_path, 'password = "hunter22"\n'))]) == 1


def test_secrets_clean_file(tmp_path):
    assert main(["secrets", str(_write(tmp_path, "x = 1\n"))]) == 0


def test_todos_marker_found(tmp_path):
    assert main(["todos", str(_write(tmp_path, "# TODO: fix this\nx = 1\n"))]) == 1


def test_sys_argv_is_restored(tmp_path):
    f = _write(tmp_path, "x = 1\n")
    before = list(sys.argv)
    main(["outline", str(f)])
    assert sys.argv == before
