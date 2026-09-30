"""godfather-wizard brain — the Grand Master, fleet dispatcher & REPL.

FATHER LAW:
  He owns no logic. He routes intents to his 33 children via shell.
  Every mutation is staged through the writewiz consent wall; the
  'y' keystroke belongs to the Governor alone. Routing is a plain,
  deterministic keyword table — anything unmapped is out of scope.
  The REPL exposes all /slashcommands from the fleet; voice is enabled
  on all responses when VOICE_ENABLED=true. bootwiz governs birth;
  godfather governs execution and conversation.
"""

import datetime as dt
import json
import subprocess
import os
from collections import Counter
from pathlib import Path

HOME = Path.home()
BIN = HOME / "bin"
BANK = HOME / ".godfather"
LEDGER = BANK / "ledger.jsonl"
ROUTER_DB = BANK / "routes.json"
STATE_FILE = BANK / "session_state.json"
VOICE_ENABLED = os.environ.get("VOICE_ENABLED", "true").lower() == "true"

FATHER_LAW = """FATHER LAW (godfather-wizard, the Grand Master)
1. DELEGATION: re-implements nothing; invokes siblings via ~/bin only.
2. TRUTH FIRST: multi-step runs anchor facts with truthwiz before acting.
3. CONSENT WALL: mutations are staged via writewiz propose; godfather
   never supplies the 'y'. The commit keystroke belongs to the Governor.
4. DETERMINISTIC ROUTES: run dispatches via the keyword table;
   unmapped intents return 'out of scope', never improvised.
5. VERDICTS: plain [OK]/[FAIL]/out of scope, exit 0/1/2, no tracebacks.
6. bootwiz governs birth; godfather governs execution + conversation.
7. EVERY DISPATCH IS JOURNALED: all routing events recorded to ledger.
8. REPL MODE exposes all /slashcommands from the fleet under one roof.
9. VOICE ENABLED: when VOICE_ENABLED=true, every REPL response speaks.
10. BANNER ON LAUNCH: every godfatherwiz repl shows the Sovereign mural.
"""

def _ensure_bank():
    BANK.mkdir(parents=True, exist_ok=True)
    if not LEDGER.exists():
        LEDGER.touch()
    if not ROUTER_DB.exists():
        default = {
            "syntax/pycheck": ["pythonwiz", "check"],
            "diff/compare": ["diffwiz", "files"],
            "json/validate": ["jsonwiz", "validate"],
            "list/listing/whatshere": ["truthwiz", "listing"],
            "models/ollama": ["ollamawiz", "list"],
            "todos/tasklist": ["todowiz", "list"],
            "tmux/sessions": ["tmuxwiz", "list"],
            "symlinks/bins": ["truthwiz", "symlinks"],
            "diag/audit": ["debugwiz", "audit"],
            "heal/repair": ["repairwiz", "ladder"],
        }
        ROUTER_DB.write_text(json.dumps(default, indent=2))
    if not STATE_FILE.exists():
        STATE_FILE.write_text(json.dumps({"session": 1, "slang": {}}, indent=2))

def load_routes():
    _ensure_bank()
    try:
        return json.loads(ROUTER_DB.read_text())
    except (json.JSONDecodeError, OSError):
        return {}

def save_routes(routes):
    _ensure_bank()
    ROUTER_DB.write_text(json.dumps(routes, indent=2))

def _now():
    return dt.datetime.now().isoformat(timespec="seconds")

def journal(event, target, detail=""):
    _ensure_bank()
    row = {"at": _now(), "event": event, "target": str(target), "detail": detail}
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True) + "\n")

def ledger_rows():
    if not LEDGER.exists():
        return []
    rows = []
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            rows.append({"at": "?", "event": "CORRUPT_ROW", "target": line, "detail": ""})
    return rows

def call_sibling(cmd_list, stdin=None):
    exe = BIN / cmd_list[0]
    if not exe.exists():
        return 2, f"[FAIL] sibling not found on bin lane: {cmd_list[0]}"
    try:
        r = subprocess.run([str(exe)] + cmd_list[1:], input=stdin,
                           capture_output=True, text=True, timeout=180)
        return r.returncode, (r.stdout + r.stderr).strip()
    except (subprocess.TimeoutExpired, OSError) as e:
        return 1, f"[FAIL] sibling call failed: {e}"

def resolve_model():
    """Honest model pick: env override if real, else first model from the live roster."""
    import shutil
    wanted = os.environ.get("GODFATHER_MODEL", "").strip()
    try:
        r = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=60)
        names = [ln.split()[0] for ln in r.stdout.strip().splitlines()[1:] if ln.strip()]
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError):
        names = []
    if wanted and wanted in names:
        return wanted
    if names:
        return names[0]
    return wanted or "llama3.2:1b"  # last resort; if this is a ghost the oracle will say so

