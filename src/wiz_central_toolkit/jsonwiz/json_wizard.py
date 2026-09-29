"""json-wizard core: standalone, importable JSON doctor. Validate, pretty-print, inspect."""
import json


class JsonWizard:
    """JSON validation and inspection engine. Never modifies the input file."""

    def validate(self, source: str) -> dict:
        try:
            parsed = json.loads(source)
        except json.JSONDecodeError as e:
            return {"valid": False, "error": str(e), "line": e.lineno, "col": e.colno}
        return {"valid": True, "type": type(parsed).__name__}

    def pretty(self, source: str, indent: int = 2) -> str:
        return json.dumps(json.loads(source), indent=indent)

    def inspect(self, source: str) -> dict:
        parsed = json.loads(source)

        def summarize(obj):
            if isinstance(obj, dict):
                return {k: summarize(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return {"_list_len": len(obj)}
            return obj

        return summarize(parsed)

    def keys(self, source: str) -> list:
        parsed = json.loads(source)
        if isinstance(parsed, dict):
            return list(parsed.keys())
        return []

    def compact(self, source: str) -> str:
        return json.dumps(json.loads(source), separators=(",", ":"))

    def get(self, source: str, path: str):
        """Dotted-path lookup. Numeric segments index arrays."""
        node = json.loads(source)
        for seg in path.split("."):
            if isinstance(node, dict) and seg in node:
                node = node[seg]
            elif isinstance(node, list) and seg.lstrip("-").isdigit():
                idx = int(seg)
                if -len(node) <= idx < len(node):
                    node = node[idx]
                else:
                    raise IndexError(f"index {seg} out of range")
            else:
                raise KeyError(f"path segment not found: {seg}")
        return node

    def diff(self, source_a: str, source_b: str) -> list:
        """Structural diff: list of paths where the docs differ."""
        a = json.loads(source_a)
        b = json.loads(source_b)
        changes = []

        def walk(x, y, path):
            if isinstance(x, dict) and isinstance(y, dict):
                for k in sorted(set(x) | set(y)):
                    if k not in x:
                        changes.append(("added", path + [k], None, y[k]))
                    elif k not in y:
                        changes.append(("removed", path + [k], x[k], None))
                    else:
                        walk(x[k], y[k], path + [k])
            elif isinstance(x, list) and isinstance(y, list):
                for i in range(max(len(x), len(y))):
                    if i >= len(x):
                        changes.append(("added", path + [i], None, y[i]))
                    elif i >= len(y):
                        changes.append(("removed", path + [i], x[i], None))
                    else:
                        walk(x[i], y[i], path + [i])
            elif x != y:
                changes.append(("changed", path, x, y))

        walk(a, b, [])
        return changes

    def stats(self, source: str) -> dict:
        parsed = json.loads(source)
        counts = {"dict": 0, "list": 0, "str": 0, "number": 0, "bool": 0, "null": 0}

        def walk(obj, depth):
            max_d = depth
            if isinstance(obj, dict):
                counts["dict"] += 1
                for v in obj.values():
                    max_d = max(max_d, walk(v, depth + 1))
            elif isinstance(obj, list):
                counts["list"] += 1
                for v in obj:
                    max_d = max(max_d, walk(v, depth + 1))
            elif isinstance(obj, str):
                counts["str"] += 1
            elif isinstance(obj, bool):
                counts["bool"] += 1
            elif obj is None:
                counts["null"] += 1
            else:
                counts["number"] += 1
            return max_d

        depth = walk(parsed, 0)
        root_keys = len(parsed) if isinstance(parsed, dict) else None
        return {
            "root_type": type(parsed).__name__,
            "root_keys": root_keys,
            "max_depth": depth,
            **counts,
        }

    def merge(self, source_a: str, source_b: str) -> dict:
        """Deep merge: b wins on scalars, dicts merge recursively, lists replace."""
        a = json.loads(source_a)
        b = json.loads(source_b)
        if not isinstance(a, dict) or not isinstance(b, dict):
            raise TypeError("merge requires two root objects")
        return self._deep_merge(a, b)

    @staticmethod
    def _deep_merge(a: dict, b: dict) -> dict:
        out = dict(a)
        for k, v in b.items():
            if isinstance(v, dict) and isinstance(out.get(k), dict):
                out[k] = JsonWizard._deep_merge(out[k], v)
            else:
                out[k] = v
        return out