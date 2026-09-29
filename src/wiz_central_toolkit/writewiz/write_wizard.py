"""write-wizard brain — the consent wall for every file write.

WRITE LAW:
  Nothing reaches disk except through 'commit', and commit is
  opened only by a literal 'y' typed by a live human at the
  terminal. There is no --yes. There is no --force. There is no
  batch mode. Proposals wait in quarantine until the Governor speaks.
  After every write, disk state is re-read and compared — a write
  without verification is a claim, not a fact.
  Every overwriting commit saves a backup first, and every wall
  event is journaled. Protected paths refuse writes absolutely.
"""

import datetime as dt
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

HOME = Path.home()
BANK = HOME / ".write-wizard"
QUARANTINE = BANK / "pending"
BACKUPS = BANK / "backups"
LEDGER = BANK / "ledger.jsonl"
PROTECTED = BANK / "protected.json"


def _ensure_quarantine():
    QUARANTINE.mkdir(parents=True, exist_ok=True)
    BACKUPS.mkdir(parents=True, exist_ok=True)
    if not PROTECTED.exists():
        PROTECTED.write_text("[]")


def _draft_path(target: Path) -> tuple[Path, Path]:
    """Deterministic draft slot for a target path (survives slashes)."""
    ident = hashlib.sha256(str(target).encode()).hexdigest()[:16]
    meta = QUARANTINE / (ident + ".meta")
    return QUARANTINE / (ident + ".draft"), meta


def _now() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def journal(event: str, target: Path, detail: str = "") -> None:
    """Append-only write journal. The wall remembers everything."""
    row = {"at": _now(), "event": event, "target": str(target), "detail": detail}
    _ensure_quarantine()
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True) + "\n")


def ledger_rows() -> list:
    if not LEDGER.exists():
        return []
    rows = []
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            rows.append({"at": "?", "event": "CORRUPT_ROW", "target": line, "detail": ""})
    return rows


def load_protected() -> list:
    _ensure_quarantine()
    try:
        return json.loads(PROTECTED.read_text())
    except (json.JSONDecodeError, OSError):
        return []


def is_protected(target: Path) -> bool:
    prot = load_protected()
    return str(target) in prot or str(target.resolve()) in prot


def protect(target_str: str) -> dict:
    target = Path(target_str).expanduser().resolve()
    prot = load_protected()
    if str(target) in prot:
        return {"ok": False, "error": f"already protected: {target}"}
    prot.append(str(target))
    PROTECTED.write_text(json.dumps(prot, indent=2))
    journal("PROTECT", target)
    return {"ok": True, "protected": str(target)}


def unprotect(target_str: str) -> dict:
    target = Path(target_str).expanduser().resolve()
    prot = load_protected()
    if str(target) not in prot:
        return {"ok": False, "error": f"not protected: {target}"}
    prot.remove(str(target))
    PROTECTED.write_text(json.dumps(prot, indent=2))
    journal("UNPROTECT", target)
    return {"ok": True, "unprotected": str(target)}


def propose(target_str: str, content: str):
    """Stage proposed content in quarantine. Touches nothing real."""
    target = Path(target_str).expanduser()
    _ensure_quarantine()
    draft, meta = _draft_path(target)
    draft.write_text(content, encoding="utf-8")
    meta.write_text(str(target), encoding="utf-8")
    return draft, meta, target


def gate_and_diff(draft: Path, target: Path):
    """Run the pythonwiz gate on .py drafts, then diff vs disk truth.

    Returns (report_lines, hard_fail). hard_fail -> commit MUST refuse.
    """
    report, hard_fail = [], False
    existed = target.exists()

    # gate 1 — syntax (python only)
    if str(target).endswith(".py"):
        r = subprocess.run(
            ["pythonwiz", "check", str(draft)],
            capture_output=True, text=True, timeout=60)
        report.append(r.stdout.strip() or r.stderr.strip())
        if r.returncode != 0:
            hard_fail = True
            report.append("[FAIL] syntax gate refused — commit blocked")
    else:
        report.append("[OK] non-python target: syntax gate waived")

    # gate 2 — diff against reality
    if existed:
        r = subprocess.run(
            ["diffwiz", "files", str(target), str(draft)],
            capture_output=True, text=True, timeout=60)
        report.append("--- diff (disk -> proposed) ---")
        report.append(r.stdout.strip() or "(no textual differences)")
        if r.returncode == 0:
            report.append("[NOTE] proposal is identical to disk truth")
    else:
        report.append(f"[NOTE] new file: {target} does not exist yet")
        try:
            head = draft.read_text(encoding="utf-8", errors="replace")[:800]
            report.append("--- proposed (first 800 chars) ---")
            report.append(head)
        except OSError as e:
            hard_fail = True
            report.append(f"[FAIL] cannot read draft: {e}")
    return report, hard_fail


