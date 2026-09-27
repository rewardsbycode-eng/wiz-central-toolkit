import shlex
from wiz_central_toolkit.tools_registry import TOOLS, get_tool_main

def main(argv=None) -> int:
    print("godfatherwiz — interactive REPL. Type a tool name + args, or 'exit'.")
    print("available tools: " + ", ".join(sorted(TOOLS)))
    while True:
        try:
            line = input("godfather> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not line:
            continue
        if line in ("exit", "quit"):
            return 0
        parts = shlex.split(line)
        tool_name, rest = parts[0], parts[1:]
        tool_main = get_tool_main(tool_name)
        if tool_main is None:
            print(f"unknown tool: {tool_name!r}")
            continue
        tool_main(rest)

if __name__ == "__main__":
    raise SystemExit(main())
