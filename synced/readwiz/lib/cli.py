"""read-wizard face — thin CLI over the policy brain."""

import sys

from lib.read_wizard import check_command, LAW_TEXT, ALLOW_VERBS, DENY_VERBS

USAGE = """readwiz - read-only mode policy engine (verb gate)
usage: readwiz check "<raw shell command>"
       readwiz verbs          dump the allow/deny tables
       readwiz law            print the READ LAW alone
verdicts: ALLOW / DENIED | exit 0 = allow, 1 = denied, 2 = usage error"""


def main():
    args = sys.argv[1:]
    if args and args[0] in ("-h", "--help"):
        print(USAGE)
        return 0
    if not args or args[0] not in ("check", "verbs", "law"):
        print(USAGE)
        return 2

    if args[0] == "law":
        print(LAW_TEXT)
        return 0

    if args[0] == "verbs":
        print("[ALLOW]")
        for v in sorted(ALLOW_VERBS):
            print(f"  {v}")
        print("[DENY]")
        for v in sorted(DENY_VERBS):
            print(f"  {v}")
        return 0

    # check mode
    if len(args) < 2:
        print("[FAIL] readwiz check requires a quoted command string")
        return 2

    verdict, reason = check_command(" ".join(args[1:]))
    if verdict == "ALLOW":
        print(f"[ALLOW] {reason}")
        return 0
    print(f"[DENIED] {reason}")
    return 1
