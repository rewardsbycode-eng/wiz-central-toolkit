"""
CodeGuard Wizard — universal code auditor & auto-fixer.
Naturalized citizen: stdlib-only (no requests), live daemon roster (no
hardcoded models), localhost default. Verdicts are plain text.
"""
import os
import json
import re
import hashlib
import urllib.request
from pathlib import Path
from datetime import datetime

OLLAMA_BASE = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")

# Seat preferences, honored ONLY if the live daemon actually serves them.
AUDIT_PREFS = ["qwen2.5-coder:3b-instruct", "stable-code:latest",
               "qwen2.5-coder:1.5b-instruct"]
FIX_PREFS = ["debug-seat:latest", "ops-seat:latest", "scholar-seat:latest",
             "qwen2.5-coder:3b-instruct"]

EXT_MAP = {
    ".py": "python", ".js": "javascript", ".ts": "typescript", ".jsx": "javascript",
    ".tsx": "typescript", ".java": "java", ".c": "c", ".cpp": "cpp", ".cc": "cpp",
    ".h": "c", ".hpp": "cpp", ".cs": "csharp", ".go": "go", ".rs": "rust",
    ".rb": "ruby", ".php": "php", ".swift": "swift", ".kt": "kotlin",
    ".scala": "scala", ".lua": "lua", ".pl": "perl", ".r": "r",
    ".sh": "bash", ".bash": "bash", ".zsh": "bash", ".fish": "bash",
    ".ps1": "powershell", ".bat": "batch", ".cmd": "batch",
    ".sql": "sql", ".html": "html", ".css": "css", ".scss": "scss",
    ".yml": "yaml", ".yaml": "yaml", ".json": "json", ".xml": "xml",
    ".toml": "toml", ".ini": "ini", ".cfg": "ini",
}
SHEBANG_PATTERNS = {
    "python": ["python", "python3"],
    "bash": ["bash", "sh", "zsh", "fish"],
    "ruby": ["ruby"], "perl": ["perl"], "node": ["node"],
    "lua": ["lua"], "php": ["php"],
    "powershell": ["pwsh", "powershell"],
}


def load_roster() -> list:
    """Ground truth: models actually served by the live daemon."""
    try:
        with urllib.request.urlopen(f"{OLLAMA_BASE}/api/tags", timeout=5) as r:
            return sorted(m.get("name", "?")
                          for m in json.loads(r.read()).get("models", []))
    except Exception:
        return []


def pick_seat(roster, prefs, env_var):
    """Env override wins; then preference order; then nothing (honest FAIL)."""
    override = os.environ.get(env_var, "").strip()
    if override:
        return override if override in roster or roster == [] else None
    for pref in prefs:
        for name in roster:
            if name == pref or name.startswith(pref.split(":")[0]):
                return name
    return None


def detect_language(filepath: str) -> str:
    """Extension, then shebang, then content sniffing."""
    p = Path(filepath)
    ext = p.suffix.lower()
    if ext in EXT_MAP:
        return EXT_MAP[ext]
    name = p.name.lower()
    if name == "dockerfile":
        return "dockerfile"
    if name == "makefile":
        return "makefile"
    try:
        with open(filepath, "r", errors="ignore") as f:
            first_line = f.readline().strip()
        if first_line.startswith("#!"):
            shebang = first_line.lower()
            for lang, markers in SHEBANG_PATTERNS.items():
                if any(m in shebang for m in markers):
                    return lang
    except Exception:
        pass
    try:
        content = open(filepath, "r", errors="ignore").read(2048).lower()
        sigs = {
            "python": ["def ", "import ", "class ", "self.", "print(", "if __name__"],
            "javascript": ["function ", "const ", "let ", "var ", "console.log", "=>"],
            "go": ["func ", "package ", "import (", "fmt.Print"],
            "rust": ["fn ", "let mut", "impl ", "pub fn", "println!"],
            "ruby": ["def ", "puts ", "require ", "module "],
            "php": ["<?php", "function ", "$this->", "echo "],
            "c": ["#include", "int main", "printf(", "struct "],
            "cpp": ["#include", "std::", "int main", "cout <<"],
        }
        scores = {lang: sum(content.count(kw) for kw in kws)
                  for lang, kws in sigs.items()}
        best = max(scores, key=scores.get) if scores else None
        if best and scores[best] >= 3:
            return best
    except Exception:
        pass
    return "unknown"


def _call_ollama(model: str, prompt: str, timeout: int = 120) -> str:
    """Stdlib-only daemon call. Returns '' on any failure."""
    try:
        payload = json.dumps({"model": model, "prompt": prompt,
                              "stream": False}).encode()
        req = urllib.request.Request(f"{OLLAMA_BASE}/api/generate", data=payload,
                                      headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read()).get("response", "").strip()
    except Exception:
        return ""


