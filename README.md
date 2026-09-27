# Wiz Central Toolkit

## Welcome

Welcome to Wiz Central Toolkit.

Wiz Central Toolkit is a command-line toolkit for deterministic developer utilities. It brings multiple practical tools together under one project and provides a consistent way to run them from the terminal.

The main command is `wiz`. It dispatches requests to the toolkit's registered utilities. The project also includes `godfatherwiz`, an interactive router that helps users discover and launch available tools. Optional AI support can be configured through Ollama or an OpenAI-compatible API.

The toolkit is intended to be:

- Simple to install and run
- Organized around independent command-line tools
- Useful for repeatable developer workflows
- Easy to extend with new utilities
- Safe to use in environments where predictable output matters

This project is currently under active development. Some tools may be experimental or incomplete, while implemented tools are tested through the project's automated test suite.

## What Is Wiz Central Toolkit?

Wiz Central Toolkit is a collection of command-line utilities managed from one central interface.

Instead of installing or remembering separate commands for every utility, users can work from a single toolkit and access the available functionality through `wiz` or `godfatherwiz`.

Typical usage looks like this:

```bash
wiz <tool> [arguments]
```


The main command is `wiz`, which dispatches to individual tools. `godfatherwiz` provides an interactive router for all registered tools and optional AI access through Ollama or an OpenAI-compatible API.

## Requirements

- Python 3.10 or newer
- `pip`
- A virtual environment is recommended

Optional dependencies used by implemented tools include:

- `pyfiglet`
- `rich`

## Installation

From the repository root:

```bash
python3 -m venv fixy-env
source fixy-env/bin/activate
python3 -m pip install -e .
```

If the virtual environment already exists:

```bash
source fixy-env/bin/activate
python3 -m pip install -e .
```

Verify the installation:

```bash
wiz --help
```

## General Usage

The general command format is:

```bash
wiz <tool> [arguments...]
```

Examples:

```bash
wiz bannerwiz HELLO
wiz readwiz verbs
wiz readwiz law
wiz rustwiz --help
wiz godfatherwiz
```

Every tool should support:

```bash
wiz <tool> --help
```

## Available Tools

| Tool | Status | Description |
|---|---|---|
| `bannerwiz` | Implemented | Render styled FIGlet ASCII banners |
| `codeguardwiz` | Placeholder | Planned code-safety checker |
| `debugwiz` | Placeholder | Planned debugging utility |
| `diffwiz` | Placeholder | Planned diff utility |
| `godfatherwiz` | Implemented | Interactive deterministic router with optional AI |
| `jsonwiz` | Placeholder | Planned JSON utility |
| `pythonwiz` | Placeholder | Planned Python utility |
| `readwiz` | Implemented | Read-only shell-command policy engine |
| `rustwiz` | Implemented | Rust project checker |
| `tmuxwiz` | Placeholder | Planned tmux utility |
| `todowiz` | Placeholder | Planned TODO utility |
| `writewiz` | Placeholder | Planned write utility |

Placeholder tools currently report that they are not yet ported. They are registered and routable, but they should not be treated as implemented functionality yet.

## bannerwiz

`bannerwiz` renders text as an ASCII banner using FIGlet and optional Rich styling.

Basic usage:

```bash
wiz bannerwiz HELLO
wiz bannerwiz "WIZ CENTRAL"
```

Options:

```text
-f, --font FONT
-s, --style STYLE
-a, --align {left,center,right}
--no-auto-fit
--subtitle SUBTITLE
--fonts
--styles
--compare TEXT
--demo
--sizes
```

Examples:

```bash
wiz bannerwiz HELLO --style minimal
wiz bannerwiz HELLO --style neon-blue
wiz bannerwiz HELLO --align center
wiz bannerwiz HELLO --subtitle "Wizard Central Toolkit"
wiz bannerwiz --fonts
wiz bannerwiz --styles
wiz bannerwiz --demo
wiz bannerwiz --sizes
wiz bannerwiz --compare HELLO
```

Show command help:

```bash
wiz bannerwiz --help
```

Available style names include:

```text
default
minimal
clean
boxed
heavy
neon-blue
neon-green
neon-pink
cyber
matrix
```

## readwiz

`readwiz` is a read-only shell-command policy engine. It checks whether a raw shell command is allowed by the configured read-only policy.

### Check a command

```bash
wiz readwiz check "pwd"
wiz readwiz check "ls -la"
wiz readwiz check "find . -maxdepth 2 -type f"
```

Always quote the command passed to `check`:

```bash
wiz readwiz check "git status --short"
```

The command returns one of these verdicts:

```text
ALLOW
DENIED
```

Exit codes:

```text
0 = allowed
1 = denied
2 = usage error
```

### Show allowed and denied verbs

```bash
wiz readwiz verbs
```

### Show the read-only policy

```bash
wiz readwiz law
```

Show help:

```bash
wiz readwiz --help
```

`readwiz` evaluates commands. It does not execute the command being checked.

## rustwiz

`rustwiz` provides Rust project checks.

Usage:

```text
wiz rustwiz check <file.rs|dir> ...
wiz rustwiz build <crate-dir>
```

Examples:

```bash
wiz rustwiz check src/main.rs
wiz rustwiz check src/
wiz rustwiz check src/main.rs src/lib.rs
wiz rustwiz build .
```

Show help:

