"""codeguardwiz — Ollama-backed code audit and repair (consent-gated writes)."""
import sys

from .cli import main as _main


def main(argv=None) -> int:
    if argv is None:
        return _main()
    saved = sys.argv
    sys.argv = [saved[0] if saved else "codeguardwiz", *argv]
    try:
        return _main()
    finally:
        sys.argv = saved


if __name__ == "__main__":
    sys.exit(main())
