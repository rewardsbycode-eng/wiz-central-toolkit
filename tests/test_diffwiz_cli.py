"""Tests for the diffwiz command-line interface."""

import sys
from unittest.mock import patch

from wiz_central_toolkit.diffwiz.cli import main


def test_diffwiz_cli_help(capsys):
    """Help should print usage information and return success."""
    with patch.object(sys, "argv", ["diffwiz", "--help"]):
        result = main()

    captured = capsys.readouterr()
    assert result == 0
    assert "usage:" in captured.out.lower()
    assert "diffwiz" in captured.out.lower()


def test_diffwiz_cli_no_args(capsys):
    """No arguments should show help and return success."""
    with patch.object(sys, "argv", ["diffwiz"]):
        result = main()

    captured = capsys.readouterr()
    assert result == 0
    assert "usage:" in captured.out.lower()


def test_diffwiz_cli_unknown_command(capsys):
    """Unknown commands should report out of scope and return code 2."""
    with patch.object(sys, "argv", ["diffwiz", "unknown-command"]):
        result = main()

    captured = capsys.readouterr()
    assert result == 2
    assert "out of scope" in captured.out.lower()