def call_ollama(prompt, model=None):
    """Consult the oracle: ollamawiz first, Ollama binary as honest fallback."""
    actual_model = model or resolve_model()
    rc, out = call_sibling(["ollamawiz", "ask", actual_model, prompt])
    if rc == 0 and out and not out.startswith("[FAIL]"):
        return rc, out
    try:
        r = subprocess.run(["ollama", "run", actual_model, prompt],
                           capture_output=True, text=True, timeout=300)
        if r.returncode == 0 and r.stdout.strip():
            return 0, r.stdout.strip()
        return 1, (r.stderr or "[FAIL] oracle returned nothing").strip()
    except FileNotFoundError:
        return 1, "[FAIL] neither ollamawiz ask nor ollama binary available"
    except subprocess.TimeoutExpired:
        return 1, "[FAIL] oracle timed out"

def speak_if_enabled(text):
    """Speak text if VOICE_ENABLED=true, otherwise silent."""
    if not VOICE_ENABLED:
        return
    rc, out = call_sibling(["voicewiz", "speak", text])  # the whole word, uncut
    # Silent success expected

def truth_anchor(path="."):
    """Law 2: anchor ground truth before multi-step action."""
    return call_sibling(["truthwiz", "brief", str(Path(path).expanduser())])

def route_directive(directive, args):
    """Deterministic dispatch. Returns (pipeline, reason) or None."""
    d = directive.lower()
    
    MUTATION_WORDS = {"write", "fix", "create", "delete", "remove", "modify", "edit", "rm", "heal", "repair"}
    
    if any(w in d for w in MUTATION_WORDS):
        return ("WALL", "mutation intent detected — route through writewiz")
    
    routes = load_routes()
    for keywords, pipeline in routes.items():
        if any(k in d for k in keywords.split("/")):
            return (pipeline + args, f"matched route: {keywords}")
    
    return None, "no route matches this intent"

def fleet_census():
    """Health sweep: count sibling *wiz executables on the bin lane."""
    wizs = sorted(BIN.glob("*wiz"))
    return len(wizs), [w.name for w in wizs]

def list_all_slash_commands():
    """Return mapping of /slash -> wizard command."""
    # Consolidated fleet-wide slash-command registry
    slash_map = {
        "/truth": "truthwiz listing",
        "/ls": "truthwiz listing",
        "/read": "truthwiz read",
        "/pycheck": "pythonwiz check",
        "/fix": "repairwiz ladder",
        "/heal": "repairwiz ladder",
        "/todo": "todowiz add",
        "/todos": "todowiz list",
        "/diff": "diffwiz files",
        "/models": "ollamawiz list",
        "/tasks": "todowiz list",
        "/audit": "debugwiz audit",
        "/diag": "debugwiz classify",
        "/bins": "truthwiz symlinks",
        "/history": "godfatherwiz history",
        "/stats": "godfatherwiz stats",
        "/routes": "godfatherwiz routes",
        "/fleet": "godfatherwiz fleet",
        "/law": "godfatherwiz law",
        "/help": "godfatherwiz help",
        "/status": "godfatherwiz status",
        "/census": "godfatherwiz census",
    }
    return slash_map

