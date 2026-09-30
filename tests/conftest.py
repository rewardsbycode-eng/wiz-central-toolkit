import pytest

from wiz_central_toolkit.debugwiz import debug_wizard


@pytest.fixture(autouse=True)
def isolate_debugwiz_ignore_file(monkeypatch, tmp_path):
    monkeypatch.setattr(
        debug_wizard,
        "IGNORE_LIST",
        tmp_path / "ignored.json",
    )


@pytest.fixture(autouse=True)
def _no_ollama(monkeypatch):
    monkeypatch.setattr(
        "wiz_central_toolkit.godfatherwiz.lib.godfather_wizard._ollama_chat_api",
        lambda *a, **k: "stub reply",
    )


@pytest.fixture
def sample_json(tmp_path):
    """Path (str) to a small valid JSON file."""
    p = tmp_path / "sample.json"
    p.write_text('{"key": "value"}')
    return str(p)
