"""
Banner Wrapper — Drop-in utility for any Python project.
Place this file next to banner_engine.py, then:

    from banner_wrapper import banner, status, title

That's it. No modifications to banner_engine.py needed.
"""

import sys
import os

# Add banner_engine.py's directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from banner_engine import ASCIIBannerEngine, StyleManager
    from rich.console import Console
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Run: pip install pyfiglet rich")
    sys.exit(1)

_engine = ASCIIBannerEngine()
_console = Console()


def banner(text: str, font: str = "standard", style: str = "clean",
           auto_fit: bool = True, align: str | None = None) -> None:
    """Print a styled ASCII banner.

    Args:
        text:    Text to render
        font:    FIGlet font name (use 'fonts' command to list)
        style:   Style preset name or any Rich color
        auto_fit: Auto-select smaller font if banner overflows
        align:   Override alignment (left/center/right)
    """
    _engine.display_banner(text, font=font, style=style,
                          auto_fit=auto_fit, align=align)


def title(text: str) -> None:
    """Small, minimal section title."""
    _engine.display_banner(text, font="small", style="minimal",
                          auto_fit=True, align="left")


def subtitle(text: str) -> None:
    """Prints plain text subtitle (no ASCII art)."""
    _console.print(f"\n[bold dim]── {text} ──[/bold dim]")


def success(text: str = "SUCCESS") -> None:
    """Green neon success banner."""
    _engine.display_banner(text, font="standard", style="neon-green",
                          auto_fit=True, align="center")


def error(text: str = "ERROR") -> None:
    """Red heavy error banner."""
    _engine.display_banner(text, font="standard", style="heavy",
                          auto_fit=True, align="left")


def warning(text: str = "WARNING") -> None:
    """Yellow comic warning banner."""
    _engine.display_banner(text, font="standard", style="comic",
                          auto_fit=True, align="center")


def info(text: str = "INFO") -> None:
    """Blue clean info banner."""
    _engine.display_banner(text, font="standard", style="clean",
                          auto_fit=True, align="left")


def splash(app_name: str, version: str = "", style: str = "neon-blue",
           font: str = "big") -> None:
    """Full startup splash screen with app name + version.

    Example:
        splash("MY APP", "v1.0")
    """
    _engine.display_banner(app_name, font=font, style=style,
                          auto_fit=True, align="center")
    if version:
        _console.print(f"[dim]  {version}[/dim]")
    _console.print(f"[dim]  {_engine.sizer.report()}[/dim]")
    _console.print(f"[dim]  {len(_engine.FONTS)} fonts available[/dim]\n")


def separator(char: str = "─", width: int | None = None) -> None:
    """Print a horizontal separator line."""
    w = width or _engine.sizer.usable_width
    _console.print(f"[dim]{char * w}[/dim]")


def list_styles() -> None:
    """Show all available style presets."""
    StyleManager.list_presets_table()


def list_fonts() -> None:
    """Show all available fonts."""
    _engine.list_fonts()


def generate_raw(text: str, font: str = "standard",
                 auto_fit: bool = False) -> str | None:
    """Return raw ASCII art string (no console output).

    Useful for embedding in logs, files, or other displays.

    Example:
        art = generate_raw("HELLO", "big")
        with open("logo.txt", "w") as f:
            f.write(art)
    """
    return _engine.generate(text, font=font, auto_fit=auto_fit)


def export_all(text: str, output_dir: str = "./banner_output") -> None:
    """Export text rendered in every available font."""
    _engine.render_all_fonts(text, output_dir)


def compare_fonts(text: str) -> None:
    """Side-by-side font comparison."""
    _engine.compare_fonts(text)


def compare_styles(text: str) -> None:
    """Side-by-side style comparison."""
    _engine.compare_styles(text)


def report() -> str:
    """Return terminal/engine size info string."""
    return _engine.sizer.report()


# ── CLI mode ──────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Banner Wrapper — Quick banner utilities")
    parser.add_argument("text", nargs="?", default="HELLO",
                       help="Text to render")
    parser.add_argument("-f", "--font", default="standard",
                       help="FIGlet font name")
    parser.add_argument("-s", "--style", default="clean",
                       help="Style preset or Rich color")
    parser.add_argument("-a", "--align", default=None,
                       choices=["left", "center", "right"],
                       help="Alignment override")
    parser.add_argument("--splash", metavar="VERSION",
                       help="Show splash screen with version")
    parser.add_argument("--success", action="store_true",
                       help="Print success banner")
    parser.add_argument("--error", action="store_true",
                       help="Print error banner")
    parser.add_argument("--warning", action="store_true",
                       help="Print warning banner")
    parser.add_argument("--info", action="store_true",
                       help="Print info banner")
    parser.add_argument("--separator", action="store_true",
                       help="Print separator line")
    parser.add_argument("--list-styles", action="store_true",
                       help="List style presets")
    parser.add_argument("--list-fonts", action="store_true",
                       help="List fonts")
    parser.add_argument("--report", action="store_true",
                       help="Show terminal info")

    args = parser.parse_args()

    if args.splash is not None:
        splash(args.text, args.splash)
    elif args.success:
        success(args.text)
    elif args.error:
        error(args.text)
    elif args.warning:
        warning(args.text)
    elif args.info:
        info(args.text)
    elif args.separator:
        separator()
    elif args.list_styles:
        list_styles()
    elif args.list_fonts:
        list_fonts()
    elif args.report:
        print(report())
    else:
        banner(args.text, font=args.font, style=args.style, align=args.align)
