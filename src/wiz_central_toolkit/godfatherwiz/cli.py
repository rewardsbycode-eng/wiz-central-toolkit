"""godfather-wizard face — the Grand Master, fleet dispatcher & REPL."""

import json
import sys
import readline

from collections import Counter
from .lib.godfather_wizard import (
    FATHER_LAW, call_sibling, call_ollama, speak_if_enabled,
    truth_anchor, route_directive, fleet_census, load_routes,
    save_routes, journal, ledger_rows, _now, schedule_task,
    queue_tasks, render_banner, list_all_slash_commands,
    session_load, session_save)

USAGE = """godfatherwiz - the Grand Master, fleet dispatcher & REPL (Citizen #33)
usage: godfatherwiz <command> [args]

CLI Commands:
  godfatherwiz audit <path>       chain truthwiz + manualwiz census
  godfatherwiz task <intent>      chain todowiz + whiteboardwiz
  godfatherwiz run <directive>    deterministic keyword router
  godfatherwiz routes             print routing table
  godfatherwiz fleet              bin-lane census
  godfatherwiz law                print FATHER LAW
  godfatherwiz truth <path>       anchor ground truth
  godfatherwiz diagnose <dir>     debugwiz audit + triage
  godfatherwiz heal <file>        repairwiz ladder → writewiz commit
  godfatherwiz status             fleet-wide health check
  godfatherwiz repl               launch interactive REPL cockpit
  godfatherwiz siblings           list all registered citizens
  godfatherwiz verify <wizard>    single citizen health check
  godfatherwiz consent <file>     force writewiz commit prompt
  godfatherwiz schedule <intent>  queue task
  godfatherwiz queue              show scheduled tasks
  godfatherwiz history            run history across delegations
  godfatherwiz stats              fleet-wide execution counts
  godfatherwiz versions           law drift detection
  godfatherwiz help <command>     usage for one subcommand
  godfatherwiz census             full fleet roster

exit codes: 0 ok | 1 failed | 2 out of scope"""

CMDS = ("audit", "task", "run", "routes", "fleet", "law", "truth", "diagnose",
        "heal", "status", "repl", "siblings", "verify", "consent", "schedule",
        "queue", "history", "stats", "versions", "help", "census")

def _fail(msg):
    print(f"[FAIL] {msg}")
    return 1

def main():
    try:
        return _dispatch()
    except Exception as e:
        print(f"[FAIL] {type(e).__name__}: {e}")
        return 1