def _try_parse_json(text: str):
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return None


def _hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()


def build_audit_prompt(language, code, filepath):
    return f"""You are a senior code auditor and security engineer. Analyze the following {language} code.

FILE: {filepath}
LANGUAGE: {language}

Audit for: security flaws, logic bugs, edge cases, quality issues, design concerns.

Format your response EXACTLY as this JSON structure:
{{
  "language": "{language}",
  "issues": [
    {{
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "category": "security|logic|edge_case|quality|design",
      "line_range": [start_line, end_line],
      "title": "Short title",
      "description": "Detailed explanation",
      "fix": "Concrete fix suggestion"
    }}
  ],
  "summary": "Overall assessment paragraph",
  "score": 0-100
}}

CODE TO AUDIT:
---
{code}
---"""


def build_fix_prompt(language, code, filepath, issues_json):
    return f"""You are an expert {language} developer. Fix ALL the issues identified in the audit.

Return ONLY the complete corrected code — no markdown fences, no explanations, no preamble.
Preserve comments and formatting not part of an issue. Add imports if a fix requires them.

ORIGINAL FILE: {filepath}

AUDIT REPORT:
{issues_json}

ORIGINAL CODE:
{code}

OUTPUT THE FULL CORRECTED CODE NOW:"""


def read_code(filepath):
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except OSError as e:
        return None


def audit(filepath: str, model: str = None) -> dict:
    """Audit one file. Returns a result dict; status OK/FAILED."""
    code = read_code(filepath)
    if code is None:
        return {"status": "FAILED", "reason": "cannot read file"}
    language = detect_language(filepath)
    if language == "unknown":
        return {"status": "FAILED", "reason": "cannot detect language"}
    roster = load_roster()
    audit_model = model or pick_seat(roster, AUDIT_PREFS, "CODEGUARD_AUDIT_MODEL")
    if not audit_model:
        return {"status": "FAILED",
                "reason": "no audit seat: daemon unreachable or no coder seat served",
                "roster_size": len(roster)}
    raw = _call_ollama(audit_model,
                       build_audit_prompt(language, code, filepath))
    if not raw:
        return {"status": "FAILED", "reason": "ollama audit call failed",
                "model": audit_model}
    audit_data = _try_parse_json(raw)
    if audit_data is None:
        return {"status": "FAILED", "reason": "unparseable audit response",
                "raw": raw[:400]}
    counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for issue in audit_data.get("issues", []):
        sev = issue.get("severity", "LOW")
        if sev in counts:
            counts[sev] += 1
    return {"status": "OK", "filepath": filepath, "language": language,
            "model": audit_model, "code_hash": _hash(code),
            "audit": audit_data, "issues_count": counts,
            "timestamp": datetime.now().isoformat()}


def fix(filepath: str, audit_result: dict = None, model: str = None) -> dict:
    """Generate fixed code for one file. Does NOT write — caller consents."""
    code = read_code(filepath)
    if code is None:
        return {"status": "FAILED", "reason": "cannot read file"}
    original_hash = _hash(code)
    if audit_result is None:
        audit_result = audit(filepath)
        if audit_result["status"] != "OK":
            return {"status": "FAILED", "reason": "audit failed before fix"}
    issues = audit_result.get("audit", {}).get("issues", [])
    if not issues:
        return {"status": "OK", "filepath": filepath,
                "original_hash": original_hash, "fixed_hash": original_hash,
                "fixed_code": code, "issues_fixed": 0,
                "message": "no issues to fix"}
    roster = load_roster()
    fix_model = model or pick_seat(roster, FIX_PREFS, "CODEGUARD_FIX_MODEL")
    if not fix_model:
        return {"status": "FAILED",
                "reason": "no fix seat: daemon unreachable or no seat served"}
    language = audit_result.get("language", "unknown")
    prompt = build_fix_prompt(language, code, filepath,
                              json.dumps(issues, indent=2))
    fixed_code = _call_ollama(fix_model, prompt, timeout=180)
    if not fixed_code:
        return {"status": "FAILED", "reason": "ollama fix call failed"}
    if fixed_code.startswith("```"):
        lines = fixed_code.split("\n")
        fixed_code = "\n".join(lines[1:-1] if lines[-1].startswith("```")
                               else lines[1:])
    fixed_code = fixed_code.strip()
    return {"status": "OK", "filepath": filepath,
            "original_hash": original_hash, "fixed_hash": _hash(fixed_code),
            "fixed_code": fixed_code, "fix_model": fix_model,
            "issues_fixed": len(issues),
            "hashes_match": original_hash == _hash(fixed_code),
            "timestamp": datetime.now().isoformat()}
