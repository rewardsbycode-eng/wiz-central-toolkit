"""godfatherwiz — interactive deterministic router with optional AI support."""

from __future__ import annotations

import shlex
import sys

from wiz_central_toolkit.godfatherwiz.ai import (
    AIProviderError,
    ask,
    status_text,
)
from wiz_central_toolkit.tools_registry import TOOLS, get_tool_main


def print_help() -> None:
    print("usage: wiz godfatherwiz")
    print()
    print("Interactive commands:")
    print("  <tool> [args...]       run a registered deterministic tool")
    print("  tools                  list registered tools")
    print("  ask <prompt>           ask the configured optional AI provider")
    print("  ai status              show AI provider configuration")
    print("  help                   show this help")
    print("  exit                   leave the REPL")
    print()
    print("AI is optional and disabled by default.")


def print_tools() -> None:
    print("available tools: " + ", ".join(sorted(TOOLS)))


def run_tool(tool_name: str, args: list[str]) -> None:
    tool_main = get_tool_main(tool_name)

    if tool_main is None:
        print(f"unknown tool: {tool_name!r}")
        print_tools()
        return

    try:
        result = tool_main(args)
        if isinstance(result, int) and result != 0:
            print(f"{tool_name} exited with status {result}")
    except SystemExit as exc:
        if exc.code not in (None, 0):
            print(f"{tool_name} exited with status {exc.code}")
    except Exception as exc:
        print(f"{tool_name}: {exc}", file=sys.stderr)


def handle_line(line: str) -> bool:
    try:
        parts = shlex.split(line)
    except ValueError as exc:
        print(f"input error: {exc}")
        return True

    if not parts:
        return True

    command, args = parts[0], parts[1:]

    if command in {"exit", "quit"}:
        return False

    if command in {"help", "-h", "--help"}:
        print_help()
        return True

    if command == "tools":
        print_tools()
        return True

    if command == "ask":
        prompt = " ".join(args).strip()
        if not prompt:
            print("usage: ask <prompt>")
            return True

        try:
            print(ask(prompt))
        except AIProviderError as exc:
            print(f"AI unavailable: {exc}")
        return True

    if command == "ai":
        if args == ["status"]:
            print(status_text())
        else:
            print("usage: ai status")
        return True

    run_tool(command, args)
    return True


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    if argv and argv[0] in {"-h", "--help", "help"}:
        print_help()
        return 0

    print("godfatherwiz — interactive toolkit REPL")
    print("Type 'help' for commands or 'exit' to quit.")
    print_tools()

    while True:
        try:
            line = input("godfather> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        if not handle_line(line):
            return 0


if __name__ == "__main__":
    raise SystemExit(main())
