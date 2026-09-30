import sys
from pathlib import Path
from unittest.mock import patch
import pytest

# Ensure repository root / src is on path for pytest discovery
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from wiz_central_toolkit.todowiz.cli import main


def test_todowiz_cli_help(capsys):
    """Test todowiz help message output."""
    with patch.object(sys, "argv", ["todowiz", "--help"]):
        assert main() == 0
        assert "usage: todowiz" in capsys.readouterr().out


def test_todowiz_cli_list_tasks(capsys):
    """Test listing tasks via todowiz CLI."""
    with patch.object(sys, "argv", ["todowiz", "list"]):
        try:
            main()
        except SystemExit as e:
            assert e.code == 0


def test_todowiz_cli_add_task():
    """Test adding a task via todowiz CLI."""
    with patch.object(sys, "argv", ["todowiz", "add", "Test todo item"]):
        try:
            main()
        except SystemExit as e:
            assert e.code == 0
