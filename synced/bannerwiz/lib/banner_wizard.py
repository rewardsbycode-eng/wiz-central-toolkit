from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.text import Text
from rich.align import Align
from pyfiglet import Figlet
import shutil
import os
import sys
import datetime

def log_error(message: str) -> None:
    """Append errors to debug.log with timestamp."""
    timestamp = datetime.datetime.now().isoformat()
    with open("debug.log", "a") as f:
        f.write(f"[{timestamp}] {message}\n")
console = Console()


# ═══════════════════════════════════════════════════════════════════════
#  SIZE MANAGER
# ═══════════════════════════════════════════════════════════════════════

class SizeManager:
    """
    Manages banner dimensions, terminal-fit logic, and scaling.
    """

    def __init__(self, max_width: int | None = None, min_width: int = 40):
        self._terminal_width = shutil.get_terminal_size((80, 24)).columns
        self.max_width = max_width or self._terminal_width
        self.min_width = min_width

    @property
    def terminal_width(self) -> int:
        return shutil.get_terminal_size((80, 24)).columns

    @property
    def usable_width(self) -> int:
        return max(self.min_width, self.terminal_width - 6)

    def refresh(self) -> None:
        self._terminal_width = self.terminal_width
        self.max_width = min(self.max_width, self.terminal_width)

    def measure_banner(self, ascii_art: str) -> int:
        if not ascii_art:
            return 0
        return max(len(line) for line in ascii_art.splitlines())

    def fits(self, ascii_art: str, margin: int = 0) -> bool:
        return self.measure_banner(ascii_art) <= (self.usable_width - margin)

    def auto_fit_font(self, text: str, preferred_font: str = "standard",
                      fallback_order: list[str] | None = None) -> str:
        if fallback_order is None:
            fallback_order = [
                preferred_font,
                "big", "standard", "slant", "small",
                "banner", "smkeyboard", "digital", "mini",
            ]
        seen = set()
        ordered = []
        for f in fallback_order:
            if f not in seen:
                ordered.append(f)
                seen.add(f)
        available = ASCIIBannerEngine.FONTS
        for font_key in ordered:
            if font_key not in available:
                continue
            fig = Figlet(font=available[font_key])
            art = fig.renderText(text)
            if self.fits(art):
                return font_key
        return ordered[-1] if ordered else "standard"

    def truncate_to_width(self, ascii_art: str, width: int | None = None) -> str:
        target = width or self.usable_width
        lines = ascii_art.splitlines()
        result = []
        for line in lines:
            if len(line) > target:
                result.append(line[:target - 1] + "\u2025")
            else:
                result.append(line)
        return "\n".join(result)

    def pad_banner(self, ascii_art: str, align: str = "left",
                   h_pad: int = 2, v_pad: int = 0) -> str:
        lines = ascii_art.splitlines()
        target_width = self.measure_banner(ascii_art) + (h_pad * 2)
        padded = []
        for _ in range(v_pad):
            padded.append("")
        for line in lines:
            stripped = line.rstrip()
            ln = len(stripped)
            if align == "center":
                left = (target_width - ln) // 2
                right = target_width - ln - left
                padded.append(" " * left + stripped + " " * right)
            elif align == "right":
                padded.append(" " * (target_width - ln) + stripped)
            else:
                padded.append(stripped + " " * (target_width - ln))
        for _ in range(v_pad):
            padded.append("")
        return "\n".join(padded)

    def report(self) -> str:
        return (
            f"Terminal: {self.terminal_width} cols | "
            f"Usable: {self.usable_width} cols | "
            f"Min: {self.min_width} | Max: {self.max_width}"
        )


# ═══════════════════════════════════════════════════════════════════════
#  STYLE MANAGER
# ═══════════════════════════════════════════════════════════════════════