def explain(target_str: str) -> dict:
    """Answer: if the Governor said 'y' right now, would it write?"""
    target = Path(target_str).expanduser()
    draft, meta = _draft_path(target)
    if not draft.exists():
        return {"ok": False, "error": "no quarantined draft"}
    verdict: dict[str, Any] = {"ok": True, "target": str(target),
               "draft_bytes": draft.stat().st_size,
               "would_write": True, "reasons": []}
    if is_protected(target):
        verdict["would_write"] = False
        verdict["reasons"].append("path is PROTECTED — absolute refusal")
    _, hard_fail = gate_and_diff(draft, target)
    if hard_fail:
        verdict["would_write"] = False
        verdict["reasons"].append("syntax gate hard-fail")
    if target.exists():
        verdict["reasons"].append("existing file — backup will be saved first")
    else:
        verdict["reasons"].append("new file — no backup needed")
    return verdict


def _backup_of(target: Path) -> Path:
    ident = hashlib.sha256(str(target).encode()).hexdigest()[:16]
    return BACKUPS / (ident + ".bak")


def backup_target(target: Path) -> bool:
    """Safety copy of current disk content before an overwriting write."""
    if not target.exists() or not target.is_file():
        return False
    bak = _backup_of(target)
    shutil.copy2(target, bak)
    return True


def rollback(target_str: str, confirm_reader=None) -> tuple:
    """Restore a target from its pre-write backup. 'y'-gated, journaled."""
    target = Path(target_str).expanduser()
    bak = _backup_of(target)
    if not bak.exists():
        journal("ROLLBACK_REFUSED", target, "no backup")
        return False, f"[FAIL] no backup exists for {target}", target
    ask = confirm_reader or input
    try:
        answer = ask("GOVERNOR CONSENT — roll back %s to backup? [y/N] " % target).strip().lower()
    except EOFError:
        journal("ROLLBACK_REFUSED", target, "EOF is not consent")
        return False, "consent withheld — EOF is not 'y', the wall holds", target
    if answer != "y":
        journal("ROLLBACK_REFUSED", target, "declined")
        return False, "consent withheld — backup untouched", target
    try:
        content = bak.read_text(encoding="utf-8")
        target.write_text(content, encoding="utf-8")
    except OSError as e:
        journal("ROLLBACK_FAILED", target, str(e))
        return False, f"[FAIL] rollback write refused: {e}", target
    on_disk = target.read_text(encoding="utf-8", errors="replace")
    if on_disk == content:
        journal("ROLLBACK_OK", target)
        return True, "[OK] rolled back and verified on disk", target
    journal("ROLLBACK_FAILED", target, "post-write mismatch")
    return False, "[FAIL] disk differs from backup after rollback — investigate", target


def discard(target_str: str, confirm_reader=None) -> tuple:
    """Burn a quarantined draft. 'y'-gated, journaled, evidence recorded."""
    target = Path(target_str).expanduser()
    draft, meta = _draft_path(target)
    if not draft.exists():
        return False, f"[FAIL] no quarantined draft for {target_str}", target
    ask = confirm_reader or input
    try:
        answer = ask("GOVERNOR CONSENT — burn draft for %s ? [y/N] " % target).strip().lower()
    except EOFError:
        journal("DISCARD_REFUSED", target, "EOF is not consent")
        return False, "consent withheld — EOF is not 'y', the wall holds", target
    if answer != "y":
        journal("DISCARD_REFUSED", target, "declined")
        return False, "consent withheld — draft stays quarantined", target
    size = draft.stat().st_size
    draft.unlink(missing_ok=True)
    meta.unlink(missing_ok=True)
    journal("DISCARDED", target, f"{size} bytes burned")
    return True, f"[OK] draft burned ({size} bytes) — journaled, not forgotten", target


def guard_sweep() -> list:
    """Run the pythonwiz gate over every pending draft. Read-only."""
    _ensure_quarantine()
    rows = []
    for draft in sorted(QUARANTINE.glob("*.draft")):
        meta = draft.with_suffix(".meta")
        target = Path(meta.read_text(encoding="utf-8").strip()) if meta.exists() else None
        row = {"draft": draft.name, "target": str(target) if target else "?"}
        if target and str(target).endswith(".py"):
            r = subprocess.run(
                ["pythonwiz", "check", str(draft)],
                capture_output=True, text=True, timeout=60)
            row["gate"] = "PASS" if r.returncode == 0 else "FAIL"
        else:
            row["gate"] = "waived"
        rows.append(row)
    return rows


def audit_quarantine() -> dict:
    _ensure_quarantine()
    drafts = list(QUARANTINE.glob("*.draft"))
    metas = list(QUARANTINE.glob("*.meta"))
    draft_ids = {d.stem for d in drafts}
    meta_ids = {m.stem for m in metas}
    orphans = [str(QUARANTINE / (i + ".draft")) for i in draft_ids - meta_ids]
    ghosts = [str(QUARANTINE / (i + ".meta")) for i in meta_ids - draft_ids]
    oldest = min((d.stat().st_mtime for d in drafts), default=None)
    return {"drafts": len(drafts), "orphans": orphans, "ghosts": ghosts,
            "oldest": dt.datetime.fromtimestamp(oldest).isoformat(timespec="seconds") if oldest else None}


