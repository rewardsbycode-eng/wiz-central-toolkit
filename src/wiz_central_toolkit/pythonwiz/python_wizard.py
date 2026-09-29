"""python-wizard core: standalone syntax doctor for Python files."""
import ast
import re
import sys
from pathlib import Path

SKIP_DIRS = {".venv", ".git", "__pycache__", ".bootstrap", "node_modules"}
STDLIB = set(sys.stdlib_module_names)

class PythonWizard:
    """AST analysis engine. Never executes the target code — parse only."""

    # ---------- existing ----------
    def check_file(self, path: Path) -> dict:
        try:
            ast.parse(path.read_text())
            return {"file": str(path), "valid": True}
        except SyntaxError as e:
            return {"file": str(path), "valid": False, "line": e.lineno,
                    "col": e.offset, "error": e.msg}

    def check_dir(self, root: Path) -> list:
        results = []
        for py in self.py_files(root):
            results.append(self.check_file(py))
        return results

    def check_entry(self, path: Path) -> dict:
        if not path.exists():
            return {"file": str(path), "valid": False, "error": "file not found"}
        content = path.read_text()
        first = content.splitlines()[0] if content else ""
        if not first.startswith("#!"):
            return {"file": str(path), "valid": False, "error": "no shebang line"}
        interp = Path(first[2:])
        if not interp.is_absolute() or not interp.exists():
            return {"file": str(path), "valid": False, "error": f"interpreter missing: {first[2:]}"}
        return {"file": str(path), "valid": True, "interpreter": str(interp)}

    # ---------- helpers ----------
    @staticmethod
    def py_files(root: Path) -> list:
        return [p for p in sorted(root.rglob("*.py"))
                if not any(part in SKIP_DIRS for part in p.parts)]

    @staticmethod
    def parse(path: Path) -> ast.Module:
        return ast.parse(path.read_text())

    # ---------- new commands ----------
    def outline(self, path: Path) -> list:
        tree = self.parse(path)
        symbols = []

        def visit(node, prefix=""):
            for child in ast.iter_child_nodes(node):
                if isinstance(child, ast.ClassDef):
                    symbols.append(("class", prefix + child.name, child.lineno))
                    visit(child, prefix + child.name + ".")
                elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    symbols.append(("def", prefix + child.name, child.lineno))

        visit(tree)
        return symbols

    def imports_of(self, path: Path) -> dict:
        tree = self.parse(path)
        siblings = {p.stem for p in path.parent.glob("*.py")}
        result: dict[str, set[str]] = {"stdlib": set(), "third_party": set(), "local": set(), "relative": set()}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    top = a.name.split(".")[0]
                    if top in STDLIB:
                        result["stdlib"].add(a.name)
                    elif top in siblings:
                        result["local"].add(a.name)
                    else:
                        result["third_party"].add(a.name)
            elif isinstance(node, ast.ImportFrom):
                if node.level > 0:
                    result["relative"].add("." * node.level + (node.module or ""))
                elif node.module:
                    top = node.module.split(".")[0]
                    if top in siblings:
                        result["local"].add(node.module)
                    elif top in STDLIB:
                        result["stdlib"].add(node.module)
                    else:
                        result["third_party"].add(node.module)
        return {k: sorted(v) for k, v in result.items()}

    def todos_of(self, path: Path) -> list:
        pat = re.compile(r"#\s*(TODO|FIXME|XXX|BUG|HACK)\b[:]?(.*)", re.IGNORECASE)
        out = []
        for i, line in enumerate(path.read_text().splitlines(), 1):
            m = pat.search(line)
            if m:
                out.append((i, m.group(1).upper(), m.group(2).strip()))
        return out

    def deadcode(self, path: Path) -> list:
        """Candidates only: names defined but never referenced by name.
        Attribute-called methods may appear here — static analysis limit."""
        tree = self.parse(path)
        defined = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                defined[node.name] = node.lineno
        used = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        dead = [(n, ln) for n, ln in defined.items()
                if n not in used and not n.startswith("__")]
        return sorted(dead, key=lambda x: x[1])

    def complexity(self, path: Path) -> list:
        tree = self.parse(path)
        out = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                c = 1
                for sub in ast.walk(node):
                    if isinstance(sub, (ast.If, ast.For, ast.While,
                                        ast.ExceptHandler, ast.With)):
                        c += 1
                    elif isinstance(sub, ast.BoolOp):
                        c += len(sub.values) - 1
                out.append((node.name, node.lineno, c))
        return sorted(out, key=lambda x: -x[2])

    def loc_stats(self, path: Path) -> dict:
        lines = path.read_text().splitlines()
        code = blank = comment = 0
        for l in lines:
            s = l.strip()
            if not s:
                blank += 1
            elif s.startswith("#"):
                comment += 1
            else:
                code += 1
        tree = self.parse(path)
        funcs = sum(1 for n in ast.walk(tree)
                   if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)))
        classes = sum(1 for n in ast.walk(tree) if isinstance(n, ast.ClassDef))
        return {"lines": len(lines), "code": code, "blank": blank,
                "comment": comment, "functions": funcs, "classes": classes}

    def docstring_report(self, path: Path) -> list:
        tree = self.parse(path)
        out = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if ast.get_docstring(node) is None:
                    out.append((node.lineno, node.name))
        return sorted(out)

    def explain_error(self, path: Path) -> dict:
        try:
            ast.parse(path.read_text())
            return {"valid": True}
        except SyntaxError as e:
            lines = path.read_text().splitlines()
            ctx = []
            lo = max(0, (e.lineno or 1) - 2)
            hi = min(len(lines), (e.lineno or 1) + 1)
            for i in range(lo, hi):
                mark = "->" if i + 1 == e.lineno else "  "
                ctx.append(f"{mark} {i+1:4d}| {lines[i]}")
            return {"valid": False, "line": e.lineno, "col": e.offset,
                    "error": e.msg, "context": ctx}

    def shebangs_dir(self, root: Path) -> list:
        results = []
        for p in self.py_files(root):
            with p.open() as f:
                first = f.readline().strip()
            if first.startswith("#!"):
                interp = first[2:]
                ok = Path(interp).is_absolute() and Path(interp).exists()
                results.append((p, interp, ok))
        return results

    def deps(self, path: Path) -> list:
        return self.imports_of(path)["third_party"]

    def call_map(self, path: Path) -> dict:
        tree = self.parse(path)
        m = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                calls = set()
                for n in ast.walk(node):
                    if isinstance(n, ast.Call):
                        if isinstance(n.func, ast.Name):
                            calls.add(n.func.id)
                        elif isinstance(n.func, ast.Attribute):
                            calls.add("." + getattr(n.func, "attr", "?"))
                m[node.name] = sorted(calls)
        return m

    def longest_functions(self, path: Path) -> list:
        tree = self.parse(path)
        out = []
        for n in ast.walk(tree):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.end_lineno:
                out.append((n.name, n.lineno, (n.end_lineno - n.lineno) + 1))
        return sorted(out, key=lambda x: -x[2])

    def bare_excepts(self, path: Path) -> list:
        tree = self.parse(path)
        out = []
        for n in ast.walk(tree):
            if isinstance(n, ast.ExceptHandler):
                name = n.type.id if isinstance(n.type, ast.Name) else None
                if n.type is None or name in ("Exception", "BaseException"):
                    swallows = any(isinstance(s, ast.Pass) for s in n.body)
                    out.append((n.lineno, "bare" if n.type is None else name, swallows))
        return out

    def secrets_scan(self, path: Path) -> list:
        pat = re.compile(
            r"(?i)(password|passwd|pwd|token|secret|api[_-]?key)\s*[=:]\s*['\"][^'\"]{3,}")
        out = []
        for i, line in enumerate(path.read_text().splitlines(), 1):
            if pat.search(line):
                out.append((i, line.strip()))
        return out

    def main_guard(self, path: Path) -> dict:
        tree = self.parse(path)
        has = False
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                src = ast.dump(node.test)
                if "__name__" in src and "__main__" in src:
                    has = True
        return {"has_main_guard": has}

    def globals_audit(self, path: Path) -> list:
        tree = self.parse(path)
        out = []
        for node in tree.body:
            if isinstance(node, ast.Assign):
                val = node.value
                mutable = isinstance(val, (ast.List, ast.Dict, ast.Set,
                                           ast.ListComp, ast.DictComp, ast.SetComp))
                names = [t.id for t in node.targets if isinstance(t, ast.Name)]
                out.append((node.lineno, ", ".join(names),
                            "mutable" if mutable else "immutable"))
        return out

    def magic_numbers(self, path: Path) -> list:
        COMMON = {0, 1, 2, -1, 3, 4, 8, 10, 16, 32, 64, 100, 1000}
        tree = self.parse(path)
        found = []
        for node in ast.walk(tree):
            if (isinstance(node, ast.Constant)
                    and isinstance(node.value, (int, float))
                    and not isinstance(node.value, bool)
                    and node.value not in COMMON):
                found.append((node.lineno, node.value))
        return sorted(set(found), key=lambda x: x[0])

    def compare_symbols(self, a: Path, b: Path) -> dict:
        try:
            sa = {(k, n) for k, n, _ in self.outline(a)}
            sb = {(k, n) for k, n, _ in self.outline(b)}
        except SyntaxError as e:
            return {"error": f"line {e.lineno}, col {e.offset}: {e.msg}"}
        return {"only_a": sorted(sa - sb), "only_b": sorted(sb - sa),
                "common": sorted(sa & sb)}

    def tree_summary(self, root: Path) -> dict:
        files = self.py_files(root)
        total_lines = funcs = classes = invalid = 0
        for p in files:
            if not self.check_file(p)["valid"]:
                invalid += 1
                continue
            text = p.read_text()
            total_lines += len(text.splitlines())
            for n in ast.walk(ast.parse(text)):
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    funcs += 1
                elif isinstance(n, ast.ClassDef):
                    classes += 1
        return {"files": len(files), "lines": total_lines,
                "functions": funcs, "classes": classes, "invalid": invalid}

    def health_score(self, path: Path) -> dict:
        r = self.check_file(path)
        if not r["valid"]:
            return {"score": 0, "reason": f"syntax error at line {r.get('line')}"}
        docs_missing = len(self.docstring_report(path))
        bare = len(self.bare_excepts(path))
        td = len(self.todos_of(path))
        hotspots = len([c for _, _, c in self.complexity(path) if c > 10])
        penalty = 5 * docs_missing + 10 * bare + 3 * td + 10 * hotspots
        return {"score": max(0, 100 - penalty), "docstrings_missing": docs_missing,
                "bare_excepts": bare, "todos": td, "complexity_hotspots": hotspots}