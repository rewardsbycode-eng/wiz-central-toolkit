# godfather-wizard

**Command:** `godfatherwiz` / alias `father` — **Citizen #33**

The Grand Master of the Sovereign Fleet: fleet dispatcher, REPL cockpit,
and single entry point that delegates every intent to certified sibling
citizens via shell calls (Delegation Law — never re-implements logic).

## CLI Commands (21 live, per USAGE block in lib/cli.py)

| Command | Purpose |
|---|---|
| audit <path> | chain truthwiz + manualwiz census |
| task <intent> | chain todowiz + whiteboardwiz |
| run <directive> | deterministic keyword router |
| routes | print routing table |
| fleet | bin-lane census |
| law | print FATHER LAW |
| truth <path> | anchor ground truth |
| diagnose <dir> | debugwiz audit + triage |
| heal <file> | repairwiz ladder → writewiz commit |
| status | fleet-wide health check |
| repl | launch interactive REPL cockpit |
| siblings | list all registered citizens |
| verify <wizard> | single citizen health check |
| consent <file> | force writewiz commit prompt |
| schedule <intent> | queue task |
| queue | show scheduled tasks |
| history | run history across delegations |
| stats | fleet-wide execution counts |
| versions | law drift detection |
| help <command> | usage for one subcommand |
| census | full fleet roster |

## REPL Slash Commands

26 slash commands (see /help in REPL). All forward user arguments as
proper argv tokens.

## CAPACITY LAW

Target: 50 commands. Hard ceiling: 100 — no exceptions without a new
Governor ruling recorded in this README.

## Changelog

- **2026-09-23 — ARG LAW**: REPL previously split each pipeline with
  `.split()[0]`, discarding the subcommand and passing the user's whole
  argument string as ONE argv token (`/read FLEET-STATE.md` reached
  truthwiz as `truthwiz FLEET-STATE.md` → honest `out of scope`).
  Fix: full pipeline preserved, args split into argv tokens.
  Verified live: /read, /ls, /audit with arguments all honored.

Fleet manifest: [../README.md](../README.md)