class StyleManager:
    """
    Predefined style presets combining color, border style, alignment,
    and box characters.
    """

    PRESETS = {
        # ── Classic ──
        "default":     {"color": "white",          "border": box.ROUNDED,             "align": "left"},
        "minimal":     {"color": "dim",            "border": box.MINIMAL,             "align": "left"},
        "clean":       {"color": "cyan",           "border": box.SQUARE,              "align": "left"},
        "boxed":       {"color": "yellow",         "border": box.DOUBLE,              "align": "left"},
        "heavy":       {"color": "red",            "border": box.HEAVY,               "align": "left"},

        # ── Neon / Cyber ──
        "neon-blue":   {"color": "bright_blue",    "border": box.DOUBLE_EDGE,         "align": "center"},
        "neon-green":  {"color": "bright_green",   "border": box.DOUBLE_EDGE,         "align": "center"},
        "neon-pink":   {"color": "bright_magenta", "border": box.DOUBLE_EDGE,         "align": "center"},
        "cyber":       {"color": "blue",           "border": box.ASCII_DOUBLE_HEAD,   "align": "center"},
        "matrix":      {"color": "green",          "border": box.MINIMAL_DOUBLE_HEAD, "align": "left"},

        # ── Elegant ──
        "elegant":     {"color": "magenta",        "border": box.ROUNDED,             "align": "center"},
        "royal":       {"color": "blue",           "border": box.DOUBLE,              "align": "center"},
        "shadow":      {"color": "bright_black",   "border": box.SIMPLE_HEAD,         "align": "left"},

        # ── Playful ──
        "retro":       {"color": "bright_yellow",  "border": box.ASCII,               "align": "center"},
        "arcade":      {"color": "bright_cyan",    "border": box.DOUBLE,              "align": "center"},
        "comic":       {"color": "bright_red",     "border": box.ROUNDED,             "align": "center"},

        # ── Bare / No frame ──
        "bare":        {"color": "white",          "border": None,                    "align": "left"},
        "bare-center": {"color": "cyan",           "border": None,                    "align": "center"},
    }

    @classmethod
    def get(cls, name: str) -> dict:
        return cls.PRESETS.get(name, cls.PRESETS["default"])

    @classmethod
    def list_presets(cls) -> list[str]:
        return sorted(cls.PRESETS.keys())

    @classmethod
    def list_presets_table(cls) -> None:
        tbl = Table(
            title="[bold magenta]Style Presets[/bold magenta]",
            show_header=True,
            header_style="bold cyan",
            box=box.DOUBLE,
        )
        tbl.add_column("ID", justify="right", style="dim", width=3)
        tbl.add_column("Preset Name", style="bold yellow")
        tbl.add_column("Color", justify="center")
        tbl.add_column("Border", justify="center")
        tbl.add_column("Align", justify="center")

        border_names = {
            id(box.ROUNDED): "Rounded",
            id(box.DOUBLE): "Double",
            id(box.SQUARE): "Square",
            id(box.HEAVY): "Heavy",
            id(box.MINIMAL): "Minimal",
            id(box.MINIMAL_DOUBLE_HEAD): "Min-Double",
            id(box.DOUBLE_EDGE): "Dbl-Edge",
            id(box.ASCII): "ASCII",
            id(box.ASCII_DOUBLE_HEAD): "ASCII-Dbl",
            id(box.SIMPLE_HEAD): "Simple-Hd",
        }

        for i, name in enumerate(sorted(cls.PRESETS.keys())):
            s = cls.PRESETS[name]
            border_label = "None" if s["border"] is None else \
                            border_names.get(id(s["border"]), "?")
            tbl.add_row(
                str(i), name,
                f"[{s['color']}]{s['color']}[/{s['color']}]",
                border_label, s["align"],
            )
        console.print(tbl)


# ═══════════════════════════════════════════════════════════════════════
#  PROFILE MANAGER
# ═══════════════════════════════════════════════════════════════════════

