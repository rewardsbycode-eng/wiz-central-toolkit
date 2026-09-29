"""bannerwiz — ASCII banner generator for Wizard Central Toolkit."""

from __future__ import annotations

import argparse
import shutil
import sys
from typing import Literal, cast

from pyfiglet import Figlet
from rich import box
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


STYLES = {
    "default": ("white", box.ROUNDED, "left"),
    "minimal": ("dim", box.MINIMAL, "left"),
    "clean": ("cyan", box.SQUARE, "left"),
    "boxed": ("yellow", box.DOUBLE, "left"),
    "heavy": ("red", box.HEAVY, "left"),
    "neon-blue": ("bright_blue", box.DOUBLE_EDGE, "center"),
    "neon-green": ("bright_green", box.DOUBLE_EDGE, "center"),
    "neon-pink": ("bright_magenta", box.DOUBLE_EDGE, "center"),
    "cyber": ("blue", box.ASCII_DOUBLE_HEAD, "center"),
    "matrix": ("green", box.MINIMAL_DOUBLE_HEAD, "left"),
    "elegant": ("magenta", box.ROUNDED, "center"),
    "royal": ("blue", box.DOUBLE, "center"),
    "retro": ("bright_yellow", box.ASCII, "center"),
    "arcade": ("bright_cyan", box.DOUBLE, "center"),
    "comic": ("bright_red", box.ROUNDED, "center"),
    "bare": ("white", None, "left"),
    "bare-center": ("cyan", None, "center"),
}


def terminal_width() -> int:
    return shutil.get_terminal_size((80, 24)).columns


def available_fonts() -> list[str]:
    return sorted(Figlet().getFonts())


def render_text(text: str, font: str, auto_fit: bool = True) -> tuple[str, str]:
    fonts = available_fonts()

    if font not in fonts:
        raise ValueError(
            f"font '{font}' was not found; use --fonts to list available fonts"
        )

    selected = font
    art = Figlet(font=selected).renderText(text)

    if auto_fit:
        usable = max(20, terminal_width() - 10)
        if max((len(line) for line in art.splitlines()), default=0) > usable:
            for candidate in (
                "small",
                "mini",
                "digital",
                "standard",
                "slant",
                "banner",
            ):
                if candidate not in fonts:
                    continue
                candidate_art = Figlet(font=candidate).renderText(text)
                if max(
                    (len(line) for line in candidate_art.splitlines()),
                    default=0,
                ) <= usable:
                    selected = candidate
                    art = candidate_art
                    break

    return art, selected


def display_banner(
    text: str,
    font: str = "standard",
    style: str = "clean",
    align: str | None = None,
    auto_fit: bool = True,
) -> int:
    if not text.strip():
        print("bannerwiz: text is required", file=sys.stderr)
        return 2

    try:
        art, selected_font = render_text(text, font, auto_fit)
    except ValueError as exc:
        print(f"bannerwiz: {exc}", file=sys.stderr)
        return 2

    color, border, preset_align = STYLES.get(style, (style, box.ROUNDED, "left"))

    selected_align = cast(Literal["left", "center", "right"], align or preset_align)
    rich_text = Text(art, style=color)
    aligned = Align(rich_text, align=selected_align)

    if border is None:
        console.print(aligned)
    else:
        console.print(
            Panel(
                aligned,
                title=f"{selected_font.upper()} . {style.upper()}",
                border_style=color,
                box=border,
                padding=(1, 2),
            )
        )

    return 0


def list_fonts() -> int:
    table = Table(
        title=f"Available ASCII Fonts ({len(available_fonts())})",
        box=box.DOUBLE,
    )
    table.add_column("ID", justify="right", style="dim")
    table.add_column("Font", style="yellow")

    for index, font in enumerate(available_fonts()):
        table.add_row(str(index), font)

    console.print(table)
    return 0


def list_styles() -> int:
    table = Table(title="Style Presets", box=box.DOUBLE)
    table.add_column("Style", style="yellow")
    table.add_column("Color")
    table.add_column("Align")

    for name, (color, border, align) in sorted(STYLES.items()):
        table.add_row(name, color, align)

    console.print(table)
    return 0


def compare_fonts(text: str) -> int:
    for font in ("standard", "slant", "big", "small", "digital", "banner"):
        if font in available_fonts():
            console.print(f"\n[bold cyan]{font}[/bold cyan]")
            art = Figlet(font=font).renderText(text)
            console.print(art)

    return 0


def demo() -> int:
    for text, font, style in (
        ("WELCOME", "standard", "clean"),
        ("BANNERWIZ", "slant", "neon-green"),
        ("TOOLKIT", "big", "royal"),
    ):
        result = display_banner(text, font, style)
        if result:
            return result
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bannerwiz",
        description="Render styled ASCII banners with FIGlet fonts.",
    )
    parser.add_argument(
        "text",
        nargs="*",
        help="text to render",
    )
    parser.add_argument(
        "-f",
        "--font",
        default="standard",
        help="FIGlet font name (default: standard)",
    )
    parser.add_argument(
        "-s",
        "--style",
        default="clean",
        help="style preset or Rich color (default: clean)",
    )
    parser.add_argument(
        "-a",
        "--align",
        choices=("left", "center", "right"),
        help="override style alignment",
    )
    parser.add_argument(
        "--no-auto-fit",
        action="store_true",
        help="do not automatically select a narrower font",
    )
    parser.add_argument(
        "--subtitle",
        help="print a subtitle below the banner",
    )
    parser.add_argument(
        "--fonts",
        action="store_true",
        help="list available FIGlet fonts",
    )
    parser.add_argument(
        "--styles",
        action="store_true",
        help="list style presets",
    )
    parser.add_argument(
        "--compare",
        metavar="TEXT",
        help="compare several fonts",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="show example banners",
    )
    parser.add_argument(
        "--sizes",
        action="store_true",
        help="show terminal sizing information",
    )
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.fonts:
        return list_fonts()

    if args.styles:
        return list_styles()

    if args.compare is not None:
        return compare_fonts(args.compare)

    if args.demo:
        return demo()

    if args.sizes:
        width = terminal_width()
        print(f"Terminal width: {width} columns")
        print(f"Usable width: {max(20, width - 10)} columns")
        return 0

    if not args.text:
        parser.print_help()
        return 0

    result = display_banner(
        " ".join(args.text),
        font=args.font,
        style=args.style,
        align=args.align,
        auto_fit=not args.no_auto_fit,
    )

    if result == 0 and args.subtitle:
        console.print(Text(args.subtitle, style="bold bright_yellow"))

    return result


if __name__ == "__main__":
    sys.exit(main())
