"""read-wizard brain — the read-only policy engine.

READ LAW:
  This wizard judges, it never acts. Given a raw shell command,
  it answers ALLOW / DENIED / out of scope. Its tables are the
  single source of truth for read-only mode in every REPL that
  binds it. Mortal and stateless: one verdict per invocation.
"""

import shlex

# ------------------------------------------------------------------
# THE VERB TABLES — the law itself. Amend only by Governor decree.
# ------------------------------------------------------------------

ALLOW_VERBS = frozenset({
    # observation
    "ls", "ll", "la", "cat", "head", "tail", "less", "more", "wc",
    "file", "stat", "du", "df", "tree", "find", "locate", "which",
    "whereis", "type", "echo", "date", "whoami", "hostname", "pwd",
    "uname", "uptime", "env", "printenv", "id", "groups", "history",
    # search
    "grep", "rg", "fgrep", "ag", "awk", "cut", "sort", "uniq", "nl",
    "column", "strings",
    # fleet read-only citizens — other wizards ARE read verbs
    "helpwiz", "pythonwiz", "diffwiz", "jsonwiz", "cmdwiz", "manualwiz",
    "gitwiz", "mapwiz",   # Governor decree 2026-09-18 — newborn inspectors admitted
    "gitwiz", "mapwiz",   # Governor decree 2026-09-18 — newborn inspectors admitted
    "truthwiz", "ollamawiz", "probewiz", "rustwiz", "readwiz",
    "benchwiz", "modelfilewiz",  # exam/show/hash/verify/list only
    # introspection
    "jq", "git",          # git gated separately (see GIT_DENY_SUBS)
    "python3",             # gated: only with -c check or read scripts
})

# git subverbs that mutate — git itself is allowed, these are not
GIT_DENY_SUBS = frozenset({
    "push", "commit", "add", "reset", "checkout", "merge", "rebase",
    "cherry-pick", "stash", "clean", "rm", "mv", "apply", "tag",
    "restore", "switch", "worktree",
})

# absolute denies — anything touching these dies regardless of position
DENY_VERBS = frozenset({
    "rm", "rmdir", "mv", "cp", "ln", "touch", "mkdir", "tee", "truncate",
    "dd", "shred", "chmod", "chown", "chattr", "setfacl", "install",
    "kill", "pkill", "shutdown", "reboot", "poweroff", "systemctl",
    "service", "crontab", "useradd", "userdel", "passwd", "sudo", "su",
    "doas", "mount", "umount", "umount", "mkfs", "pip", "pip3", "apt",
    "apt-get", "snap", "npm", "curl", "wget", "scp", "rsync", "ssh",
    "sftp", "nc", "socat", "bootwiz",  # birthing citizens is Tier 2
})

# raw-string tokens that mean writing no matter which verb fronts them
WRITE_MARKERS = (">>", ">", "$(", "`")


def _first_verb(segment):
    """Peel the first word of one pipe-segment, tolerating quoting."""
    try:
        words = shlex.split(segment)
    except ValueError:
        return None
    words = [w for w in words if w and w != "sudo"]
    return words[0] if words else None


def check_command(raw):
    """Judge one raw shell line. Returns (verdict, reason).

    verdict: 'ALLOW' | 'DENIED'
    """
    if not raw or not raw.strip():
        return "DENIED", "empty command"
    raw = raw.strip()

    # stage 1 — write markers anywhere in the raw line
    for marker in WRITE_MARKERS:
        if marker in raw:
            return "DENIED", f"write marker '{marker}' present"

    # stage 2 — judge every segment of every pipe
    for segment in raw.split("|"):
        seg = segment.strip()
        if not seg:
            continue
        verb = _first_verb(seg)
        if verb is None:
            return "DENIED", "unparseable segment"
        # peel path prefixes: /usr/bin/grep -> grep
        verb_clean = verb.rsplit("/", 1)[-1]

        if verb_clean in DENY_VERBS:
            return "DENIED", f"verb '{verb_clean}' is a write/mutate verb"
        if verb_clean not in ALLOW_VERBS:
            return "DENIED", f"verb '{verb_clean}' not on the read allowlist"

        # git subverb gate
        if verb_clean in ("git", "/usr/bin/git"):
            try:
                words = shlex.split(seg)
            except ValueError:
                return "DENIED", "unparseable git command"
            subs = [w for w in words[1:] if not w.startswith("-")]
            if subs and subs[0] in GIT_DENY_SUBS:
                return "DENIED", f"git subverb '{subs[0]}' mutates state"

    return "ALLOW", "read-only"


# ---------------- charter text ----------------

LAW_TEXT = """READ LAW (read-wizard, the verb gate)
1. readwiz judges; it never executes. REPLs bind it as policy engine.
2. ALLOW means read-only: observation, search, fleet read-only citizens.
3. Redirection (>, >>), substitution ($(), `) and every write verb: DENIED.
4. Unknown verbs default DENIED — absence from the table is not permission.
5. git is read-only ONLY for its observing subverbs (status, log, diff, show...).
6. Tables amend only by Governor decree, witnessed by commit.
7. Mortal and stateless: one verdict, then death. No memory of commands seen.
"""