class ProfileManager:
    """
    Loads and manages named banner profiles from a YAML config file.
    Falls back gracefully if PyYAML is not installed.
    """

    DEFAULT_CONFIG_PATH = "config.yaml"

    def __init__(self, config_path: str | None = None):
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.profiles: dict = {}
        self._loaded = False
        self._load()

    def _load(self) -> None:
        """Attempt to load profiles from YAML."""
        try:
            import yaml
        except ImportError:
            console.print("[yellow]⚠ PyYAML not installed. "
                          "Run: pip install pyyaml[/yellow]")
            return

        try:
            with open(self.config_path, "r") as f:
                data = yaml.safe_load(f)
        except FileNotFoundError:
            return  # No config file — that's OK
        except Exception as e:
            console.print(f"[red]✗ Error loading {self.config_path}: {e}[/red]")
            return

        if data and "profiles" in data:
            self.profiles = data["profiles"]
            self._loaded = True

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def get(self, name: str) -> dict | None:
        """Return a profile by name, or None if not found."""
        profile = self.profiles.get(name)
        if profile is None:
            console.print(f"[red]✗ Profile '{name}' not found in "
                          f"{self.config_path}[/red]")
            self.list_profiles()
            return None
        return profile

    def list_profiles(self) -> None:
        """Display all available profiles in a table."""
        if not self.profiles:
            console.print(f"[yellow]No profiles loaded. "
                          f"Create {self.config_path} or run "
                          f"'profiles --create' to generate a template.[/yellow]")
            return

        tbl = Table(
            title=f"[bold magenta]Banner Profiles ({self.config_path})[/bold magenta]",
            show_header=True,
            header_style="bold cyan",
            box=box.DOUBLE,
        )
        tbl.add_column("ID", justify="right", style="dim", width=3)
        tbl.add_column("Profile Name", style="bold yellow")
        tbl.add_column("Font", justify="center")
        tbl.add_column("Style", justify="center")
        tbl.add_column("Align", justify="center")
        tbl.add_column("Auto-Fit", justify="center")

        for i, name in enumerate(sorted(self.profiles.keys())):
            p = self.profiles[name]
            auto_fit = "✓" if p.get("auto_fit", True) else "✗"
            tbl.add_row(
                str(i),
                name,
                p.get("font", "standard"),
                p.get("style", "default"),
                p.get("align", "left"),
                auto_fit,
            )

        console.print(tbl)

    def create_template(self, path: str | None = None) -> None:
        """Generate a default config.yaml template."""
        target = path or self.DEFAULT_CONFIG_PATH

        template = """# ASCII Banner Engine — Profile Configuration
# Define named profiles for quick banner rendering.
# Usage: python3 banner_engine.py --profile hero "WELCOME"

profiles:
  hero:
    font: big
    style: neon-green
    align: center
    auto_fit: true

  subtitle:
    font: small
    style: clean
    align: center
    auto_fit: false

  error:
    font: standard
    style: heavy
    align: left
    auto_fit: true

  success:
    font: slant
    style: neon-green
    align: center
    auto_fit: true

  warning:
    font: speed
    style: comic
    align: center
    auto_fit: true

  matrix:
    font: binary
    style: matrix
    align: left
    auto_fit: true

  gothic:
    font: gothic
    style: royal
    align: center
    auto_fit: true

  debug:
    font: mini
    style: minimal
    align: left
    auto_fit: false
"""

        with open(target, "w") as f:
            f.write(template)

        console.print(f"[green]✓ Template created: {target}[/green]")
        console.print("[dim]Edit it to customize your profiles.[/dim]")


# ═══════════════════════════════════════════════════════════════════════
#  ASCII BANNER ENGINE
# ═══════════════════════════════════════════════════════════════════════

