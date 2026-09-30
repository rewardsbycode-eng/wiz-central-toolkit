import sys
from unittest.mock import patch

from wiz_central_toolkit.godfatherwiz import __main__ as godfatherwiz_main
from wiz_central_toolkit.godfatherwiz import ai as godfather_ai


def test_godfatherwiz_main_execution_with_mocked_ai(monkeypatch, capsys):
    """Test godfatherwiz CLI execution with dynamic patching based on available module attributes."""
    monkeypatch.setattr(sys, "argv", ["godfatherwiz"])

    # Provide mock stdin inputs to satisfy input() calls and cleanly terminate the REPL loop
    input_responses = iter(["give me advice", "/quit"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(input_responses))

    # Determine what functions/classes exist on godfather_ai to patch appropriately
    patched = False

    # Case 1: Check for known top-level functions on godfather_ai
    for target_func in ["ask", "ask_ai", "ask_godfather", "query", "run", "chat"]:
        if hasattr(godfather_ai, target_func):
            with patch.object(godfather_ai, target_func, return_value="Mocked AI response"):
                godfatherwiz_main.main()
            patched = True
            break

    # Case 2: Fallback if no specific target function was found/patched
    if not patched:
        godfatherwiz_main.main()

    captured = capsys.readouterr()
    assert "stub reply" in captured.out

from types import SimpleNamespace
from unittest.mock import Mock

from wiz_central_toolkit.rustwiz import __main__ as rust_main
from wiz_central_toolkit.rustwiz import rust_wizard as rust_module


def test_rustwiz_check_directory_with_valid_and_invalid_files(tmp_path, monkeypatch, capsys):
    """Cover directory scanning and both rustc success/failure paths."""
    source_dir = tmp_path / "rust_project"
    source_dir.mkdir()

    good_file = source_dir / "good.rs"
    bad_file = source_dir / "bad.rs"
    good_file.write_text("fn good() {}")
    bad_file.write_text("this is invalid rust")

    results = [
        SimpleNamespace(returncode=0, stderr=""),
        SimpleNamespace(
            returncode=1,
            stderr="error: expected item\nerror: invalid syntax",
        ),
    ]

    mock_run = Mock(side_effect=results)
    monkeypatch.setattr(rust_module.subprocess, "run", mock_run)

    result = rust_module.RustWizard().check([str(source_dir)])

    assert result == 1
    assert mock_run.call_count == 2

    output = capsys.readouterr().out
    assert "[OK]" in output
    assert "[FAIL]" in output
    assert "1/2 valid, 1 invalid" in output


def test_rustwiz_check_single_rs_file(tmp_path, monkeypatch, capsys):
    """Cover checking one explicit .rs file."""
    source_file = tmp_path / "main.rs"
    source_file.write_text("fn main() {}")

    monkeypatch.setattr(
        rust_module.subprocess,
        "run",
        Mock(return_value=SimpleNamespace(returncode=0, stderr="")),
    )

    result = rust_module.RustWizard().check([str(source_file)])

    assert result == 0
    assert "[OK]" in capsys.readouterr().out


def test_rustwiz_check_empty_directory(tmp_path, capsys):
    """Cover the no-Rust-files-found path."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    result = rust_module.RustWizard().check([str(empty_dir)])

    assert result == 1
    assert "[FAIL] no .rs files found" in capsys.readouterr().out


def test_rustwiz_build_success(tmp_path, monkeypatch, capsys):
    """Cover a successful cargo check."""
    crate_dir = tmp_path / "crate"
    crate_dir.mkdir()
    (crate_dir / "Cargo.toml").write_text("[package]\nname = 'demo'\nversion = '0.1.0'\n")

    mock_run = Mock(
        return_value=SimpleNamespace(returncode=0, stderr="")
    )
    monkeypatch.setattr(rust_module.subprocess, "run", mock_run)

    result = rust_module.RustWizard().build(str(crate_dir))

    assert result == 0
    assert "cargo check passed" in capsys.readouterr().out
    mock_run.assert_called_once()


def test_rustwiz_build_failure(tmp_path, monkeypatch, capsys):
    """Cover a failed cargo check and error output."""
    crate_dir = tmp_path / "crate"
    crate_dir.mkdir()
    (crate_dir / "Cargo.toml").write_text("[package]\nname = 'demo'\nversion = '0.1.0'\n")

    mock_run = Mock(
        return_value=SimpleNamespace(
            returncode=1,
            stderr="error: could not compile demo\nanother error",
        )
    )
    monkeypatch.setattr(rust_module.subprocess, "run", mock_run)

    result = rust_module.RustWizard().build(str(crate_dir))

    assert result == 1

    output = capsys.readouterr().out
    assert "cargo check failed" in output
    assert "could not compile demo" in output


def test_rustwiz_main_no_arguments(capsys):
    """Cover the CLI usage message when no arguments are supplied."""
    result = rust_main.main([])

    assert result == 2
    assert "usage:" in capsys.readouterr().out


def test_rustwiz_main_check(monkeypatch, tmp_path):
    """Cover the CLI check command."""
    monkeypatch.setattr(
        rust_main.RustWizard,
        "check",
        lambda self, args: 7,
    )

    src = tmp_path / "example.rs"
    src.write_text("fn main() {}\n")
    result = rust_main.main(["check", str(src)])

    assert result == 7


def test_rustwiz_main_build(monkeypatch, tmp_path):
    """Cover the CLI build command."""
    monkeypatch.setattr(
        rust_main.RustWizard,
        "build",
        lambda self, crate_dir: 8,
    )

    crate = tmp_path / "my-crate"
    crate.mkdir()
    (crate / "Cargo.toml").write_text("[package]\nname = \"x\"\n")
    result = rust_main.main(["build", str(crate)])

    assert result == 8

