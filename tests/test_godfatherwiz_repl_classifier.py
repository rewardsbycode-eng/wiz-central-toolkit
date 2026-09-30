"""Tests for _classify_repl_input function in cli.py."""
import sys
from pathlib import Path

from wiz_central_toolkit.godfatherwiz.lib.cli import _classify_repl_input

def test_empty_input():
    assert _classify_repl_input("") == ("empty", [])
    assert _classify_repl_input("   \n\t") == ("empty", [])

def test_quit_and_exit():
    assert _classify_repl_input("/quit") == ("quit", [])
    assert _classify_repl_input("/exit") == ("quit", [])

def test_help_command():
    assert _classify_repl_input("/help") == ("help", [])

def test_voices_command():
    assert _classify_repl_input("/voices") == ("voices", [])

def test_model_command():
    assert _classify_repl_input("/model") == ("model", [])

def test_more_commands():
    assert _classify_repl_input("/more-commands") == ("more-commands", [])

def test_valid_wiz_command():
    result = _classify_repl_input("/wiz read-wizard --file foo.py")
    assert result == ("wiz", ["read-wizard", "--file", "foo.py"])

def test_unknown_slash_command():
    assert _classify_repl_input("/unknown_cmd arg1") == (
        "slash",
        ["/unknown_cmd", "arg1"],
    )

def test_chat_input():
    assert _classify_repl_input("Hello, oracle!") == ("chat", ["Hello, oracle!"])