class ASCIIBannerEngine:
    """Multi-style ASCII banner generator using pyfiglet"""

    # Curated aliases — readable names for cryptic FIGlet font names
    _ALIASES = {
        "3d": "3-d",
        "isomeric": "isometric1",
        "technology": "4x4_offr",
        "fireball": "fire_font-s",
        "pump": "puffy",
    }

    # Auto-load all available FIGlet fonts, then layer aliases on top
    FONTS = {f: f for f in Figlet().getFonts()}
    FONTS.update(_ALIASES)

    def __init__(self, size_manager: SizeManager | None = None,
                 profile_manager: ProfileManager | None = None):
        self.sizer = size_manager or SizeManager()
        self.profiler = profile_manager or ProfileManager()

    # ── Core generation ──────────────────────────────────────────────

    def generate(self, text: str, font: str = "standard",
                 auto_fit: bool = False) -> str | None:
        if font not in self.FONTS:
            console.print(f"[red]Font '{font}' not found. "
                          f"Use 'fonts' command to list available.[/red]")
            return None
        if auto_fit:
            font = self.sizer.auto_fit_font(text, preferred_font=font)
        fig = Figlet(font=self.FONTS[font])
        return fig.renderText(text)

    # ── Display ──────────────────────────────────────────────────────

    def display_banner(self, text: str, font: str = "standard",
                       style: str = "default",
                       auto_fit: bool = True,
                       align: str | None = None) -> None:
        # Resolve style — .copy() prevents mutating the class-level PRESETS
        if style in StyleManager.PRESETS:
            preset = StyleManager.get(style).copy()
        else:
            preset = {"color": style, "border": box.ROUNDED, "align": "left"}

        if align:
            preset["align"] = align

        ascii_art = self.generate(text, font, auto_fit=auto_fit)
        if ascii_art is None:
            return

        if not self.sizer.fits(ascii_art, margin=6):
            ascii_art = self.sizer.truncate_to_width(
                ascii_art, self.sizer.usable_width - 6)

        rich_text = Text(ascii_art, style=preset["color"])
        aligned = Align(rich_text, align=preset["align"])

        panel_title = (f"[bold {preset['color']}]\n"
            f"{font.upper()} . {style.upper()}\n"
            f"[/bold {preset['color']}]")

        if preset["border"] is None:
            console.print(aligned)
        else:
            panel = Panel(
                aligned,
                title=panel_title,
                border_style=preset["color"],
                box=preset["border"],
                padding=(1, 2),
            )
            console.print(panel)
    def render_profile(self, text: str, profile_name: str) -> None:
        """Render banner using a named profile from config.yaml."""
        profile = self.profiler.get(profile_name)
        if profile is None:
            return

        font = profile.get("font", "standard")
        style = profile.get("style", "default")
        align = profile.get("align")
        auto_fit = profile.get("auto_fit", True)

        self.display_banner(text, font=font, style=style,
                           auto_fit=auto_fit, align=align)

    # ── Listing ──────────────────────────────────────────────────────

    def list_fonts(self) -> None:
        ref_table = Table(
            title=f"[bold magenta]Available ASCII Fonts ({len(self.FONTS)})[/bold magenta]",
            show_header=True,
            header_style="bold cyan",
            box=box.DOUBLE,
        )
        ref_table.add_column("ID", justify="right", style="dim", width=5)
        ref_table.add_column("Key", style="bold yellow")
        ref_table.add_column("FIGlet Name", style="dim")

        for i, (key, figlet_name) in enumerate(sorted(self.FONTS.items())):
            alias_tag = " [cyan](alias)[/cyan]" if key != figlet_name else ""
            ref_table.add_row(str(i), key, figlet_name + alias_tag)

        console.print(ref_table)

    def list_styles(self) -> None:
        StyleManager.list_presets_table()

    # ── Comparison ───────────────────────────────────────────────────
    def compare_fonts(self, text: str, fonts: list[str] | None = None) -> None:
        if fonts is None:
            fonts = [
                "standard", "slant", "big", "ghost",
                "digital", "small", "gothic", "bubble",
            ]

        preview_grid = Table(
            title="[bold green]Font Comparison Preview[/bold green]",
            box=box.MINIMAL_DOUBLE_HEAD,
            show_lines=True,
        )
        preview_grid.add_column("Font -> Preview", style="white")

        colors = ["bright_green", "bright_cyan", "bright_yellow",
                  "bright_magenta", "bright_blue", "bright_red",
                  "bright_white", "green"]

        for i, font_name in enumerate(fonts):
            if font_name not in self.FONTS:
                preview_grid.add_row(f"[red]x {font_name} (not found)[/red]")
                continue
            try:
                fig = Figlet(font=self.FONTS[font_name])
                preview = fig.renderText(text)
                preview_lines = preview.splitlines()
                if len(preview_lines) > 6:
                    preview = "\n".join(preview_lines[:6]) + "\n..."
                color = colors[i % len(colors)]
                cell = (f"[bold {color}]{font_name}[/bold {color}]\n"
                        f"[{color}]{preview}[/{color}]")
                preview_grid.add_row(cell)
            except Exception as e:
                preview_grid.add_row(f"[red]x {font_name} (error: {e})[/red]")

        console.print(preview_grid)

    def compare_styles(self, text: str = "COMPARE", styles: list[str] | None = None) -> None:
        """Compare multiple style presets side-by-side in a table."""
        if styles is None:
            styles = ["default", "clean", "neon-green", "heavy", "matrix", "royal", "bare"]

        border_names = {
            id(box.ROUNDED): "Rounded",
            id(box.DOUBLE): "Double",
            id(box.SQUARE): "Square",
            id(box.HEAVY): "Heavy",
            id(box.MINIMAL): "Minimal",
            id(box.MINIMAL_DOUBLE_HEAD): "Min-Double",
            id(box.DOUBLE_EDGE): "Dbl-Edge",
            id(box.ASCII): "ASCII",
            id(box.ASCII_DOUBLE_HEAD): "ASCII-Dbl",
            id(box.SIMPLE_HEAD): "Simple-Hd",
        }

        grid = Table(
            title=f"[bold magenta]Style Comparison — '{text}'[/bold magenta]",
            box=box.MINIMAL_DOUBLE_HEAD,
            show_lines=True,
        )
        grid.add_column("Style → Preview", style="white")

        for style_name in styles:
            preset = StyleManager.get(style_name)

            border_label = "None" if preset["border"] is None else \
                border_names.get(id(preset["border"]), "Unknown")

            cell = f"[bold {preset['color']}]{style_name}[/bold {preset['color']}]\n"
            cell += f"[dim]Color: {preset['color']} | Border: {border_label} | Align: {preset['align']}[/dim]\n"

            art = self.generate(text.upper(), "small", auto_fit=True)
            if art:
                lines = art.splitlines()
                preview = "\n".join(lines)
                cell += f"[{preset['color']}]{preview}[/{preset['color']}]"

            grid.add_row(cell)

        console.print(grid)

    # ── Batch / Export ───────────────────────────────────────────────

    def render_all_fonts(self, text: str, output_dir: str = "./banner_output") -> None:
        os.makedirs(output_dir, exist_ok=True)
        count = 0
        failed = 0
        for key, figlet_name in sorted(self.FONTS.items()):
            try:
                fig = Figlet(font=figlet_name)
                art = fig.renderText(text)
                safe_name = key.replace("/", "_").replace("\\", "_")
                path = os.path.join(output_dir, f"{safe_name}.txt")
                with open(path, "w", encoding="utf-8") as f:
                    f.write(f"# Font: {key} -> {figlet_name}\n")
                    f.write(f"# Size: {self.sizer.measure_banner(art)} cols\n")
                    f.write(art)
                count += 1
            except Exception:
                console.print(f"[red]x Failed: {key} ({figlet_name})[/red]")
                failed += 1
        console.print(f"[green]Rendered {count} fonts to {output_dir}/[/green]")
        if failed:
            console.print(f"[red]{failed} fonts failed.[/red]")

    def run_diagnostics(self) -> None:
        """Run full engine diagnostics."""
        console.print("\n[bold reverse] ENGINE DIAGNOSTICS [/bold reverse]\n")

        # Terminal info
        console.print("[bold cyan]Terminal:[/bold cyan]")
        console.print(f"  {self.sizer.report()}")

        # Font stats
        console.print("\n[bold cyan]Fonts:[/bold cyan]")
        console.print(f"  Total loaded: {len(self.FONTS)}")
        aliases = {k: v for k, v in self.FONTS.items() if k != v}
        console.print(f"  Aliases: {len(aliases)}")
        for k, v in aliases.items():
            console.print(f"    {k} -> {v}")

        # Style stats
        console.print("\n[bold cyan]Styles:[/bold cyan]")
        console.print(f"  Presets: {len(StyleManager.PRESETS)}")
        for name in sorted(StyleManager.PRESETS.keys()):
            s = StyleManager.PRESETS[name]
            border = "None" if s["border"] is None else "Set"
            console.print(f"    {name}: color={s['color']}, border={border}, align={s['align']}")

        # Profile stats
        console.print("\n[bold cyan]Profiles:[/bold cyan]")
        console.print(f"  Config file: {self.profiler.config_path}")
        console.print(f"  Loaded: {self.profiler.is_loaded}")
        console.print(f"  Count: {len(self.profiler.profiles)}")
        if self.profiler.profiles:
            for name in sorted(self.profiler.profiles.keys()):
                p = self.profiler.profiles[name]
                console.print(f"    {name}: font={p.get('font','?')}, "
                              f"style={p.get('style','?')}, "
                              f"align={p.get('align','?')}")

        # Test render
        console.print("\n[bold cyan]Test Render:[/bold cyan]")
        test_text = "DIAG"
        test_font = "standard"
        try:
            art = self.generate(test_text, test_font, auto_fit=False)
            if art:
                width = self.sizer.measure_banner(art)
                fits = self.sizer.fits(art, margin=6)
                console.print(f"  Text: '{test_text}'")
                console.print(f"  Font: {test_font}")
                console.print(f"  Width: {width} cols")
                console.print(f"  Fits terminal: {'Yes' if fits else 'No'}")
                console.print(f"  Lines: {len(art.splitlines())}")
            else:
                console.print("  [red]Failed to generate test banner[/red]")
        except Exception as e:
            console.print(f"  [red]Error: {e}[/red]")

        console.print("\n[green]Diagnostics complete.[/green]\n")

