"""todo-wizard core: standalone, importable todo engine."""
import json
import hashlib
import datetime as dt
from pathlib import Path
from typing import Optional

class TodoWizard:
    """Per-project persistent todo engine. Storage lives in ~/.todo-wizard/."""

    BANK = Path.home() / ".todo-wizard"

    def __init__(self, project_dir: Optional[str] = None, bank: Optional[Path] = None):
        self.project = Path(project_dir or Path.cwd()).resolve()
        self.bank = bank or self.BANK
        self.store_path = self._store_for(self.project)

    def _store_for(self, path: Path) -> Path:
        key = hashlib.sha256(str(path).encode()).hexdigest()[:16]
        return self.bank / f"{path.name}-{key}.json"

    def _load(self) -> dict:
        if self.store_path.exists():
            return json.loads(self.store_path.read_text())
        return {"project": str(self.project), "todos": [], "created": self._now()}

    def _save(self, data: dict) -> None:
        self.bank.mkdir(parents=True, exist_ok=True)
        tmp = self.store_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2))
        tmp.replace(self.store_path)

    @staticmethod
    def _now() -> str:
        return dt.datetime.now().isoformat(timespec="seconds")

    def add(self, text: str, priority: str = "normal") -> dict:
        data = self._load()
        item = {
            "id": max((t["id"] for t in data["todos"] + data.get("archive", [])), default=0) + 1,
            "text": text,
            "priority": priority,
            "done": False,
            "created": self._now(),
            "completed": None,
        }
        data["todos"].append(item)
        data["last_modified"] = self._now()
        self._save(data)
        return item

    def complete(self, todo_id: int) -> bool:
        data = self._load()
        for item in data["todos"]:
            if item["id"] == todo_id and not item["done"]:
                item["done"] = True
                item["completed"] = self._now()
                self._save(data)
                return True
        return False

    def remove(self, todo_id: int) -> bool:
        data = self._load()
        before = len(data["todos"])
        data["todos"] = [t for t in data["todos"] if t["id"] != todo_id]
        if len(data["todos"]) < before:
            self._save(data)
            return True
        return False

    def list_todos(self, pending_only: bool = False) -> list:
        todos = self._load()["todos"]
        return [t for t in todos if not t["done"]] if pending_only else todos

    def stats(self) -> dict:
        todos = self.list_todos()
        done = sum(1 for t in todos if t["done"])
        return {"total": len(todos), "done": done, "pending": len(todos) - done}

    def undo_complete(self, todo_id: int) -> bool:
        """Reopen a closed task."""
        data = self._load()
        for item in data["todos"]:
            if item["id"] == todo_id and item["done"]:
                item["done"] = False
                item["completed"] = None
                data["last_modified"] = self._now()
                self._save(data)
                return True
        return False

    def note(self, todo_id: int, text: str) -> bool:
        """Append a progress note to a task (evidence trail)."""
        data = self._load()
        for item in data["todos"]:
            if item["id"] == todo_id:
                notes = item.setdefault("notes", [])
                notes.append({"text": text, "at": self._now()})
                data["last_modified"] = self._now()
                self._save(data)
                return True
        return False

    def oldest(self) -> Optional[dict]:
        """Return the stalest pending task."""
        pending = self.list_todos(pending_only=True)
        if not pending:
            return None
        return min(pending, key=lambda t: t["created"])

    def archive_done(self) -> int:
        """Move completed tasks to the archive list (never destroy)."""
        data = self._load()
        done_items = [t for t in data["todos"] if t["done"]]
        if not done_items:
            return 0
        archive = data.setdefault("archive", [])
        archive.extend(done_items)
        archive.sort(key=lambda t: t.get("completed") or "")
        data["todos"] = [t for t in data["todos"] if not t["done"]]
        data["last_modified"] = self._now()
        self._save(data)
        return len(done_items)

    def overdue(self, days: int = 7) -> list:
        """Pending tasks older than N days."""
        cutoff = dt.datetime.now() - dt.timedelta(days=days)
        result = []
        for t in self.list_todos(pending_only=True):
            created = dt.datetime.fromisoformat(t["created"])
            age_days = (dt.datetime.now() - created).total_seconds() / 86400
            if created < cutoff:
                result.append((t, age_days))
        return result