# diff-wizard — "the honest differ"

## Purpose
Unified diffs between files and directory trees, with fleet-aware filtering. The truth lane for what changed.

## Commands
- `diffwiz files <a> <b>` — unified diff between two text files
- `diffwiz dirs <a> <b>` — recursive tree diff, skipping SKIP_DIRS (.venv, .git, __pycache__, node_modules)

## Verdicts
[OK] on identical/clean diff; [FAIL] on differences (diff text shown) or missing targets; `out of scope` for non-text targets. Exit codes 0/1/2.

## Fleet Role
Consent-wall partner: displays the unified diff before any patch lands in micro_runners' Auto-Writer and ollama_squad's architect. No write lane, ever.

## Laws Kept
Stateless and mortal; stdlib difflib; no filesystem writes.