# ═══════════════════════════════════════════════════════════════════════
#  DEMO FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════

def demo_basic_banners():
    engine = ASCIIBannerEngine()
    console.print("\n[bold blue]=== BASIC BANNERS (auto-fit ON) ===[/bold blue]\n")
    engine.display_banner("HELLO", "standard", "clean")
    engine.display_banner("WELCOME", "slant", "neon-green")
    engine.display_banner("AUTHOR", "big", "elegant")
    engine.display_banner("SYSTEM", "ghost", "neon-blue")


def demo_themed_banners():
    engine = ASCIIBannerEngine()
    themes = [
        ("CYBERPUNK", "speed",     "cyber"),
        ("GHOST",     "ghost",     "bare-center"),
        ("MATRIX",    "binary",    "matrix"),
        ("SPACE",     "starwars",  "neon-pink"),
        ("URBAN",     "graffiti",  "retro"),
        ("GOTHIC",    "gothic",    "royal"),
    ]
    console.print("\n[bold]=== THEMED COLLECTIONS ===[/bold]\n")
    for text, font, style in themes:
        engine.display_banner(text, font, style)
        console.print()


def demo_styles():
    engine = ASCIIBannerEngine()
    console.print("\n[bold magenta]=== STYLE PRESETS ===[/bold magenta]\n")
    StyleManager.list_presets_table()
    console.print()
    for style in ["minimal", "neon-green", "matrix", "royal", "arcade", "bare"]:
        engine.display_banner("STYLES", "slant", style)


