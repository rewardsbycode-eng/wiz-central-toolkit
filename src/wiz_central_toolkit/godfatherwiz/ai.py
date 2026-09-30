"""Optional AI providers for Godfatherwiz.

AI is disabled by default. Requests are made only when ask() is called with
a configured provider.
"""

import json
import os
from urllib.request import Request, urlopen


class AIProviderError(RuntimeError):
    """Raised when AI is disabled or a provider request fails."""


def provider_name() -> str:
    """Return the configured provider name, defaulting to disabled."""
    return os.environ.get("WIZ_AI_PROVIDER", "none").strip().lower() or "none"


def provider_config() -> dict:
    """Return the active provider configuration from environment variables."""
    provider = provider_name()
    defaults = {
        "ollama": "http://localhost:11434",
        "openai": "https://api.openai.com/v1",
        "openai-compatible": "https://api.example.com/v1",
        "anthropic": "https://api.anthropic.com/v1",
    }
    return {
        "provider": provider,
        "model": os.environ.get("WIZ_AI_MODEL", ""),
        "base_url": os.environ.get("WIZ_AI_BASE_URL", defaults.get(provider, "")),
        "api_key": (
            os.environ.get("WIZ_AI_API_KEY")
            or os.environ.get("OPENAI_API_KEY", "")
            if provider in ("openai", "openai-compatible")
            else os.environ.get("WIZ_AI_API_KEY")
            or os.environ.get("ANTHROPIC_API_KEY", "")
            if provider == "anthropic"
            else ""
        ),
    }


def status_text() -> str:
    """Describe AI availability without exposing credentials."""
    provider = provider_name()
    if provider == "none":
        return (
            "AI provider: none\n"
            "Deterministic tool routing is available.\n"
            "Set WIZ_AI_PROVIDER to enable optional AI."
        )
    config = provider_config()
    return (
        f"AI provider: {provider}\n"
        f"AI model: {config['model'] or '(default)'}\n"
        f"AI endpoint: {config['base_url']}"
    )


def _post_json(url: str, payload: dict, headers: dict) -> dict:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    try:
        with urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise AIProviderError(f"AI provider request failed: {exc}") from exc


def ask(prompt: str) -> str:
    """Send a prompt to the configured provider and return its response."""
    config = provider_config()
    provider = config["provider"]
    if provider == "none":
        raise AIProviderError("No AI provider configured")
    if provider not in ("ollama", "openai", "openai-compatible", "anthropic"):
        raise AIProviderError(f"Unsupported AI provider: {provider}")

    model = config["model"]
    base_url = config["base_url"].rstrip("/")

    if provider == "ollama":
        data = _post_json(
            f"{base_url}/api/chat",
            {
                "model": model or "llama3.2",
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
            },
            {},
        )
        try:
            return data["message"]["content"]
        except (KeyError, TypeError) as exc:
            raise AIProviderError("Unexpected Ollama response") from exc

    api_key = config["api_key"]
    if not api_key:
        raise AIProviderError(f"No API key configured for {provider}")

    if provider == "anthropic":
        data = _post_json(
            f"{base_url}/messages",
            {
                "model": model or "claude-3-5-sonnet-latest",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": prompt}],
            },
            {"x-api-key": api_key, "anthropic-version": "2023-06-01"},
        )
        try:
            return "".join(
                item["text"] for item in data["content"] if item.get("type") == "text"
            )
        except (KeyError, TypeError) as exc:
            raise AIProviderError("Unexpected Anthropic response") from exc

    data = _post_json(
        f"{base_url}/chat/completions",
        {
            "model": model or "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
        },
        {"Authorization": f"Bearer {api_key}"},
    )
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise AIProviderError("Unexpected OpenAI-compatible response") from exc
