# Wiz Central Toolkit (`wiz-central-toolkit`)

> **The Sovereign Developer Utilities Fleet & AI Router**  
> Fast, zero-dependency, local-first CLI tools designed for Linux development, system orchestration, and deterministic safety policy execution.

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Validation Suite](https://img.shields.io/badge/Validation-13%2F13_Passed-brightgreen.svg)](#validation--testing)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)

`wiz-central-toolkit` is a production-grade suite of 12 developer utilities that run locally with minimal overhead and deterministic output. Designed to operate standalone as individual CLI binaries or orchestrated through **GodfatherWiz** and **Wiz**, every tool in this repository is fully functional, disk-verified, and CI-tested.

---

## 🌟 Fleet Inventory & Command Mapping

All 12 wizard modules on disk are active, registered, and disk-verified:

| Wizard Module | Direct Executable | Central Alias | Primary Functionality & Subcommands |
| :--- | :--- | :--- | :--- |
| **`wiz`** | `wiz` | `wiz` | Central dispatcher & alias router (`banner`, `codeguard`, `debug`, `diff`, `json`, `python`, `read`, `rust`, `tmux`, `todo`, `write`) |
| **`godfatherwiz`** | `godfatherwiz` | `godfatherwiz` | Grand Master fleet supervisor, deterministic task routing, and interactive REPL cockpit |
| **`codeguardwiz`** | `codeguardwiz` | `wiz codeguard` | Static security scanner (`audit`, `fix`, `lang`, `roster`, `scan`, `watch`, `severity`, `explain`, `scaffold`) |
| **`debugwiz`** | `debugwiz` | `wiz debug` | Diagnosis oracle (`trace`, `locate`, `classify`, `hotspot`, `timeline`, `imports`, `suggest`, `audit`, `report`) |
| **`diffwiz`** | `diffwiz` | `wiz diff` | Change-truth doctor (`files`, `dirs`, `context`, `summary`, `word`, `same`, `reverse`) |
| **`jsonwiz`** | `jsonwiz` | `wiz json` | Standalone JSON doctor (`validate`, `pretty`, `compact`, `inspect`, `keys`, `get`, `diff`, `stats`, `merge`) |
| **`pythonwiz`** | `pythonwiz` | `wiz python` | Standalone Python parser & health auditor (`check`, `outline`, `imports`, `complexity`, `loc`, `secrets`, `score`) |
| **`readwiz`** | `readwiz` | `wiz read` | Read-only policy verb gate (`check`, `verbs`, `law`) |
| **`rustwiz`** | `rustwiz` | `wiz rust` | Rust project syntax & build checker (`check`, `build`) |
| **`tmuxwiz`** | `tmuxwiz` | `wiz tmux` | Sovereign tmux session manager (`new`, `attach`, `kill`, `list`, `census`, `rename`) |
| **`todowiz`** | `todowiz` | `wiz todo` | Task management wizard (`add`, `list`, `done`, `undo`, `note`, `oldest`, `overdue`, `stats`, `export`) |
| **`writewiz`** | `writewiz` | `wiz write` | Consent wall for file writes (`propose`, `preview`, `commit`, `verify`, `rollback`, `protect`, `backups`) |

---

## 🛠 Usage Examples

### 1. Central Router (`wiz` / `godfatherwiz`)
Execute sub-tools via `wiz` or inspect fleet state with `godfatherwiz`:
```bash
# Execute sub-tools via alias
wiz todo add "Refactor logger module"
wiz json validate config.json

# GodfatherWiz fleet supervision
godfatherwiz census
godfatherwiz status
godfatherwiz repl