def demo_size_manager():
    engine = ASCIIBannerEngine()
    sm = engine.sizer
    console.print(f"\n[bold cyan]=== SIZE MANAGER REPORT ===[/bold cyan]")
    console.print(f"  {sm.report()}\n")
    test_text = "AUTOFIT_TESTING_WIDE_BANNERS"
    console.print(f"[yellow]Testing text: '{test_text}'[/yellow]")
    best_font = sm.auto_fit_font(test_text, preferred_font="big")
    console.print(f"[green]Auto-fit selected: '{best_font}'[/green]\n")
    engine.display_banner(test_text, best_font, "clean", auto_fit=False)


# ═══════════════════════════════════════════════════════════════════════
#  INTERACTIVE MENU
# ═══════════════════════════════════════════════════════════════════════

def interactive_menu():
    engine = ASCIIBannerEngine()
    console.print("\n[bold reverse] ASCII BANNER ENGINE v1.0 [/bold reverse]")
    console.print(f"[dim]  {engine.sizer.report()}[/dim]")
    console.print(f"[dim]  {len(engine.FONTS)} fonts loaded[/dim]\n")

    while True:
        console.print("\n[bold cyan]Commands:[/bold cyan]")
        console.print("  [yellow]<text>[/yellow]          - generate banner")
        console.print("  [yellow]hero: WELCOME[/yellow]   - use 'hero' profile")
        console.print("  [yellow]6: WELCOME[/yellow]      - use profile ID #6")
        console.print("  [yellow]hero[/yellow]             - select profile, then type text")
        console.print("  [yellow]fonts[/yellow]           - list all fonts")
        console.print("  [yellow]styles[/yellow]          - list style presets")
        console.print("  [yellow]sizes[/yellow]           - show size info")
        console.print("  [yellow]compare <text>[/yellow]   - compare sample fonts")
        console.print("  [yellow]compare-styles <text>[/yellow] - compare style presets")
        console.print("  [yellow]export <text>[/yellow]     - render all fonts to files")
        console.print("  [yellow]profiles[/yellow]       - list saved profiles")
        console.print("  [yellow]create-config[/yellow] - generate config.yaml template")
        console.print("  [yellow]debug[/yellow]            - run engine diagnostics")
        console.print("  [yellow]debug: <text>[/yellow]   - render with debug info")
        console.print("  [yellow]quit[/yellow]")

        raw = console.input("\n[bold yellow]> [/bold yellow]").strip()
        if not raw:
            continue

        parts = raw.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if cmd == "quit":
            console.print("[green]Goodbye.[/green]")
            break
        elif cmd == "fonts":
            engine.list_fonts()
        elif cmd == "styles":
            engine.list_styles()
        elif cmd == "sizes":
            console.print(f"[cyan]{engine.sizer.report()}[/cyan]")
            best = engine.sizer.auto_fit_font("SAMPLE TEXT", "big")
            console.print(f"[green]Best fit for 'SAMPLE TEXT': {best}[/green]")
        elif cmd == "compare":
            engine.compare_fonts(arg or "Hello")
        elif cmd == "compare-styles":
            engine.compare_styles(arg or "TEST")
        elif cmd == "export":
            text = arg or "EXPORT_DEMO"
            engine.render_all_fonts(text)
        elif cmd == "profiles":
            engine.profiler.list_profiles()
        elif cmd == "create-config":
            engine.profiler.create_template()
        else:
            text = raw

            # ── Profile selection by name or ID with colon ──
            # Examples: "hero: WELCOME" or "6: WELCOME"
            if ":" in text:
                parts = text.split(":", 1)
                selector = parts[0].strip()
                actual_text = parts[1].strip()

                # Try ID number first
                if selector.isdigit():
                    idx = int(selector)
                    sorted_names = sorted(engine.profiler.profiles.keys())
                    if 0 <= idx < len(sorted_names):
                        profile_name = sorted_names[idx]
                        engine.render_profile(actual_text, profile_name)
                        continue
                    else:
                        console.print(f"[red]Invalid ID. Use 0-{len(sorted_names)-1}[/red]")
                        continue

                # Try profile name
                profile = engine.profiler.get(selector)
                if profile is not None:
                    engine.render_profile(actual_text, selector)
                    continue

                # Not a profile — treat as banner text with colon
                console.print(f"[red]Profile '{selector}' not found.[/red]")
                continue

            # ── Profile selection by name alone (no colon) ──
            # Example: "hero" → prompts for text
            if text in engine.profiler.profiles:
                console.print(f"[dim]Using profile '{text}'. Enter text to render:[/dim]")
                profile_text = console.input("[bold]> [/bold]").strip()
                if profile_text:
                    engine.render_profile(profile_text, text)
                continue

            # ── Profile selection by ID number alone (no colon) ──
            # Example: "6" → prompts for text
            if text.isdigit():
                idx = int(text)
                sorted_names = sorted(engine.profiler.profiles.keys())
                if 0 <= idx < len(sorted_names):
                    profile_name = sorted_names[idx]
                    console.print(f"[dim]Using profile '{profile_name}'. Enter text to render:[/dim]")
                    profile_text = console.input("[bold]> [/bold]").strip()
                    if profile_text:
                        engine.render_profile(profile_text, profile_name)
                    continue
                else:
                    console.print(f"[red]Invalid ID. Use 0-{len(sorted_names)-1}[/red]")
                    continue
            # ── Debug mode: render + show diagnostic info ──
            if text.lower().startswith("debug:"):
                debug_text = text.split(":", 1)[1].strip()
                if not debug_text:
                    debug_text = "DEBUG"

                console.print("\n[bold yellow]--- DEBUG INFO ---[/bold yellow]")
                console.print(f"  Input text: '{debug_text}'")
                console.print(f"  Terminal: {engine.sizer.terminal_width} cols")
                console.print(f"  Usable: {engine.sizer.usable_width} cols")

                art = engine.generate(debug_text, "standard", auto_fit=True)
                if art:
                    width = engine.sizer.measure_banner(art)
                    fits = engine.sizer.fits(art, margin=6)
                    truncated = not fits

                    console.print(f"  Font used: standard (auto-fit)")
                    console.print(f"  Banner width: {width} cols")
                    console.print(f"  Fits: {'Yes' if fits else 'No (truncated)'}")
                    console.print(f"  Lines: {len(art.splitlines())}")
                    console.print(f"  Profile loaded: {engine.profiler.is_loaded}")
                    console.print(f"  Fonts available: {len(engine.FONTS)}")
                    console.print(f"  Styles available: {len(StyleManager.PRESETS)}")
                    console.print()

                engine.display_banner(debug_text, "standard", "clean", auto_fit=True)
                continue

            # ── Standalone 'debug' command runs full diagnostics ──
            if text.lower() == "debug":
                engine.run_diagnostics()
                continue

            # ── Normal flow: prompt for font + style ──
            console.print("\n[dim]Font (name or number 1-8):[/dim]")
            console.print("  1-standard 2-slant 3-big 4-ghost "
                          "5-banner 6-gothic 7-digital 8-small")
            font_choice = console.input("[bold]Font: [/bold]").strip().lower()
            font_map = {
                "1": "standard", "2": "slant", "3": "big",
                "4": "ghost", "5": "banner", "6": "gothic",
                "7": "digital", "8": "small",
            }
            font = font_map.get(font_choice, font_choice or "standard")

            console.print("[dim]Style (preset name or color):[/dim]")
            console.print(f"  {' | '.join(StyleManager.list_presets()[:8])}")
            style_choice = console.input("[bold]Style: [/bold]").strip().lower()
            style = style_choice or "default"

            engine.display_banner(text, font, style)


