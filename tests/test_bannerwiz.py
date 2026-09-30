"""Tests for bannerwiz."""
import sys
from io import StringIO
from unittest.mock import patch


def test_bannerwiz_help():
    """Test bannerwiz --help displays usage."""
    from wiz_central_toolkit.bannerwiz.cli import main
    
    with patch('sys.stdout', new=StringIO()) as fake_out:
        ret = main(["--help"])
        assert ret == 0
        output = fake_out.getvalue()
        assert "bannerwiz" in output.lower() or "banner" in output.lower()


def test_bannerwiz_basic():
    """Test bannerwiz renders a simple banner."""
    from wiz_central_toolkit.bannerwiz.cli import main
    
    with patch('sys.stdout', new=StringIO()) as fake_out:
        ret = main(["HELLO"])
        assert ret == 0
        output = fake_out.getvalue()
        assert "\n" in output
        assert len(output.strip()) > 50


def test_bannerwiz_style():
    """Test bannerwiz with style option."""
    from wiz_central_toolkit.bannerwiz.cli import main
    
    with patch('sys.stdout', new=StringIO()) as fake_out:
        ret = main(["TEST", "--style", "minimal"])
        assert ret == 0


def test_bannerwiz_demo():
    """Test bannerwiz demo mode."""
    from wiz_central_toolkit.bannerwiz.cli import main
    
    with patch('sys.stdout', new=StringIO()) as fake_out:
        ret = main(["--demo"])
        assert ret == 0


def test_bannerwiz_fonts():
    """Test bannerwiz lists fonts."""
    from wiz_central_toolkit.bannerwiz.cli import main
    
    with patch('sys.stdout', new=StringIO()) as fake_out:
        ret = main(["--fonts"])
        assert ret == 0


def test_bannerwiz_styles():
    """Test bannerwiz lists styles."""
    from wiz_central_toolkit.bannerwiz.cli import main
    
    with patch('sys.stdout', new=StringIO()) as fake_out:
        ret = main(["--styles"])
        assert ret == 0
