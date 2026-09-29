"""write-wizard face — thin CLI over the consent wall."""

import json
import sys

from .write_wizard import (
    LAW_TEXT, propose, gate_and_diff, commit, _draft_path, _ensure_quarantine,
    discard, rollback, guard_sweep, audit_quarantine, purge_old, stats,
    ledger_rows, explain, protect, unprotect, load_protected, law_digest,
    BACKUPS, QUARANTINE)

USAGE = """writewiz - the consent wall for file writes
usage: writewiz propose <path>        stage content (reads stdin) in quarantine
       writewiz preview <path>        gate + diff the staged draft vs disk
       writewiz commit <path>         ask Governor consent, write, verify
       writewiz pending               list quarantined drafts
       writewiz law                   print the WRITE LAW alone
       writewiz status <path>         draft state: bytes, age, target
       writewiz diff <path>           disk vs draft diff alone
       writewiz verify <path>         gate + verification, zero consent
       writewiz explain <path>        would-commit verdict with reasons
       writewiz discard <path>        burn a draft ('y'-gated, journaled)
       writewiz guard                 gate sweep over every pending draft
       writewiz audit                 quarantine census: drafts, orphans
       writewiz ledger                full write journal
       writewiz history <path>        journal filtered to one target
       writewiz stats                 counts: staged, written, refused
       writewiz protect <path>        forbid writes — absolute refusal
       writewiz unprotect <path>      lift a protection (Governor only)
       writewiz protected             list protected paths
       writewiz backups               list pre-write safety copies
       writewiz rollback <path>       restore from backup ('y'-gated)
       writewiz purge-old <days>      burn drafts older than N days ('y'-gated)
       writewiz law-digest            sha256 of WRITE LAW (drift detection)
exit codes: 0 ok | 1 refused/failed | 2 usage error"""

CMDS = ("propose", "preview", "commit", "pending", "law", "status", "diff",
        "verify", "explain", "discard", "guard", "audit", "ledger", "history",
        "stats", "protect", "unprotect", "protected", "backups", "rollback",
        "purge-old", "law-digest")


def _load(target_str):
    from pathlib import Path
    _ensure_quarantine()
    draft, meta = _draft_path(Path(target_str).expanduser())
    if not draft.exists() or not meta.exists():
        print(f"[FAIL] no quarantined draft for {target_str} — propose first")
        return None
    return draft, meta