def purge_old(days: int, confirm_reader=None) -> tuple:
    """Burn drafts older than N days. 'y'-gated, journaled."""
    import time
    _ensure_quarantine()
    cutoff = time.time() - days * 86400
    aged = [d for d in QUARANTINE.glob("*.draft") if d.stat().st_mtime < cutoff]
    if not aged:
        return True, f"[OK] no drafts older than {days} days", Path("none")
    ask = confirm_reader or input
    try:
        answer = ask(f"GOVERNOR CONSENT — burn {len(aged)} draft(s) older than {days} days? [y/N] ").strip().lower()
    except EOFError:
        return False, "consent withheld — EOF is not 'y', the wall holds", Path("none")
    if answer != "y":
        return False, "consent withheld — nothing burned", Path("none")
    for d in aged:
        meta = d.with_suffix(".meta")
        target = meta.read_text(encoding="utf-8").strip() if meta.exists() else "?"
        journal("PURGED", Path(target), f"{d.name} older than {days} days")
        d.unlink(missing_ok=True)
        meta.unlink(missing_ok=True)
    return True, f"[OK] burned {len(aged)} aged draft(s) — journaled", Path("none")


def stats() -> dict:
    counts: dict[str, int] = {}
    for row in ledger_rows():
        counts[row["event"]] = counts.get(row["event"], 0) + 1
    _ensure_quarantine()
    drafts = len(list(QUARANTINE.glob("*.draft")))
    backups = len(list(BACKUPS.glob("*.bak")))
    return {"events": counts, "pending_drafts": drafts,
            "backups": backups, "protected": len(load_protected())}


def law_digest() -> dict:
    return {
        "law_sha256": hashlib.sha256(LAW_TEXT.encode()).hexdigest(),
        "law_chars": len(LAW_TEXT),
        "law_lines": len(LAW_TEXT.splitlines()),
    }


def commit(draft: Path, meta: Path, confirm_reader=None):
    """The wall. confirm_reader is injectable for testing ONLY.

    In production the REPL supplies nothing — input() asks a live human.
    There is no path around the prompt.
    """
    target = Path(meta.read_text(encoding="utf-8").strip()).expanduser()

    # Law 11 enforced INSIDE the wall — protected paths refuse absolutely
    if is_protected(target):
        journal("COMMIT_REFUSED", target, "path is PROTECTED")
        return False, "[FAIL] path is PROTECTED — the wall refuses absolutely", target

    # Law 5 enforced INSIDE the wall — the gate runs here, not in trust
    report, hard_fail = gate_and_diff(draft, target)
    for line in report:
        print(line)
    if hard_fail:
        journal("COMMIT_REFUSED", target, "syntax gate hard-fail")
        return False, "[FAIL] syntax gate refused — commit blocked without asking", target

    ask = confirm_reader or input
    try:
        answer = ask("GOVERNOR CONSENT — write to %s ? [y/N] " % target).strip().lower()
    except EOFError:
        journal("COMMIT_REFUSED", target, "EOF is not consent")
        return False, "consent withheld — EOF is not 'y', the wall holds", target
    if answer != "y":
        journal("COMMIT_REFUSED", target, "declined")
        return False, "consent withheld — draft stays quarantined", target

    # Law 9 — safety backup before any overwriting write
    if backup_target(target):
        journal("BACKUP_SAVED", target)

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        content = draft.read_text(encoding="utf-8")
        target.write_text(content, encoding="utf-8")
    except OSError as e:
        journal("COMMIT_FAILED", target, str(e))
        return False, f"[FAIL] write refused: {e}", target

    # verification — re-read disk and compare (claims are not facts)
    on_disk = target.read_text(encoding="utf-8", errors="replace")
    if on_disk == content:
        draft.unlink(missing_ok=True)
        meta.unlink(missing_ok=True)
        journal("COMMITTED", target)
        return True, "[OK] written and verified on disk", target
    journal("COMMIT_FAILED", target, "post-write mismatch")
    return False, "[FAIL] disk differs from draft after write — investigate", target


LAW_TEXT = """WRITE LAW (write-wizard, the consent wall)
1. propose stages content in ~/.write-wizard/pending — disk untouched.
2. preview runs the pythonwiz gate and diffwiz against disk truth.
3. commit opens ONLY on a literal 'y' typed live by the Governor.
4. No --yes. No --force. No batch. No env var. No exception.
5. A failing syntax gate is a hard fail: commit MUST refuse.
6. Every write is re-read from disk; unequal bytes = reported FAIL.
7. Drafts survive refusal — quarantine keeps evidence, never destroys it.
8. Tables and laws amend only by Governor decree, witnessed by commit.
9. Every overwriting commit saves a backup first: rollback is a right.
10. Every wall event — commit, refusal, burn, rollback — is journaled.
11. Protected paths refuse writes absolutely, past any consent.
"""