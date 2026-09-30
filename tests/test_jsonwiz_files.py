"""Tests for jsonwiz."""
import json
import sys
from io import StringIO
from unittest.mock import patch


def test_jsonwiz_help():
    """Test jsonwiz --help displays usage."""
    from wiz_central_toolkit.jsonwiz.lib.cli import main
    
    with patch('sys.stdout', new=StringIO()) as fake_out:
        ret = main(["--help"])
        assert ret == 0


def test_jsonwiz_validate_valid(sample_json):
    """Test jsonwiz validates valid JSON."""
    from wiz_central_toolkit.jsonwiz.lib.cli import main
    
    with patch('sys.stdout', new=StringIO()):
        ret = main(["validate", sample_json])
        assert ret == 0


def test_jsonwiz_validate_invalid(tmp_path):
    """Test jsonwiz rejects invalid JSON."""
    from wiz_central_toolkit.jsonwiz.lib.cli import main
    
    invalid_json = tmp_path / "invalid.json"
    invalid_json.write_text("{broken json}")
    
    with patch('sys.stdout', new=StringIO()):
        ret = main(["validate", str(invalid_json)])
        assert ret != 0


def test_jsonwiz_inspect(sample_json):
    """Test jsonwiz inspects JSON structure."""
    from wiz_central_toolkit.jsonwiz.lib.cli import main
    
    with patch('sys.stdout', new=StringIO()) as fake_out:
        ret = main(["inspect", sample_json])
        assert ret == 0
        output = fake_out.getvalue()
        assert "key" in output
