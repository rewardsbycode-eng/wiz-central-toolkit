"""Tests for the jsonwiz command-line interface."""

import sys
from unittest.mock import patch

from wiz_central_toolkit.jsonwiz.cli import main


def test_jsonwiz_cli_help(capsys):
    with patch.object(sys, "argv", ["jsonwiz", "--help"]):
        result = main()

    captured = capsys.readouterr()
    assert result == 0
    assert "usage:" in captured.out.lower()


def test_jsonwiz_cli_validate_valid_json(tmp_path, capsys):
    json_file = tmp_path / "valid.json"
    json_file.write_text('{"status": "ok", "count": 1}')

    with patch.object(sys, "argv", ["jsonwiz", "validate", str(json_file)]):
        result = main()

    captured = capsys.readouterr()
    assert result == 0
    assert "valid json" in captured.out.lower()


def test_jsonwiz_cli_validate_invalid_json(tmp_path, capsys):
    json_file = tmp_path / "invalid.json"
    json_file.write_text('{"status": "ok",')

    with patch.object(sys, "argv", ["jsonwiz", "validate", str(json_file)]):
        result = main()

    captured = capsys.readouterr()
    assert result == 1
    assert "invalid json" in captured.out.lower()


def test_jsonwiz_cli_validate_missing_file(capsys):
    with patch.object(sys, "argv", ["jsonwiz", "validate", "/no/such/file.json"]):
        result = main()

    captured = capsys.readouterr()
    assert result == 1
    assert "file not found" in captured.out.lower()