```bash
wiz rustwiz --help
```

The `build` command expects a Rust crate directory containing the appropriate Cargo project files.

## godfatherwiz

`godfatherwiz` is the interactive toolkit router.

Start it with:

```bash
wiz godfatherwiz
```

The interactive prompt is:

```text
godfather>
```

### Interactive commands

```text
<tool> [args...]       run a registered deterministic tool
tools                  list registered tools
ask <prompt>           ask the configured optional AI provider
ai status              show AI provider configuration
help                   show this help
exit                   leave the REPL
quit                   leave the REPL
```

Example session:

```text
godfather> tools
godfather> bannerwiz HELLO --style minimal
godfather> readwiz verbs
godfather> ai status
godfather> exit
```

The deterministic tools do not require an AI provider.

### Run a tool through godfatherwiz

```bash
wiz godfatherwiz
```

Then:

```text
godfather> bannerwiz HELLO
godfather> readwiz check "pwd"
godfather> rustwiz --help
godfather> exit
```

Tool help commands are handled without terminating the REPL:

```text
godfather> bannerwiz --help
godfather> readwiz --help
godfather> rustwiz --help
```

Unknown commands are reported without terminating the session:

```text
godfather> unknown-tool
```

## Optional AI Support

AI is disabled by default. The deterministic toolkit continues to work when no AI provider is configured.

Check the current AI configuration inside the REPL:

```text
godfather> ai status
```

Default output:

```text
AI provider: none
Deterministic tool routing is available.
Set WIZ_AI_PROVIDER to enable optional AI.
```

### Ollama

Configure Ollama:

```bash
export WIZ_AI_PROVIDER=ollama
export WIZ_AI_MODEL=llama3.2
export WIZ_AI_BASE_URL=http://localhost:11434
```

Start the router:

```bash
wiz godfatherwiz
```

Ask a question:

```text
godfather> ai status
godfather> ask Explain what readwiz does
```

The default Ollama endpoint is:

```text
http://localhost:11434
```

The adapter sends chat requests to:

```text
http://localhost:11434/api/chat
```

### OpenAI-compatible API

Configure an OpenAI-compatible service:

```bash
export WIZ_AI_PROVIDER=openai-compatible
export WIZ_AI_MODEL=your-model
export WIZ_AI_BASE_URL=https://api.example.com/v1
export WIZ_AI_API_KEY='your-api-key'
```

Start the router:

```bash
wiz godfatherwiz
```

Then:

```text
godfather> ai status
godfather> ask Explain deterministic routing
```

The adapter sends chat requests to:

```text
https://api.example.com/v1/chat/completions
```

The API key is sent as a bearer token. Do not commit API keys to the repository.

### Disable AI

Unset the provider variables:

```bash
unset WIZ_AI_PROVIDER
unset WIZ_AI_MODEL
unset WIZ_AI_BASE_URL
unset WIZ_AI_API_KEY
```

Or explicitly disable it:

```bash
export WIZ_AI_PROVIDER=none
```

With AI disabled, this remains available:

```text
godfather> bannerwiz HELLO
```

This reports a controlled error:

```text
godfather> ask test
AI unavailable: No AI provider configured. Use a deterministic tool command or configure Ollama/API access.
```

## Command-Line Testing

Test top-level help:

```bash
wiz --help
```

Test every registered tool's help path:

```bash
for tool in \
  bannerwiz \
  codeguardwiz \
  debugwiz \
  diffwiz \
  godfatherwiz \
  jsonwiz \
  pythonwiz \
  readwiz \
  rustwiz \
  tmuxwiz \
  todowiz \
  writewiz
do
  echo "===== $tool ====="
  wiz "$tool" --help
done
```

Test the interactive router:

```bash
wiz godfatherwiz <<'SESSION'
help
ai status
tools
bannerwiz --help
readwiz --help
rustwiz --help
ask
unknown-tool
exit
SESSION
```

## Development Checks

Compile the Python source:

```bash
python3 -m py_compile \
  src/wiz_central_toolkit/godfatherwiz/ai.py \
  src/wiz_central_toolkit/godfatherwiz/__main__.py
```

Run the test suite:

```bash
python3 -m pytest
```

Check for whitespace errors:

```bash
git diff --check
```

Check repository state:

```bash
git status --short
```

A clean working tree produces no output from:

```bash
git status --short
```

## Git Workflow

Review changes:

```bash
git diff
git diff --cached
```

Stage all intended changes:

```bash
git add -A
```

Commit:

```bash
git commit -m "Describe the change"
```

Show the latest commit:

```bash
git show --stat --oneline HEAD
```

## Current Test Status

The current test suite contains the package version test. Run:

```bash
python3 -m pytest
```

The deterministic router and provider adapter should also be manually tested using the commands in this README.

## Project Layout

```text
src/
└── wiz_central_toolkit/
    ├── bannerwiz/
    ├── codeguardwiz/
    ├── debugwiz/
    ├── diffwiz/
    ├── godfatherwiz/
    │   ├── __main__.py
    │   └── ai.py
    ├── jsonwiz/
    ├── pythonwiz/
    ├── readwiz/
    │   ├── __main__.py
    │   └── read_wizard.py
    ├── rustwiz/
    ├── tmuxwiz/
    ├── todowiz/
    ├── writewiz/
    ├── tools_registry.py
    └── wiz/
```

## License

