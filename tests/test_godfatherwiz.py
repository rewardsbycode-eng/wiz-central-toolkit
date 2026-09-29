from unittest.mock import MagicMock, patch

import pytest

from wiz_central_toolkit.godfatherwiz.ai import (
    AIProviderError,
    ask,
    provider_config,
    provider_name,
    status_text,
)


def test_godfatherwiz_provider_defaults(monkeypatch):
    monkeypatch.delenv("WIZ_AI_PROVIDER", raising=False)
    assert isinstance(provider_name(), str)
    assert isinstance(provider_config(), dict)


def test_godfatherwiz_status():
    status = status_text()
    assert isinstance(status, str)


def test_godfatherwiz_ask_none(monkeypatch):
    monkeypatch.setenv("WIZ_AI_PROVIDER", "none")
    with pytest.raises(AIProviderError, match="No AI provider configured"):
        ask("Hello")


@patch("wiz_central_toolkit.godfatherwiz.ai.urlopen")
def test_godfatherwiz_ask_ollama_mocked(mock_urlopen, monkeypatch):
    monkeypatch.setenv("WIZ_AI_PROVIDER", "ollama")
    monkeypatch.setenv("WIZ_AI_MODEL", "qwen2.5-coder")

    mock_response = MagicMock()
    mock_response.read.return_value = b'{"message": {"content": "Hello from mock AI"}}'
    mock_response.__enter__.return_value = mock_response
    mock_urlopen.return_value = mock_response

    response = ask("Hello")
    assert response == "Hello from mock AI"
