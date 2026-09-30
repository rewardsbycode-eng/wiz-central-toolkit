# ASCII Banner Engine v1.0

> Generate stunning ASCII text banners with auto-discovered pyfiglet fonts (typically 571+), 18 style presets, intelligent terminal sizing, and full engine diagnostics.


---

## Features

### Auto-Discovered Fonts (Typically 571+)

No hardcoded font dictionaries. The engine discovers all available pyfiglet fonts at runtime and adds 5 curated aliases for readability.

| Category | Count | Example |
|----------|-------|---------|
| Auto-discovered fonts | Depends on your installation (typically ~571) | standard, slant, big, gothic |
| Curated aliases | 5 (hardcoded) | 3d to 3-d, isomeric to isometric1 |
| Your total | Reported at startup | Shown in interactive menu header |

### 18 Style Presets

| Category | Presets |
|----------|---------|
| Classic | default, minimal, clean, boxed, heavy |
| Neon/Cyber | neon-blue, neon-green, neon-pink, cyber, matrix |
| Elegant | elegant, royal, shadow |
| Playful | retro, arcade, comic |
| Bare | bare, bare-center |

### Intelligent Size Manager

- Auto-fit: Tries larger fonts first, falls back to smaller ones if banner overflows
- Truncation: Hard-cuts wide banners with indicator
- Padding/Alignment: Left, center, right padding control
- Real-time detection: Refreshes terminal width on window resize

### Debug & Diagnostics (New!)

Full transparency on engine state with new diagnostic tools:

| Feature | Description |
|---------|-------------|
| `--debug` CLI flag | Run full engine diagnostics (terminal, fonts, styles, profiles) |
| `--verbose <text>` | Render banner with detailed output (width, fit status, line count) |
| `debug` command (interactive) | Run full diagnostics from interactive menu |
| `debug: <text>` (interactive) | Render banner with per-render diagnostic info |
| `debug.log` file | Automatic error logging with timestamps |

### Export Mode

Render your text in every font and save to individual .txt files:

    python3 banner_engine.py --export TRUTH

---

## Installation

    pip install pyfiglet rich

Verify:

    python3 banner_engine.py --help

---

## Usage

### CLI Commands

| Command | Description |
|---------|-------------|
| `python3 banner_engine.py "<text>"` | Quick render with default styling |
| `python3 banner_engine.py --demo` | Basic banner examples |
| `python3 banner_engine.py --themes` | Themed collections |
| `python3 banner_engine.py --styles` | Show style preset gallery |
| `python3 banner_engine.py --sizes` | SizeManager diagnostics |
| `python3 banner_engine.py --fonts` | List all available fonts |
| `python3 banner_engine.py --compare <text>` | Side-by-side font comparison |
| `python3 banner_engine.py --compare-styles <text>` | Compare style presets side-by-side |
| `python3 banner_engine.py --export <text>` | Render all fonts to files |
| `python3 banner_engine.py --interactive` | Full interactive menu |
| `python3 banner_engine.py --debug` | Run full engine diagnostics |
| `python3 banner_engine.py --verbose <text>` | Render with detailed output |
| `python3 banner_engine.py --help` | Show command reference |

### Interactive Mode

    python3 banner_engine.py

| Input | Action |
|-------|--------|
| `<text>` | Enter font + style prompts |
| `fonts` | List all fonts |
| `styles` | Show style presets |
| `sizes` | Terminal size info |
| `compare <text>` | Font comparison |
| `compare-styles <text>` | Compare style presets in grid |
| `export <text>` | Batch render |
| `debug` | Run full engine diagnostics |
| `debug: <text>` | Render with debug info |
| `quit` | Exit |

---

## Style Presets

| Preset | Color | Border | Alignment |
|--------|-------|--------|-----------|
| default | white | Rounded | left |
| minimal | dim | Minimal | left |
| clean | cyan | Square | left |
| boxed | yellow | Double | left |
| heavy | red | Heavy | left |
| neon-blue | bright_blue | Double Edge | center |
| neon-green | bright_green | Double Edge | center |
| neon-pink | bright_magenta | Double Edge | center |
| cyber | blue | ASCII Double Head | center |
| matrix | green | Minimal Double Head | left |
| elegant | magenta | Rounded | center |
| royal | blue | Double | center |
| shadow | bright_black | Simple Head | left |
| retro | bright_yellow | ASCII | center |
| arcade | bright_cyan | Double | center |
| comic | bright_red | Rounded | center |
| bare | white | none | left |
| bare-center | cyan | none | center |

Bonus: Any Rich color name works as a style input too!

---

## Programmatic Usage

    from banner_engine import ASCIIBannerEngine, StyleManager, SizeManager

    engine = ASCIIBannerEngine()
    art = engine.generate("TRUTH", font="big", auto_fit=True)
    engine.display_banner("TRUTH", font="standard", style="neon-green")

---

## Curated Aliases (5)

| Alias Key | Actual FIGlet Name | Purpose |
|-----------|-------------------|---------|
| 3d | 3-d | Readable shorthand |
| isomeric | isometric1 | Cleaner naming |
| technology | 4x4_offr | Cryptic name fix |
| fireball | fire_font-s | Thematic alias |
| pump | puffy | Typo fix |

---

## Font Families (Examples)

- Large: big, block, colossal, epic, doh, 3d, isometric1-4, henry_3d, letters
- Small: small, mini, term, stop, alphabet, rectangles, smkeyboard, smslant
- Tech: digital, binary, lcd, dotmatrix, hex, eftirobot, eftiwater, eftiwall
- Decorative: ghost, starwars, cosmic, graffiti, script, rounded, gothic
- AMC: amc_razor, amc_razor2, amc_tubes, amc_neko, amc_3_liv1
- NancyJ: nancyj, nancyj_fancy, nancyj_improved, nancyj_underlined

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| ModuleNotFoundError: pyfiglet | Run `pip install pyfiglet rich` |
| Font not found | Use `--fonts` to list available keys |
| Banner overflows terminal | Enable auto_fit=True or use smaller fonts |
| Colors dont show | Ensure terminal supports ANSI colors |
| UnicodeEncodeError on Windows | Set `PYTHONIOENCODING=utf-8` |
| KeyboardInterrupt traceback | Now handled gracefully in v1.0+ |

---

## Project Structure

    ASCII_Banner_Engine/
    +-- banner_engine.py
    +-- banner_output/
    +-- config.yaml
    +-- debug.log
    +-- README.md

---

## Credits

- pyfiglet - The legendary ASCII art font library
- Rich - Beautiful Python terminal formatting

---

## License

MIT - Free to use, modify, and distribute.

---

## Roadmap

- [x] Debug diagnostics mode
- [x] Verbose render output
- [x] Error logging to file
- [x] Graceful interrupt handling
- [ ] Gradient color banners (multi-color lines)
- [ ] Animation frames (cycle fonts/styles)
- [ ] Web API endpoint (Flask/FastAPI)
- [ ] Image export (PNG/JPEG via Pillow)
- [ ] Plugin system for custom renderers

---

**Go ahead and create some art.**

**SUDOER - Alex** - Honesty first. Audit everything. If its not real, it doesnt belong.
