import sys
from wiz_central_toolkit.tools_registry import TOOLS, get_tool_main

def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print("wiz — invoke any tool: wiz <tool> [args...]")
        print("available tools: " + ", ".join(sorted(TOOLS)))
        return 0
    tool_name, rest = argv[0], argv[1:]
    tool_main = get_tool_main(tool_name)
    if tool_main is None:
        print(f"unknown tool: {tool_name!r}")
        print("available tools: " + ", ".join(sorted(TOOLS)))
        return 2
    result = tool_main(rest)
    return result if isinstance(result, int) else 0

if __name__ == "__main__":
    raise SystemExit(main())
