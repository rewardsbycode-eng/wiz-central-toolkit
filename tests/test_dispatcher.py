import json

from wiz_central_toolkit.wiz import __main__ as dispatcher


def test_version(capsys):
    result = dispatcher.main(["--version"])

    captured = capsys.readouterr()

    assert result == 0
    assert captured.out.startswith("wiz ")


def test_help(capsys):
    result = dispatcher.main(["--help"])

    captured = capsys.readouterr()

    assert result == 0
    assert "usage: wiz" in captured.out
    assert "available tools:" in captured.out


def test_alias_dispatch(monkeypatch):
    received = {}

    def fake_tool(args):
        received["args"] = args
        return 0

    monkeypatch.setattr(
        dispatcher,
        "get_tool_main",
        lambda name: fake_tool if name == "rustwiz" else None,
    )

    result = dispatcher.main(["rust", "check", "."])

    assert result == 0
    assert received["args"] == ["check", "."]


def test_json_output(monkeypatch, capsys):
    def fake_tool(args):
        print("tool output")
        return 0

    monkeypatch.setattr(
        dispatcher,
        "get_tool_main",
        lambda name: fake_tool if name == "rustwiz" else None,
    )

    result = dispatcher.main(["--json", "rust", "check", "."])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert result == 0
    assert payload["tool"] == "rustwiz"
    assert payload["args"] == ["check", "."]
    assert payload["exit_code"] == 0
    assert payload["stdout"] == "tool output\n"


def test_unknown_tool(capsys):
    result = dispatcher.main(["does-not-exist"])

    captured = capsys.readouterr()

    assert result == 2
    assert "unknown tool" in captured.err
