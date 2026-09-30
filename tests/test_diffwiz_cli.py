import sys
from pathlib import Path
from unittest.mock import patch
import pytest

# Ensure repository root / src is on path for pytest discovery
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Adjust fallback if modules are located inside a subpackage (e.g., src.diffwiz or wizard_central.diffwiz)
try:
    from diffwiz.cli import main
except ModuleNotFoundError:
    try:
        from wizard_central.diffwiz.cli import main
    except ModuleNotFoundError:
        from src.diffwiz.cli import main


def test_diffwiz_cli_help(capsys):
    """Test that diffwiz CLI prints help output when requested."""
    with patch.object(sys, "argv", ["diffwiz", "--help"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert "usage:" in captured.out.lower() or "help" in captured.out.lower()


def test_diffwiz_cli_no_args(capsys):
    """Test behavior when no arguments are passed."""
    with patch.object(sys, "argv", ["diffwiz"]):
        try:
            main()
        except SystemExit as e:
            assert e.code in (0, 2)