def _dispatch():
    args = sys.argv[1:]
    if args and args[0] in ("-h", "--help"):
        print(USAGE)
        return 0
    if not args:
        # bare invocation = the throne room: banner, voice, chat, slash commands
        return run_repl()
    if args[0] not in CMDS:
        print(USAGE)
        return 2
    
    cmd = args[0]
    
    # === CORE DISPATCHERS ===
    if cmd == "law":
        print(FATHER_LAW)
        return 0
    
    if cmd == "versions":
        import hashlib
        print("father_law_sha256:", hashlib.sha256(FATHER_LAW.encode()).hexdigest())
        return 0
    
    if cmd == "census":
        count, names = fleet_census()
        print(f"[OK] {count} certified citizens on the fleet")
        for i, n in enumerate(names, 1):
            print(f"  #{i:02d}  {n}")
        return 0
    
    if cmd == "help":
        if len(args) < 2:
            print("[FAIL] help requires a command name")
            return 2
        target = args[1]
        for line in USAGE.splitlines():
            if target in line:
                print(line.strip())
        return 0
    
    if cmd == "routes":
        routes = load_routes()
        if not routes:
            print("(routing table empty)")
            return 0
        for k, v in routes.items():
            print(f"  {k:25s} -> {' '.join(v)}")
        return 0
    
    if cmd == "fleet":
        count, names = fleet_census()
        print(f"[OK] {count} sibling wizards on the bin lane")
        for n in names:
            print(f"  {n}")
        return 0
    
    if cmd == "siblings":
        count, names = fleet_census()
        for i, n in enumerate(names, 1):
            print(f"[{i:2d}] {n}")
        return 0
    
    if cmd == "history":
        rows = ledger_rows()
        if not rows:
            print("(ledger empty — no dispatches yet)")
            return 0
        for row in rows:
            print(f"{row['at']}  {row['event']:16s} {row['target']} {row['detail']}")
        return 0
    
    if cmd == "stats":
        counts = Counter(r["event"] for r in ledger_rows())
        print(dict(counts) if counts else "(no events recorded)")
        return 0

    if cmd == "status":
        key_wizards = ["truthwiz", "writewiz", "pythonwiz", "bootwiz", "repairwiz"]
        for w in key_wizards:
            rc, out = call_sibling([w, "--help"])
            # exit 2 = usage fallthrough on --help, NOT death. Death = rc 1 or missing.
            alive = rc in (0, 2)
            print(f"[{'OK' if alive else 'FAIL'}] {w} {'reachable' if alive else 'unresponsive'}")
        return 0

    if cmd == "repl":
        return run_repl()
    
    # === PIPELINERS ===
    if cmd == "audit":
        if len(args) < 2:
            return _fail("audit requires a path")
        rc_overall = 0
        print("--- PHASE 1: truth anchor ---")
        rc, out = truth_anchor(args[1])
        print(out or "(no output)")
        if rc != 0:
            rc_overall = 1
        print("--- PHASE 2: manual census ---")
        rc, out = call_sibling(["manualwiz", "census", args[1]])
        print(out or "(no output)")
        if rc != 0:
            rc_overall = 1
        print(f"[{'OK' if rc_overall == 0 else 'FAIL'}] audit pipeline complete")
        return rc_overall
    
    if cmd == "task":
        if len(args) < 2:
            return _fail("task requires an intent")
        intent = " ".join(args[1:])
        rc_overall = 0
        print("--- PHASE 1: todowiz intake ---")
        rc, out = call_sibling(["todowiz", "add", intent])
        print(out or "(no output)")
        if rc != 0:
            rc_overall = 1
        print("--- PHASE 2: whiteboard ledger ---")
        rc, out = call_sibling(["whiteboardwiz", "task", "new", intent])
        print(out or "(no output)")
        if rc != 0:
            rc_overall = 1
        print(f"[{'OK' if rc_overall == 0 else 'FAIL'}] task pipeline complete")
        return rc_overall
    
    if cmd == "run":
        if len(args) < 2:
            return _fail("run requires a directive")
        directive = " ".join(args[1:])
        rc, anchor = truth_anchor(".")
        print(f"--- truth anchor (law 2) ---")
        print(anchor or "(no output)")
        
        pipeline, reason = route_directive(directive, [])
        if pipeline == "WALL":
            print(f"[CONSENT WALL] {reason}")
            print("to mutate: echo 'content' | writewiz propose <path>")
            print("then answer the wall yourself: writewiz commit <path>")
            journal("WALL_ROUTED", directive, "mutation detected")
            return 0
        if pipeline is None:
            print("out of scope — no route matches this directive")
            print("run 'godfatherwiz routes' to see the lawful table")
            journal("ROUTED", directive, "out of scope")
            return 2
        
        journal("ROUTED", directive, reason)
        print(f"[ROUTE] {reason}")
        print(f"--- executing: {' '.join(pipeline)} ---")
        rc, out = call_sibling(pipeline)
        print(out or "(no output)")
        if rc == 0:
            print("[OK] pipeline complete")
        else:
            print(f"[FAIL] pipeline ended with exit {rc}")
        return rc
    
    if cmd == "truth":
        if len(args) < 2:
            return _fail("truth requires a path")
        rc, out = truth_anchor(args[1])
        print(out or "(no output)")
        return rc
    
    if cmd == "diagnose":
        if len(args) < 2:
            return _fail("diagnose requires a directory")
        rc_overall = 0
        print("--- PHASE 1: debugwiz audit ---")
        rc, out = call_sibling(["debugwiz", "audit", args[1]])
        print(out or "(no output)")
        if rc != 0:
            rc_overall = 1
        print("--- PHASE 2: debugwiz triage ---")
        rc, out = call_sibling(["debugwiz", "triage", args[1]])
        print(out or "(no output)")
        if rc != 0:
            rc_overall = 1
        return rc_overall
    
    if cmd == "heal":
        if len(args) < 2:
            return _fail("heal requires a file path")
        rc, out = call_sibling(["repairwiz", "ladder", args[1]])
        print(out or "(no output)")
        print(f"handoff: writewiz commit {args[1]}   # your keystroke, Governor")
        return rc
    
    if cmd == "verify":
        if len(args) < 2:
            return _fail("verify requires a wizard name")
        rc, out = call_sibling([args[1], "--help"])
        print(f"[{'OK' if rc == 0 else 'FAIL'}] {args[1]} {'healthy' if rc == 0 else 'unhealthy'}")
        return 0
    
    if cmd == "consent":
        if len(args) < 2:
            return _fail("consent requires a file path")
        print(f"writewiz commit {args[1]}   # your keystroke, Governor")
        return 0
    
    if cmd == "schedule":
        if len(args) < 2:
            return _fail("schedule requires an intent")
        intent = " ".join(args[1:])
        task_id = schedule_task(intent)
        print(f"[OK] task scheduled: id={task_id}, intent={intent}")
        return 0

    if cmd == "queue":
        tasks = queue_tasks()
        if not tasks:
            print("(queue empty)")
            return 0
        for t in tasks:
            print(f"[{t['status']}] {t['id']} — {t['intent']}")
        return 0

    print("out of scope")
    return 2

