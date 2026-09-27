# commandline-wizard — "the fleet auditor"

## Purpose
The fleet's auditor and truth-witness. Runs live health censuses across all citizens, scans shell history for dangerous patterns, and audits archived model sessions for honesty.

## Commands
- `cmdwiz run census` — live health check: invoke every fleet CLI, verify availability and exit codes
- `cmdwiz history <file>` — scan shell history for dangerous commands (danger scan, for audit forensics)
- `cmdwiz sessions <dir>` — scan micro_runners JSON session archives for TOOL: requests and fabrication fingerprints; per-conversation honesty scores
- `cmdwiz history --help` — full usage

## Verdicts
[OK]/[FAIL] per check in census mode; [OK]/[FAIL]/out of scope; exit codes 0/1/2. No tracebacks, ever.

## Fleet Role
The fleet's doctor and forensic witness. Census receipts saved as timestamped reports in `reports/`. Proof-of-life ritual: `commandlinewiz run census`.

## Laws Kept
Stateless and mortal; stdlib only; reads histories and session archives, writes reports only.
