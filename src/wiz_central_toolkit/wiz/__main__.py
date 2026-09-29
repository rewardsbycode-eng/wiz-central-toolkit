"""Top-level dispatcher for Wizard Central Toolkit."""

from __future__ import annotations

import contextlib
import importlib.metadata
import io
import json
import sys

from wiz_central_toolkit.tools_registry import TOOLS, get_tool_main

ALIASES = {
    "banner": "bannerwiz",
    "codeguard": "codeguardwiz",
    "debug": "debugwiz",
    "diff": "diffwiz",
    "json": "jsonwiz",
    "python": "pythonwiz",
    "read": "readwiz",
    "rust": "rustwiz",
    "tmux": "tmuxwiz",
    "todo": "todowiz",
    "write": "writewiz",
}


def package_version() -> str:
    try:
        return importlib.metadata.version("wiz-central-toolkit")
    except importlib.metadata.PackageNotFoundError:
        return "0.1.0"


def print_help() -> None:
    print("usage: wiz [--json] <tool> [args...]")
    print()
    print("options:")
    print("  -h, --help       show this help message")
    print("  --version        show the installed version")
    print("  --json           emit command output as JSON")
    print()
    print("available tools: " + ", ".join(sorted(TOOLS)))
    print()
    print("aliases:")
    for alias, tool in sorted(ALIASES.items()):
        print(f"  {alias:<12} {tool}")


def normalize_tool_name(name: str) -> str:
    return ALIASES.get(name, name)


def run_json(tool_name: str, tool_args: list[str], tool_main) -> int:
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()

    try:
        with (
            contextlib.redirect_stdout(stdout_buffer),
            contextlib.redirect_stderr(stderr_buffer),
        ):
            result = tool_main(tool_args)

        exit_code = result if isinstance(result, int) else 0
    except SystemExit as exc:
        exit_code = exc.code if isinstance(exc.code, int) else 1
    except Exception as exc:
        exit_code = 1
        stderr_buffer.write(f"{type(exc).__name__}: {exc}")

    payload = {
        "tool": tool_name,
        "args": tool_args,
        "exit_code": exit_code,
        "stdout": stdout_buffer.getvalue(),
        "stderr": stderr_buffer.getvalue(),
    }

    print(json.dumps(payload, indent=2))
    return exit_code


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    if not argv or argv[0] in {"-h", "--help", "help"}:
        print_help()
        return 0

    if argv[0] in {"--version", "-V"}:
        print(f"wiz {package_version()}")
        return 0

    json_mode = "--json" in argv
    if json_mode:
        argv = [argument for argument in argv if argument != "--json"]

    if not argv:
        print_help()
        return 0

    requested_name, tool_args = argv[0], argv[1:]
    tool_name = normalize_tool_name(requested_name)
    tool_main = get_tool_main(tool_name)

    if tool_main is None:
        print(f"unknown tool: {requested_name!r}", file=sys.stderr)
        print("available tools: " + ", ".join(sorted(TOOLS)), file=sys.stderr)
        return 2

    if json_mode:
        return run_json(tool_name, tool_args, tool_main)

    result = tool_main(tool_args)
    return result if isinstance(result, int) else 0


if __name__ == "__main__":
    raise SystemExit(main())