# ============================================================================
# INTERACTIVE REPL MODE — THE COCKPIT
# ============================================================================

def _load_cfg():
    import json
    from pathlib import Path as _P
    cfgf = _P.home() / ".godfather" / "config.json"
    try:
        return json.loads(cfgf.read_text())
    except Exception:
        return {}

def _save_cfg(cfg):
    import json
    from pathlib import Path as _P
    cfgf = _P.home() / ".godfather" / "config.json"
    cfgf.parent.mkdir(parents=True, exist_ok=True)
    cfgf.write_text(json.dumps(cfg, indent=2))

def _pick_model():
    """Numbered model dropdown — picks from the LIVE Ollama roster, persists choice."""
    import os
    import subprocess
    print("\n💾 MODEL SELECTOR (live Ollama roster)")
    try:
        r = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=60)
        names = [ln.split()[0] for ln in r.stdout.strip().splitlines()[1:] if ln.strip()]
    except (OSError, subprocess.SubprocessError):
        names = []
    if not names:
        print("[FAIL] no models found — is Ollama running?")
        return
    for i, n in enumerate(names, 1):
        print(f"  [{i}] {n}")
    try:
        idx_pick = int(input("👑 model # ").strip()) - 1
        if 0 <= idx_pick < len(names):
            chosen = names[idx_pick]
            os.environ["GODFATHER_MODEL"] = chosen
            cfg = _load_cfg()
            cfg["model"] = chosen
            _save_cfg(cfg)
            print(f"[OK] oracle set to {chosen} (persisted in ~/.godfather/config.json)")
        else:
            print("[FAIL] invalid selection")
    except ValueError:
        print("[FAIL] enter a number")
    except (KeyboardInterrupt, EOFError):
        print("\n[OK] model selection cancelled — Sovereignty preserved.")

