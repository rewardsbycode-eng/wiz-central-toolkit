# todo-wizard — "the task ledger"

## Purpose
Simple, honest task storage and querying. One file lane per home: ~/.todo-wizard.

## Commands
- `todowiz add "<task>"` — record a task
- `todowiz list` — list tasks with done/open state
- `todowiz done <id>` — mark a task complete (tolerant of duplicate completion)
- `todowiz stats` — JSON summary of task state

## Verdicts
[OK] on success; [FAIL] on missing task/store; `out of scope` beyond task storage. Exit codes 0/1/2.

## Fleet Role
Personal task lane; distinct from whiteboardwiz (which serves task ledger + skill-ratification for the fleet's governance) — todowiz is the lightweight daily pocket.

## Laws Kept
Stateless and mortal; stdlib only; writes only to ~/.todo-wizard.
