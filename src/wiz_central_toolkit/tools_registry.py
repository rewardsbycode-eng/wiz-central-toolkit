"""Shared tool registry — both `wiz` and `godfatherwiz` dispatch through this.
Add a new tool by adding one line here; nothing else needs to know about it."""
import importlib

TOOLS = {
    "bannerwiz": "wiz_central_toolkit.bannerwiz.__main__",
    "codeguardwiz": "wiz_central_toolkit.codeguardwiz.__main__",
    "debugwiz": "wiz_central_toolkit.debugwiz.__main__",
    "godfatherwiz": "wiz_central_toolkit.godfatherwiz.__main__",
    "diffwiz": "wiz_central_toolkit.diffwiz.__main__",
    "jsonwiz": "wiz_central_toolkit.jsonwiz.__main__",
    "pythonwiz": "wiz_central_toolkit.pythonwiz.__main__",
    "readwiz": "wiz_central_toolkit.readwiz.__main__",
    "rustwiz": "wiz_central_toolkit.rustwiz.__main__",
    "tmuxwiz": "wiz_central_toolkit.tmuxwiz.__main__",
    "todowiz": "wiz_central_toolkit.todowiz.__main__",
    "writewiz": "wiz_central_toolkit.writewiz.__main__",
}

def get_tool_main(name: str):
    """Import a tool's main() lazily by name. Returns None if unknown."""
    module_path = TOOLS.get(name)
    if module_path is None:
        return None
    module = importlib.import_module(module_path)
    return module.main