def _pick_voice():
    """Universal voice picker — direct disk discovery, no device assumptions.
    Scans every plausible Piper root on THIS machine + env overrides.
    Pairing law: a voice is real only with its .onnx.json config beside it."""
    import os
    from pathlib import Path as _P
    print("\n🎙️  VOICE SELECTOR (universal disk discovery)")

    home = _P.home()
    roots = []
    for var in ("VOICE_ROOT", "PAPER_VOICE_ROOT", "PIPER_VOICE_PATH"):
        val = os.environ.get(var)
        if val:
            roots.append(_P(val))
    roots.extend([
        home / "piper" / "voices",
        home / ".local" / "share" / "piper" / "voices",
        home / "piper-voices",
        _P("/usr/share/piper/voices"),
        _P("/usr/local/share/piper/voices"),
        home / ".config" / "piper" / "voices",
    ])

    found = {}  # name -> root it lives in
    for root in roots:
        if not root.is_dir():
            continue
        for onnx in root.glob("*.onnx"):
            if (root / (onnx.name + ".json")).exists() or onnx.with_suffix(".onnx.json").exists():
                found.setdefault(onnx.stem, root)

    if not found:
        print("[FAIL] no paired Piper voices found on this machine")
        print("roots scanned:")
        for r in roots:
            print(f"    {r}  {'(exists)' if r.is_dir() else ''}")
        print("hint: export VOICE_ROOT=<your voices dir> and retry")
        return

    # active voice: first .active found in any root
    active = ""
    for r in roots:
        af = r / ".active"
        if af.is_file():
            active = af.read_text().strip()
            break

    names = sorted(found)
    print(f"found {len(names)} voice(s):")
    for i, v in enumerate(names, 1):
        mark = "  <-- active" if v == active else ""
        print(f"  [{i:2d}] {v}{mark}")

    try:
        pick = input("👑 voice # ").strip()
        idx = int(pick) - 1
    except ValueError:
        print("[FAIL] enter a number")
        return
    except (KeyboardInterrupt, EOFError):
        print("\n[OK] voice selection cancelled — Sovereignty preserved.")
        return
    if not (0 <= idx < len(names)):
        print(f"[FAIL] pick 1-{len(names)}")
        return

    chosen = names[idx]
    root = found[chosen]
    (root / ".active").write_text(chosen)
    cfg = _load_cfg()
    cfg["voice"] = chosen
    cfg["voice_root"] = str(root)
    _save_cfg(cfg)
    # offer immediate ear test
    try:
        rc, out = call_sibling(["voicewiz", "speak", "voice set to " + chosen])
        if rc != 0:
            print(f"[OK] voice set to {chosen} (no ear test — voicewiz speak unavailable)")
        else:
            print(f"[OK] voice set to {chosen} — did you hear it?")
    except Exception:
        print(f"[OK] voice set to {chosen}")

def _classify_repl_input(user_input):
    """Return the action and arguments for one REPL line."""
    text = user_input.strip()

    if not text:
        return ("empty", [])

    if text in ("/quit", "/exit"):
        return ("quit", [])

    if text == "/help":
        return ("help", [])

    if text == "/voices":
        return ("voices", [])

    if text == "/model":
        return ("model", [])

    if text == "/more-commands":
        return ("more-commands", [])

    if text.startswith("/wiz"):
        tokens = text.split()
        return ("wiz", tokens[1:])

    if text.startswith("/"):
        parts = text.split()
        return ("slash", parts)

    return ("chat", [text])

