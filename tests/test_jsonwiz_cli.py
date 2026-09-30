import json
import sys
from pathlib import Path
from unittest.mock import patch, mock_open
import pytest

# Ensure repository root / src is on path for pytest discovery
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from jsonwiz.cli import main
except ModuleNotFoundError:
    try:
        from wizard_central.jsonwiz.cli import main
    except ModuleNotFoundError:
        from src.jsonwiz.cli import main


def test_jsonwiz_cli_help(capsys):
    """Test jsonwiz help flag."""
    with patch.object(sys, "argv", ["jsonwiz", "--help"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0


def test_jsonwiz_cli_validate_valid_json(capsys):
    """Test jsonwiz with valid JSON payload/file."""
    valid_json = '{"status": "ok", "count": 1}'

    with patch.object(sys, "argv", ["jsonwiz", "dummy.json"]), \
         patch("builtins.open", mock_open(read_data=valid_json)), \
         patch("pathlib.Path.exists", return_value=True):
        try:
            main()
        except SystemExit as e:
            assert e.code == 0


def test_jsonwiz_cli_invalid_json(capsys):
    """Test jsonwiz graceful handling of invalid JSON input."""
    invalid_json = '{"status": "ok",'

    with patch.object(sys, "argv", ["jsonwiz", "invalid.json"]), \
         patch("builtins.open", mock_open(read_data=invalid_json)), \
         patch("pathlib.Path.exists", return_value=True):
        try:
            main()
        except SystemExit as e:
            assert e.code != 0
