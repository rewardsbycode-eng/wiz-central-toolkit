"""todo-wizard CLI front-end."""
import sys
import json
from .lib.todo_wizard import TodoWizard

def main() -> int:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("todowiz - standalone todo wizard")
        print("usage: todowiz <command> [args]")
        print("  add <text>            add a task (default priority normal)")
        print("  list                  list all tasks")
        print("  done <id>            complete a task")
        print("  undo <id>            reopen a completed task")
        print("  note <id> <text>     append a progress note to a task")
        print("  oldest               show the stalest pending task")
        print("  overdue [days]       pending tasks older than N days (default 7)")
        print("  archive-done         move completed tasks to archive")
        print("  rm <id>              remove a task")
        print("  stats                JSON summary")
        print("  export               full JSON dump")
        return 0

    wiz = TodoWizard()
    cmd = args[0]

    if cmd == "add":
        text = " ".join(args[1:]) or "untitled"
        item = wiz.add(text)
        print(f"[+] #{item['id']} {item['text']}")
    elif cmd == "list":
        for t in wiz.list_todos():
            mark = "x" if t["done"] else " "
            n_notes = len(t.get("notes", []))
            suffix = f" [{n_notes} notes]" if n_notes else ""
            print(f"[{mark}] #{t['id']} ({t['priority']}) {t['text']}{suffix}")
    elif cmd == "done":
        ok = wiz.complete(int(args[1]))
        print("[OK] completed" if ok else "[FAIL] not found or already done")
        return 0 if ok else 1
    elif cmd == "undo":
        ok = wiz.undo_complete(int(args[1]))
        print("[OK] reopened" if ok else "[FAIL] not found or not done")
        return 0 if ok else 1
    elif cmd == "note":
        if len(args) < 3:
            print("out of scope - note requires id and text")
            return 2
        ok = wiz.note(int(args[1]), " ".join(args[2:]))
        print("[OK] noted" if ok else "[FAIL] no such task")
        return 0 if ok else 1
    elif cmd == "oldest":
        t = wiz.oldest()
        if t is None:
            print("no pending tasks")
        else:
            print(f"#{t['id']} {t['text']} (created {t['created']})")
    elif cmd == "overdue":
        days = int(args[1]) if len(args) > 1 else 7
        results = wiz.overdue(days)
        if not results:
            print(f"no pending tasks older than {days} days")
        else:
            for t, age in results:
                print(f"#{t['id']} {t['text']} — {age:.1f} days old (created {t['created']})")
        return 1 if results else 0
    elif cmd == "archive-done":
        moved = wiz.archive_done()
        print("[OK] archived %d completed tasks" % moved if moved else "no completed tasks to archive")
    elif cmd == "rm":
        ok = wiz.remove(int(args[1]))
        print("[OK] removed" if ok else "[FAIL] not found")
        return 0 if ok else 1
    elif cmd == "stats":
        print(json.dumps(wiz.stats()))
    elif cmd == "export":
        print(json.dumps(wiz.list_todos(), indent=2))
    else:
        print("out of scope")
        return 2
    return 0
