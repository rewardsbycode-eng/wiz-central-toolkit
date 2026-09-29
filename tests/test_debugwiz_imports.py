"""Regression tests for debugwiz's undefined-name / missing-import detection."""
from pathlib import Path

from wiz_central_toolkit.debugwiz import debug_wizard


def _missing(tmp_path: Path, source: str) -> list[str]:
    f = tmp_path / "sample.py"
    f.write_text(source)
    return debug_wizard.names(f)


def test_relative_import_does_not_crash(tmp_path):
    assert _missing(tmp_path, "from . import helper\nhelper()\n") == []


def test_relative_import_with_module(tmp_path):
    assert _missing(tmp_path, "from .pkg import thing\nthing()\n") == []


def test_locals_and_functions_are_not_flagged(tmp_path):
    src = "def add(a, b):\n    total = a + b\n    return total\n\nresult = add(1, 2)\nprint(result)\n"
    assert _missing(tmp_path, src) == []


def test_undefined_name_is_reported(tmp_path):
    assert _missing(tmp_path, "print(undefined_thing)\n") == ["undefined_thing"]


def test_dotted_import_binds_top_level_name(tmp_path):
    assert _missing(tmp_path, "import os.path\nprint(os.path.join('a', 'b'))\n") == []


def test_multi_import_binds_every_name(tmp_path):
    assert _missing(tmp_path, "import os, sys\nprint(os.name, sys.platform)\n") == []


def test_alias_binds_alias(tmp_path):
    assert _missing(tmp_path, "import json as j\nprint(j.dumps({}))\n") == []


def test_comprehension_lambda_except_with_walrus(tmp_path):
    src = (
        "squares = [n * n for n in range(3)]\n"
        "f = lambda x: x + 1\n"
        "try:\n    pass\nexcept ValueError as err:\n    print(err)\n"
        "with open('x') as fh:\n    fh.read()\n"
        "if (m := len(squares)) > 1:\n    print(m)\n"
    )
    assert _missing(tmp_path, src) == []


def test_star_import_disables_detection(tmp_path):
    assert _missing(tmp_path, "from os.path import *\nprint(join('a'))\n") == []


def test_syntax_error_returns_empty(tmp_path):
    assert _missing(tmp_path, "def f(:\n") == []


def test_imports_result_shape(tmp_path):
    f = tmp_path / "sample.py"
    f.write_text("print(nope)\n")
    assert debug_wizard.imports(f) == {"file": str(f), "likely_missing": ["nope"]}
