# python-wizard — "the fleet gate"

## Purpose
The AST syntax doctor for Python files and whole trees. Nothing enters or leaves the fleet without passing this gate.

## Commands
- `pythonwiz check <file.py>` — compile-check a single file, errors verbatim
- `pythonwiz check <dir>` — sweep every .py under a directory (skips .venv, .git, __pycache__)
- Legacy alias: `pywiz`

## Verdicts
[OK] per clean file; [FAIL] with verbatim error text (file:line); `out of scope` for non-Python targets. Exit codes 0/1/2.

## Fleet Role
THE gate of the fleet — Law VI. Certifies all fleet code before it walks: bootwiz certification trials, forge runs in mode-manifesting-wizard, every REPL graft, and the estate keeper's post-graft checks all route through this gate. An [OK] means "compiles", not "correct" — mission-fidelity judgment belongs to benchwiz/probewiz exams and the human lane.

## Laws Kept
Stateless and mortal; stdlib ast/compile only; no filesystem writes.