def run_repl():
    """Launch interactive REPL with banner, voice, ollama chat, slash-commands."""
    import os
    render_banner()
    slash_map = list_all_slash_commands()
    session = session_load()
    session["session"] = session.get("session", 0) + 1
    session_save(session)
    cfg = _load_cfg()
    if cfg.get("model"):
        os.environ["GODFATHER_MODEL"] = cfg["model"]  # restore persisted choice
    print(f"\n👁️  SESSION {session['session']} — Sovereign Fleet Cockpit\n")
    print("Type /help for slash commands, /quit to exit.\n")
    chat_memory = []

    while True:
        try:
            raw_input = input("👑 godfather> ")
            action, args = _classify_repl_input(raw_input)
        except (EOFError, KeyboardInterrupt):
            print("\n[OK] Godfather bows out. Sovereignty preserved.")
            break

        if not raw_input:
            continue

        if raw_input in ("/quit", "/exit"):
            print("[OK] Godfather bows out. Sovereignty preserved.")
            break

        if raw_input == "/help":
            print("📜 AVAILABLE SLASH COMMANDS:")
            for cmd, desc in slash_map.items():
                print(f"  {cmd:15s} → {desc}")
            print("  /voices         → pick voice (numbered dropdown)")
            print("  /model          → pick model (numbered dropdown)")
            print("  /more-commands  → full fleet arsenal (all citizens)")
            continue

        if raw_input == "/voices":
            _pick_voice()
            continue

        if raw_input == "/model":
            _pick_model()
            continue

        if raw_input == "/more-commands":
            count, names = fleet_census()
            print(f"\n📚 FLEET ARSENAL — {count} citizens")
            print("=" * 60)
            for w in names:
                rc, out = call_sibling([w, "--help"])
                lines = out.splitlines()
                print(f"\n{w.upper()} ({'★' if rc == 0 else '✗'}):")
                for line in lines[:10]:
                    print(f"    {line}")
                if len(lines) > 10:
                    print(f"    ... ({len(lines) - 10} more, run '{w} --help')")
            print("\n" + "=" * 60)
            continue

        if raw_input.startswith("/"):
            cmd = raw_input.split()[0]
            if cmd in slash_map:
                # ARG LAW: keep the full pipeline (cmd + subcommand),
                # and split user args into proper argv tokens. Passing the
                # whole arg string as ONE element made citizens receive
                # 'FLEET-STATE.md' as an unknown subcommand.
                pipeline = slash_map[cmd].split()
                args = raw_input[len(cmd):].strip().split()
                rc, out = call_sibling(pipeline + args)
                print(out or "(no output)")
            elif cmd == "/wiz" and len(raw_input.split()) > 1:
                # UNIVERSAL DELEGATION: /wiz <citizen> [args...]
                # Resolves against the real bin lane — a citizen that
                # does not exist on disk cannot be invoked. Zero fabrication.
                parts = raw_input.split()
                target = parts[1]
                wiz_args = parts[2:]
                bin_path = Path.home() / "bin"
                real = bin_path / target
                if not real.exists():
                    candidates = [w.name for w in sorted(bin_path.glob(target + "*"))]
                    if not candidates:
                        print(f"out of scope — no citizen named '{target}' on the bin lane")
                        continue
                    if len(candidates) == 1:
                        real = bin_path / candidates[0]
                    else:
                        print(f"[FAIL] ambiguous citizen '{target}': {candidates}")
                        continue
                print(f"[ROUTE] universal delegation -> {real.name} {' '.join(wiz_args)}".rstrip())
                rc, out = call_sibling([str(real)] + wiz_args)
                print(out or "(no output)")
            else:
                print(f"[FAIL] unknown slash command: {cmd}")
                print("run /help to see available commands, or /wiz <citizen> [args]")
            continue

        # Natural language → chat WITH HANDS: oracle may request real tools
        model = os.environ.get("GODFATHER_MODEL", "")
        if not model:
            try:
                from lib.godfather_wizard import resolve_model
                model = resolve_model()
            except ImportError:
                model = "oracle"
        print(f"🤖 consulting oracle ({model})...", flush=True)
        from lib.godfather_wizard import oracle_tool_loop
        reply, chat_memory = oracle_tool_loop(raw_input, model, chat_memory)
        print(f"\n👑 godfather: {reply}\n")
        speak_if_enabled(reply)  # the whole word, uncut

if __name__ == "__main__":
    sys.exit(main())
