import pytest

from wiz_central_toolkit.debugwiz import debug_wizard


@pytest.fixture(autouse=True)
def isolate_debugwiz_ignore_file(monkeypatch, tmp_path):
    monkeypatch.setattr(
        debug_wizard,
        "IGNORE_LIST",
        tmp_path / "ignored.json",
    )
