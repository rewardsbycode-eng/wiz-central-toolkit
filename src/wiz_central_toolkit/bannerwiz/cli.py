import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))


def _render_dependencies():
    from rich.console import Console
    from rich.text import Text
    from pyfiglet import figlet_format
    return Console(), Text, figlet_format

BANNER_FONT = "ansi_regular"

def render_sovereign(words, subtitle=None):
    """The Sovereign mural: stacked block words, purple crest / blue base per word."""
    console, Text, figlet_format = _render_dependencies()
    for word in words:
        lines = [l for l in figlet_format(word.upper(), font=BANNER_FONT, width=999).splitlines() if l.strip()]
        half = len(lines) // 2
        for i, line in enumerate(lines):
            color = "bright_magenta" if i < half else "bright_blue"
            console.print(Text(line.rstrip(), style=f"bold {color}"))
    if subtitle:
        console.print(Text(" ".join(subtitle.upper()), style="bold bright_yellow"))

def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in ("-h", "--help"):
        print("bannerwiz - ASCII banner wizard")
        print("usage: bannerwiz <words...> [--subtitle TEXT] | --demo | --themes | --styles | --interactive")
        return 0
    if not argv:
        print("bannerwiz - ASCII banner wizard")
        print("usage: bannerwiz <words...> [--subtitle TEXT] | --demo | --themes | --styles | --interactive")
        return 0
    if argv[0] in ("--demo", "--themes", "--styles", "--sizes", "--interactive", "--fonts"):
        import runpy
        import os
        eng = Path(__file__).resolve().parent / "lib" / "banner_wizard.py"
        os.environ["_BANNERWIZ_SUBCMD"] = argv[0]
        # delegate to the engine's mature surface
        sys.argv = [str(eng)] + argv
        runpy.run_path(str(eng), run_name="__main__")
        return 0
    subtitle = None
    if "--subtitle" in argv:
        i = argv.index("--subtitle")
        subtitle = argv[i + 1] if i + 1 < len(argv) else None
        argv = argv[:i] + ([] if subtitle is None else []) + argv[i + 2:]
    if not argv:
        print("out of scope - no words given")
        return 2
    render_sovereign(argv, subtitle=subtitle)
    return 0

if __name__ == "__main__":
    sys.exit(main())