def session_load():
    _ensure_bank()
    try:
        return json.loads(STATE_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return {"session": 1}

def session_save(state):
    _ensure_bank()
    STATE_FILE.write_text(json.dumps(state, indent=2))

def schedule_task(intent, delay_secs=0):
    """Queue a task with timestamp."""
    _ensure_bank()
    task_id = hash(f"{intent}{_now()}") % 100000
    task = {"id": task_id, "intent": intent, "scheduled_at": _now(),
            "delay_sec": delay_secs, "status": "queued"}
    tasks = load_routes()
    tasks[f"task_{task_id}"] = task
    save_routes(tasks)
    journal("SCHEDULED", str(task_id), intent)
    return task_id

def queue_tasks():
    """Show scheduled tasks."""
    _ensure_bank()
    tasks = load_routes()
    return [v for k, v in tasks.items() if k.startswith("task_")]

def render_banner():
    """Sovereign mural: figlet + rich 16-color, guaranteed to fit the terminal."""
    import shutil
    try:
        from pyfiglet import Figlet
        from rich.console import Console
        from rich.text import Text
    except ImportError:
        print("=== GODFATHER — GRAND MASTER OF THE SOVEREIGN FLEET ===")
        return

    width = shutil.get_terminal_size((100, 24)).columns
    text = "GODFATHER"
    subtitle = "G R A N D   M A S T E R   O F   T H E   S O V E R E I G N   F L E E T"

    # Width-fit: walk fonts until the art fits with a 2-col margin
    art = None
    for font in ("slant", "smslant", "small", "term", "digital"):
        candidate = Figlet(font=font, width=width).renderText(text).rstrip("\n")
        longest = max((len(ln) for ln in candidate.splitlines()), default=0)
        if longest <= width - 2:
            art = candidate
            break
    if art is None:  # terminal too narrow for any font — plain, clean, honest
        print("=== GODFATHER — GRAND MASTER OF THE SOVEREIGN FLEET ===")
        return

    console = Console(highlight=False)
    console.print(Text(art, style="bright_magenta bold"))
    if len(subtitle) <= width - 2:
        console.print(Text(subtitle, style="bright_yellow"))
    else:
        console.print(Text("GRAND MASTER", style="bright_yellow"))
    _, _census_names = fleet_census()
    console.print(Text(f"{width} cols | Sovereign Fleet: {len(_census_names)} citizens, zero lies",
                       style="bright_cyan"))

# ------------------------------------------------------------------
# ORACLE WITH HANDS — the Governor's tool channel for the cockpit
# ------------------------------------------------------------------

ORACLE_SPINE = """You command the Sovereign Fleet — check AVAILABLE TOOLS below for the live citizen count and capacity.
You act as the central dispatcher and reasoning engine for all interactive wizard queries.
You command the real CLI wizards listed below on this machine. You have NO eyes and NO hands
of your own. Your only way to act or observe is the TOOL channel.

TOOL CHANNEL — to request one real action, reply with a single line, exactly:
TOOL: <command>
where <command> is a real wizard invocation from the AVAILABLE TOOLS list.

LAWS:
- ONE tool call per reply. Then STOP and wait for the true result.
- NEVER invent output, file names, or states you have not been shown.
- NEVER use shell commands (ls, cat, rm, pwd...) — they are forbidden and rejected.
- When you have enough truth, drop the channel and answer plainly.
- If no tool fits, answer plainly and say so.

WORKED EXAMPLE — if the user asks "what files are in ~/wizard_central?",
your ENTIRE reply must be exactly this one line:
TOOL: truthwiz listing __HOME__/wizard_central

Then stop. The true result will be given to you, and you summarize it.
"""

import os as _os_home
ORACLE_SPINE = ORACLE_SPINE.replace("__HOME__", _os_home.path.expanduser("~"))

CONSENT_PREFIXES = ("writewiz", "repairwiz heal", "repairwiz commit")

def _ollama_chat_api(messages, model):
    """Direct stdlib chat call — no external deps, honest failures."""
    import json as _j
    import urllib.request
    import urllib.error
    payload = _j.dumps({"model": model, "messages": messages,
                        "stream": False}).encode()
    req = urllib.request.Request(
        "http://127.0.0.1:11434/api/chat",
        data=payload, headers={"Content-Type": "application/json"})
    import os as _os
    _timeout = int(_os.environ.get("WIZ_OLLAMA_TIMEOUT", "600"))
    with urllib.request.urlopen(req, timeout=_timeout) as r:
        data = _j.loads(r.read().decode())
    return data.get("message", {}).get("content", "")

def build_tool_manifest():
    """Real fleet roster from disk — no fabricated commands."""
    _, names = fleet_census()
    # names only — probe hints bloated the context; the oracle doesn't need them
    return ", ".join(names)

def oracle_tool_loop(question, model, memory, max_rounds=5):
    """Chat with hands: tool calls execute REAL wizards, results feed back in.
    Returns (final_reply, memory). Memory is this session's conversation."""
    import os as _os
    if _os.environ.get("WIZ_AI_PROVIDER", "").strip().lower() == "none":
        return ("[FAIL] AI disabled (WIZ_AI_PROVIDER=none)", memory)
    if not memory:
        memory.append({"role": "system",
                       "content": ORACLE_SPINE + "\nAVAILABLE TOOLS:\n" + build_tool_manifest()})
    memory.append({"role": "user", "content": question})

    for round_i in range(max_rounds):
        try:
            reply = _ollama_chat_api(memory, model)
        except Exception as e:
            return (f"[FAIL] oracle unreachable ({type(e).__name__}: {e})", memory)
        memory.append({"role": "assistant", "content": reply})

        tool_line = None
        for line in reply.splitlines():
            if line.strip().upper().startswith("TOOL:"):
                tool_line = line.strip()[5:].strip()
                break
        if not tool_line:
            return reply, memory  # a plain answer — done

        # consent wall: mutating lanes need the Governor's y/n
        if tool_line.startswith(CONSENT_PREFIXES):
            try:
                ans = input(f"\n⚠️  oracle wants to WRITE: {tool_line}\napprove? [y/N] ")
            except (KeyboardInterrupt, EOFError):
                ans = "n"
            if ans.strip().lower() != "y":
                memory.append({"role": "user", "content":
                               "GOVERNOR DENIED this action. Proceed without it."})
                continue

        print(f"🔧 {tool_line}")
        parts = [word.replace("~", __import__("os").path.expanduser("~"))
                 if word.startswith("~") else word
                 for word in tool_line.split()]
        if not parts:
            continue

        # FLEET WHITELIST — only real citizens may act. No shell reach-arounds.
        # Common shell verbs are TRANSLATED to their lawful fleet equivalents.
        SHELL_TRANSLATIONS = {
            "ls": ["truthwiz", "listing"],
            "dir": ["truthwiz", "listing"],
            "cat": ["truthwiz", "read"],
            "head": ["truthwiz", "head"],
            "pwd": ["truthwiz", "brief"],
            "find": ["truthwiz", "find"],
            "du": ["truthwiz", "du"],
            "stat": ["truthwiz", "stat"],
            "grep": ["truthwiz", "read"],
        }
        fleet_names = set(fleet_census()[1])
        if parts[0] not in fleet_names:
            if parts[0] in SHELL_TRANSLATIONS:
                new_parts = SHELL_TRANSLATIONS[parts[0]] + parts[1:]
                print(f"[TRANSLATE] '{parts[0]}' → '{' '.join(new_parts[:2])}' (lawful fleet equivalent)")
                parts = new_parts
            else:
                memory.append({"role": "user", "content":
                    f"REJECTED: '{parts[0]}' is NOT a fleet tool. Shell commands are "
                    f"forbidden. Your ONLY way to see files is exactly this line:\n"
                    f"TOOL: truthwiz listing <path>\n"
                    f"Emit that line now with the real path, or answer plainly."})
                print(f"[REJECT] '{parts[0]}' is not a citizen — bouncing back")
                continue
        if parts[0] not in fleet_names:
            memory.append({"role": "user", "content":
                f"REJECTED: '{parts[0]}' is not a fleet tool. Answer plainly instead."})
            print(f"[REJECT] '{parts[0]}' is not a citizen — bouncing back")
            continue

        # DUPLICATE SHIELD — same command twice = answer from what we already have
        sig = " ".join(parts)
        if not hasattr(oracle_tool_loop, "_last_calls"):
            oracle_tool_loop._last_calls = set()
        if sig in oracle_tool_loop._last_calls:
            oracle_tool_loop._dup_count = getattr(oracle_tool_loop, "_dup_count", 0) + 1
            if oracle_tool_loop._dup_count >= 2:
                # small brains can't pivot — present the truth ourselves, honestly
                last_result = getattr(oracle_tool_loop, "_last_result", "(none)")
                print("[FORCED SUMMARY] oracle won't stop repeating — presenting raw truth")
                return ("[RAW TRUTH — oracle could not summarize, presented verbatim]\n"
                        + last_result, memory)
            memory.append({"role": "user", "content":
                f"DUPLICATE: you already ran '{sig}'. STOP calling tools. Your next "
                f"reply must be a PLAIN ANSWER with no TOOL: line. Summarize the "
                f"result you already received. Nothing else."})
            print("[DEDUP] identical tool call suppressed — final warning issued")
            continue
        seen_calls.add(sig)

        rc, out = call_sibling(parts)
        result = (out or "").strip() or "(no output)"
        oracle_tool_loop._last_result = result

        # CONTEXT DIET — small seats have 4096-token windows; feed a digest,
        # not the raw firehose. Tell the oracle it was truncated.
        MAX_RESULT_LINES = 60
        lines = result.splitlines()
        truncated_note = ""
        if len(lines) > MAX_RESULT_LINES:
            result = "\n".join(lines[:MAX_RESULT_LINES])
            truncated_note = ("\n(result truncated to first "
                              f"{MAX_RESULT_LINES} of {len(lines)} lines)")

        memory.append({"role": "user", "content":
                       f"TOOL RESULT ({tool_line}, exit {rc}):\n{result}"
                       + truncated_note})

    return ("[FAIL] oracle exhausted tool rounds without a plain answer "
            "(run /model to pick a stronger seat)", memory)