def main(argv=None):
    import datetime as dt
    from pathlib import Path

    args = sys.argv[1:] if argv is None else list(argv)
    if args and args[0] in ("-h", "--help"):
        print(USAGE)
        return 0
    if not args or args[0] not in CMDS:
        print(USAGE)
        return 2

    cmd = args[0]

    if cmd == "law":
        print(LAW_TEXT)
        return 0
    if cmd == "law-digest":
        print(json.dumps(law_digest(), indent=2))
        return 0

    if cmd == "pending":
        _ensure_quarantine()
        drafts = sorted(QUARANTINE.glob("*.draft"))
        if not drafts:
            print("(quarantine empty)")
            return 0
        for d in drafts:
            meta = d.with_suffix(".meta")
            target = meta.read_text(encoding="utf-8") if meta.exists() else "?"
            print(f"  {d.name}  ->  {target}")
        return 0
    if cmd == "guard":
        rows = guard_sweep()
        if not rows:
            print("(quarantine empty)")
            return 0
        rc = 0
        for row in rows:
            mark = "[OK]" if row["gate"] in ("PASS", "waived") else "[FAIL]"
            if row["gate"] == "FAIL":
                rc = 1
            print(f"{mark} {row['draft']} gate={row['gate']} -> {row['target']}")
        return rc
    if cmd == "audit":
        r = audit_quarantine()
        print(f"drafts={r['drafts']} orphans={len(r['orphans'])} "
              f"ghosts={len(r['ghosts'])} oldest={r['oldest'] or 'never'}")
        for o in r["orphans"]:
            print(f"[ORPHAN] {o}")
        for g in r["ghosts"]:
            print(f"[GHOST] {g}")
        return 1 if (r["orphans"] or r["ghosts"]) else 0
    if cmd == "ledger":
        rows = ledger_rows()
        if not rows:
            print("(ledger empty — no wall events yet)")
            return 0
        for row in rows:
            print(f"{row['at']}  {row['event']:16s} {row['target']} {row['detail']}")
        return 0
    if cmd == "stats":
        print(json.dumps(stats(), indent=2))
        return 0
    if cmd == "protected":
        prot = load_protected()
        if not prot:
            print("(no protected paths)")
            return 0
        for p in prot:
            print(f"[SHIELD] {p}")
        return 0
    if cmd == "backups":
        _ensure_quarantine()
        baks = sorted(BACKUPS.glob("*.bak"))
        if not baks:
            print("(no backups — nothing has been overwritten yet)")
            return 0
        for b in baks:
            print(f"[BAK] {b.name} ({b.stat().st_size} bytes, "
                  f"{dt.datetime.fromtimestamp(b.stat().st_mtime).isoformat(timespec='seconds')})")
        return 0

    if cmd in ("protect", "unprotect") :
        if len(args) < 2:
            print("[FAIL] requires a path")
            return 2
        r = protect(args[1]) if cmd == "protect" else unprotect(args[1])
        if r["ok"]:
            print(f"[OK] {cmd}ed: {list(r.values())[1]}")
            return 0
        print(f"[FAIL] {r['error']}")
        return 1

    if cmd == "purge-old":
        if len(args) < 2:
            print("[FAIL] purge-old requires a number of days")
            return 2
        ok, msg, _ = purge_old(int(args[1]))
        print(msg)
        return 0 if ok else 1

    # --- path-taking commands ---
    if len(args) < 2:
        print(f"[FAIL] writewiz {cmd} requires a path")
        return 2
    target_str = args[1]
    target = Path(target_str).expanduser()

    if cmd == "propose":
        content = sys.stdin.read()
        draft, meta, t = propose(target_str, content)
        print(f"[OK] staged: {draft.name} -> {t} ({len(content)} chars quarantined)")
        return 0
    if cmd == "status":
        loaded = _load(target_str)
        if loaded is None:
            return 1
        draft, meta = loaded
        age = dt.datetime.now() - dt.datetime.fromtimestamp(draft.stat().st_mtime)
        print(f"target:   {meta.read_text(encoding='utf-8').strip()}")
        print(f"draft:    {draft.name}")
        print(f"bytes:    {draft.stat().st_size}")
        print(f"staged:   {age.seconds // 60} minutes ago")
        print(f"shielded: {'YES — writes refused' if (lambda tw: tw.resolve().as_posix() in [p for p in load_protected()] or str(tw) in load_protected())(target) else 'no'}")
        return 0
    if cmd == "diff":
        loaded = _load(target_str)
        if loaded is None:
            return 1
        draft, meta = loaded
        report, hard_fail = gate_and_diff(draft, target)
        for line in report:
            print(line)
        return 1 if hard_fail else 0
    if cmd == "verify":
        loaded = _load(target_str)
        if loaded is None:
            return 1
        draft, meta = loaded
        if target.exists():
            on_disk = target.read_text(encoding="utf-8", errors="replace")
            draft_text = draft.read_text(encoding="utf-8", errors="replace")
            print("[OK] draft matches disk" if on_disk == draft_text
                  else "[FAIL] draft differs from disk")
            return 0 if on_disk == draft_text else 1
        print("[NOTE] target does not exist yet — new file")
        return 0
    if cmd == "explain":
        r = explain(target_str)
        if not r["ok"]:
            print(f"[FAIL] {r['error']}")
            return 1
        verdict = "WOULD WRITE" if r["would_write"] else "WOULD REFUSE"
        print(f"[{verdict}] {r['target']} ({r['draft_bytes']} bytes staged)")
        for reason in r["reasons"]:
            print(f"  - {reason}")
        return 0
    if cmd == "preview":
        loaded = _load(target_str)
        if loaded is None:
            return 1
        draft, meta = loaded
        report, hard_fail = gate_and_diff(draft, target)
        for line in report:
            print(line)
        return 1 if hard_fail else 0
    if cmd == "commit":
        loaded = _load(target_str)
        if loaded is None:
            return 1
        draft, meta = loaded
        ok, msg, t = commit(draft, meta)
        print(msg)
        return 0 if ok else 1
    if cmd == "history":
        rows = [r for r in ledger_rows() if target.as_posix() in r["target"]]
        if not rows:
            print(f"(no journal entries for {target_str})")
            return 0
        for row in rows:
            print(f"{row['at']}  {row['event']:16s} {row['detail']}")
        return 0
    if cmd == "discard":
        ok, msg, t = discard(target_str)
        print(msg)
        return 0 if ok else 1
    if cmd == "rollback":
        ok, msg, t = rollback(target_str)
        print(msg)
        return 0 if ok else 1

    print(USAGE)
    return 2