import pytest
from wiz_central_toolkit.readwiz.read_wizard import check_command, _first_verb


def test_readwiz_first_verb():
    assert _first_verb("ls -la") == "ls"
    assert _first_verb("  git  status ") == "git"


def test_readwiz_check_command_allow():
    verdict, reason = check_command("ls -la")
    assert verdict == "ALLOW"
    assert "read-only" in reason.lower()


def test_readwiz_check_command_deny():
    verdict, reason = check_command("rm -rf /")
    assert verdict == "DENIED"
    assert "rm" in reason
