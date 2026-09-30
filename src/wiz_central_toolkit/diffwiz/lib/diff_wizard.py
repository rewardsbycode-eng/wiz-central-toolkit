"""diff-wizard core: standalone change-truth doctor. Unified file diffs, filtered tree diffs."""
import difflib
from pathlib import Path

SKIP_DIRS = {".venv", ".git", "__pycache__", ".bootstrap", "node_modules"}

class DiffWizard:
    """Read-only truth engine. Never modifies either side of a comparison."""

    def diff_files(self, path_a: Path, path_b: Path) -> str:
        a_lines = path_a.read_text(errors="replace").splitlines(keepends=True)
        b_lines = path_b.read_text(errors="replace").splitlines(keepends=True)
        return "".join(difflib.unified_diff(
            a_lines, b_lines,
            fromfile=str(path_a), tofile=str(path_b),
        ))

    def diff_dirs(self, dir_a: Path, dir_b: Path) -> dict:
        files_a = {
            str(p.relative_to(dir_a)): p
            for p in dir_a.rglob("*")
            if p.is_file() and not any(part in SKIP_DIRS for part in p.parts)
        }
        files_b = {
            str(p.relative_to(dir_b)): p
            for p in dir_b.rglob("*")
            if p.is_file() and not any(part in SKIP_DIRS for part in p.parts)
        }
        only_a = sorted(set(files_a) - set(files_b))
        only_b = sorted(set(files_b) - set(files_a))
        common = sorted(set(files_a) & set(files_b))
        differing = [rel for rel in common
                     if files_a[rel].read_bytes() != files_b[rel].read_bytes()]
        return {"only_a": only_a, "only_b": only_b, "differing": differing}

    def diff_files_context(self, path_a: Path, path_b: Path, context: int = 3) -> str:
        a_lines = path_a.read_text(errors="replace").splitlines(keepends=True)
        b_lines = path_b.read_text(errors="replace").splitlines(keepends=True)
        return "".join(difflib.unified_diff(
            a_lines, b_lines,
            fromfile=str(path_a), tofile=str(path_b),
            n=context,
        ))

    def diff_summary(self, source_a: Path, source_b: Path) -> dict:
        if source_a.is_dir() and source_b.is_dir():
            result = self.diff_dirs(source_a, source_b)
            added = len(result["only_b"])
            removed = len(result["only_a"])
            changed = len(result["differing"])
            if not (added or removed or changed):
                return {"identical": True}
            return {
                "identical": False,
                "added_lines": added + changed,
                "removed_lines": removed + changed,
                "hunks": added + removed + changed,
            }
        diff_text = self.diff_files(source_a, source_b)
        if not diff_text:
            return {"identical": True}
        added = sum(1 for line in diff_text.splitlines() if line.startswith("+") and not line.startswith("+++"))
        removed = sum(1 for line in diff_text.splitlines() if line.startswith("-") and not line.startswith("---"))
        changed_hunks = sum(1 for line in diff_text.splitlines() if "@@" in line)
        return {"identical": False, "added_lines": added, "removed_lines": removed, "hunks": changed_hunks}

    def diff_word_level(self, source_a: Path, source_b: Path) -> str:
        a_text = source_a.read_text(errors="replace")
        b_text = source_b.read_text(errors="replace")
        a_words = a_text.split()
        b_words = b_text.split()
        matcher = difflib.SequenceMatcher(None, a_words, b_words)
        output = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                output.append(" ".join(a_words[i1:i2]))
            elif tag == "replace":
                output.append(f"<del>{' '.join(a_words[i1:i2])}</del><ins>{' '.join(b_words[j1:j2])}</ins>")
            elif tag == "delete":
                output.append(f"<del>{' '.join(a_words[i1:i2])}</del>")
            elif tag == "insert":
                output.append(f"<ins>{' '.join(b_words[j1:j2])}</ins>")
        return "\n".join(output)

    def files_identical(self, path_a: Path, path_b: Path) -> bool:
        return path_a.read_bytes() == path_b.read_bytes()

    def diff_files_reverse(self, path_a: Path, path_b: Path) -> str:
        return self.diff_files(path_b, path_a)