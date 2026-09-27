"""Optional AI provider support for godfatherwiz.

The core toolkit does not require an AI provider. Supported modes:
- none
- ollama
- openai-compatible
"""

from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class AIProviderError(RuntimeError):
    """Raised when an optional AI provider cannot be used."""


def provider_name() -> str:
    return os.getenv("WIZ_AI_PROVIDER", "none").strip().lower()


def provider_config() -> dict[str, str]:
    provider = provider_name()

    if provider == "ollama":
        return {
            "provider": provider,
            "model": os.getenv("WIZ_AI_MODEL", "llama3.2"),
            "base_url": os.getenv(
                "WIZ_AI_BASE_URL",
                "http://localhost:11434",
            ).rstrip("/"),
        }

    if provider in {"openai", "openai-compatible"}:
        return {
            "provider": "openai-compatible",
            "model": os.getenv("WIZ_AI_MODEL", ""),
            "base_url": os.getenv(
                "WIZ_AI_BASE_URL",
                "https://api.openai.com/v1",
            ).rstrip("/"),
            "api_key": os.getenv("WIZ_AI_API_KEY", ""),
        }

    return {
        "provider": "none",
        "model": "",
        "base_url": "",
    }


def status_text() -> str:
    config = provider_config()
    provider = config["provider"]

    if provider == "none":
        return (
            "AI provider: none\n"
            "Deterministic tool routing is available.\n"
            "Set WIZ_AI_PROVIDER to enable optional AI."
        )

    lines = [
        f"AI provider: {provider}",
        f"AI model: {config.get('model') or '(not configured)'}",
        f"AI endpoint: {config.get('base_url') or '(not configured)'}",
    ]

    if provider == "openai-compatible":
        lines.append(
            "API key: configured"
            if config.get("api_key")
            else "API key: missing"
        )

    return "\n".join(lines)


def ask(prompt: str) -> str:
    config = provider_config()
    provider = config["provider"]

    if provider == "none":
        raise AIProviderError(
            "No AI provider configured. "
            "Use a deterministic tool command or configure Ollama/API access."
        )

    if not prompt.strip():
        raise AIProviderError("AI prompt is required")

    if not config.get("model"):
        raise AIProviderError("WIZ_AI_MODEL is required")

    if provider == "ollama":
        payload = {
            "model": config["model"],
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }
        url = f"{config['base_url']}/api/chat"
        headers = {"Content-Type": "application/json"}

    elif provider == "openai-compatible":
        if not config.get("api_key"):
            raise AIProviderError(
                "WIZ_AI_API_KEY is required for an OpenAI-compatible provider"
            )

        payload = {
            "model": config["model"],
            "messages": [{"role": "user", "content": prompt}],
        }
        url = f"{config['base_url']}/chat/completions"
        headers = {
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json",
        }

    else:
        raise AIProviderError(f"unsupported AI provider: {provider}")

    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urlopen(request, timeout=120) as response:
            body = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise AIProviderError(
            f"AI provider returned HTTP {exc.code}: {detail}"
        ) from exc
    except URLError as exc:
        raise AIProviderError(
            f"could not connect to AI provider: {exc.reason}"
        ) from exc
    except TimeoutError as exc:
        raise AIProviderError("AI provider request timed out") from exc
    except json.JSONDecodeError as exc:
        raise AIProviderError("AI provider returned invalid JSON") from exc

    if provider == "ollama":
        content = body.get("message", {}).get("content", "")
    else:
        choices = body.get("choices", [])
        content = (
            choices[0].get("message", {}).get("content", "")
            if choices
            else ""
        )

    if not content:
        raise AIProviderError("AI provider returned no response text")

    return str(content).strip()
