# rust-wizard — "the honest Rust validator"

## Purpose
Syntax and build validation for Rust code with compiler errors reported verbatim — never paraphrased, never softened. The pythonwiz doctrine applied to the Rust lane.

## Commands
- `rustwiz check <file.rs>` — compile-check one file, errors verbatim
- `rustwiz check <dir>` — sweep every .rs file under a directory
- `rustwiz build` — run `cargo check` on the current crate

## Verdicts
[OK] per clean file; [FAIL] with verbatim rustc error text; `out of scope` for non-Rust targets. Exit codes 0/1/2.

## Fleet Role
The Rust lane of the fleet gate. Serves any project needing Rust validation; counterpart to pythonwiz for Python.

## Laws Kept
Stateless and mortal; relies on host rustc/cargo toolchain (rustc 1.93.1 on msi); no tracebacks, ever.