# ═══════════════════════════════════════════════════════════════════════
#  MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    try:
        from pyfiglet import Figlet
    except ImportError:
        console.print("[red]Install required packages:[/red]")
        console.print("  pip install pyfiglet rich")
        sys.exit(1)

    font_count = len(ASCIIBannerEngine.FONTS)

    print(f"""
+-----------------------------------------------------------+
|                                                           |
|   ASCII BANNER ENGINE v1.0                                |
|                                                           |
|   {font_count} fonts auto-loaded | 18 style presets | SizeManager  |
|                                                           |
+-----------------------------------------------------------+
""")

    try:
        if len(sys.argv) > 1:
            cmd = sys.argv[1].lower()

            if cmd == "--demo":
                demo_basic_banners()
            elif cmd == "--themes":
                demo_themed_banners()
            elif cmd == "--styles":
                demo_styles()
            elif cmd == "--sizes":
                demo_size_manager()
            elif cmd == "--compare":
                ASCIIBannerEngine().compare_fonts(
                    sys.argv[2] if len(sys.argv) > 2 else "Hello")
            elif cmd == "--compare-styles":
                ASCIIBannerEngine().compare_styles(
                    sys.argv[2] if len(sys.argv) > 2 else "TEST")
            elif cmd == "--interactive":
                interactive_menu()
            elif cmd == "--fonts":
                ASCIIBannerEngine().list_fonts()
            elif cmd == "--export":
                ASCIIBannerEngine().render_all_fonts(
                    sys.argv[2] if len(sys.argv) > 2 else "DEMO")
            elif cmd == "--profiles":
                pm = ProfileManager()
                if not pm.is_loaded:
                    console.print("[yellow]No config.yaml found.[/yellow]")
                    console.print("[dim]Create one with: "
                                  "python3 banner_engine.py --create-config[/dim]")
                else:
                    pm.list_profiles()
            elif cmd == "--create-config":
                pm = ProfileManager()
                pm.create_template()
            elif cmd == "--profile":
                if len(sys.argv) < 3:
                    console.print("[red]Usage: --profile <name> <text>[/red]")
                    console.print("[dim]Available profiles: python3 "
                                  "banner_engine.py --profiles[/dim]")
                else:
                    profile_name = sys.argv[2]
                    text = sys.argv[3] if len(sys.argv) > 3 else "PROFILE TEST"
                    engine = ASCIIBannerEngine()
                    engine.render_profile(text, profile_name)
            elif cmd == "--debug":
                engine = ASCIIBannerEngine()
                engine.run_diagnostics()
            elif cmd == "--verbose":
                if len(sys.argv) < 3:
                    console.print("[red]Usage: --verbose <text>[/red]")
                else:
                    text = sys.argv[2]
                    engine = ASCIIBannerEngine()
                    console.print("\n[bold yellow]--- VERBOSE RENDER ---[/bold yellow]")
                    console.print(f"  Input: '{text}'")
                    console.print(f"  Terminal: {engine.sizer.terminal_width} cols")

                    art = engine.generate(text, "standard", auto_fit=True)
                    if art:
                        width = engine.sizer.measure_banner(art)
                        fits = engine.sizer.fits(art, margin=6)
                        console.print(f"  Auto-fit: ON")
                        console.print(f"  Width: {width} cols")
                        console.print(f"  Fits: {'Yes' if fits else 'No'}")
                        console.print(f"  Lines: {len(art.splitlines())}")
                        console.print()

                    engine.display_banner(text, "standard", "clean", auto_fit=True)
            elif cmd == "--help":
                console.print("""
[bold]ASCII Banner Engine v1.0 - Commands:[/bold]

  [cyan]--demo[/cyan]            Basic banner examples
  [cyan]--themes[/cyan]          Themed banner collection
  [cyan]--styles[/cyan]          Style preset showcase
  [cyan]--sizes[/cyan]           SizeManager demo
  [cyan]--compare <text>[/cyan]  Compare fonts side-by-side
  [cyan]--compare-styles <text>[/cyan]  Compare style presets
  [cyan]--fonts[/cyan]           List all available fonts
  [cyan]--export <text>[/cyan]   Render all fonts to ./banner_output/
  [cyan]--interactive[/cyan]    Full interactive menu
  [cyan]--debug[/cyan]            Run full engine diagnostics
  [cyan]--verbose <text>[/cyan]   Render with detailed output
  [cyan]<text>[/cyan]            Quick render with default styling
""")
            else:
                ASCIIBannerEngine().display_banner(sys.argv[1], "banner", "clean")
        else:
            interactive_menu()

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted. Goodbye.[/yellow]")
        sys.exit(0)
    except EOFError:
        console.print("\n[yellow]End of input. Goodbye.[/yellow]")
        sys.exit(0)
