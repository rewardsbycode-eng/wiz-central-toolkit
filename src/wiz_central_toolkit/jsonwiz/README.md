# json-wizard — "the JSON inspector"

## Purpose
Validation and key-inspection for JSON files. Honest verdicts on structure, no more.

## Commands
- `jsonwiz validate <file.json>` — parse and report validity, errors verbatim
- `jsonwiz keys <file.json>` — list top-level keys of parsed JSON

## Verdicts
[OK] on valid JSON; [FAIL] on invalid JSON with error position; `out of scope` for non-JSON targets. Exit codes 0/1/2.

## Fleet Role
The JSON lane of the fleet gate — mode specs, census reports, and REPL session archives all pass through jsonwiz for structural truth before consumption.

## Laws Kept
Stateless and mortal; stdlib json only; no filesystem writes.
