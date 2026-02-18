"""Parser for pytest-bdd step decorators from Python files.

Uses Python ``ast`` module for robust parsing – handles multi-line
decorators, ``parsers.parse()``, ``parsers.re()``, ``parsers.cfparse()``,
``target_fixture`` kwargs, etc. without fragile regexes.
"""

import ast
import hashlib
import os
import re
from pathlib import Path
from typing import Optional, Union


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PLACEHOLDER_RE = re.compile(
    r"\{(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)(?::(?P<type>[^}]+))?\}"
)

_STEP_DECORATOR_NAMES = frozenset({"given", "when", "then", "step"})


def extract_placeholders(pattern: str) -> list[dict]:
    """Extract placeholder names and optional parser types from step pattern."""
    placeholders: list[dict] = []
    for match in PLACEHOLDER_RE.finditer(pattern):
        placeholders.append(
            {
                "name": match.group("name"),
                "type": match.group("type") or "str",
            }
        )
    return placeholders


def build_step_id(
    *,
    step_type: Union[str, list[str]],
    pattern: str,
    source_file: str,
    function_name: str | None,
) -> str:
    """Build deterministic step id used for retrieval and rendering."""
    if isinstance(step_type, list):
        type_str = ",".join(sorted(step_type))
    else:
        type_str = step_type

    payload = f"{type_str}|{pattern}|{source_file}|{function_name or ''}"
    digest = hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]
    prefix = "step" if isinstance(step_type, list) else step_type
    return f"{prefix}_{digest}"


# ---------------------------------------------------------------------------
# AST-based extraction
# ---------------------------------------------------------------------------


def _resolve_decorator_name(node: ast.expr) -> Optional[str]:
    """Return lowercase decorator name if it is a BDD step decorator call.

    Handles:
    * ``@given(...)``  – ``ast.Name``
    * ``@parsers.given(...)`` (unlikely but safe) – ``ast.Attribute``
    """
    if isinstance(node, ast.Call):
        node = node.func
    if isinstance(node, ast.Name):
        name = node.id.lower()
    elif isinstance(node, ast.Attribute):
        name = node.attr.lower()
    else:
        return None
    return name if name in _STEP_DECORATOR_NAMES else None


def _extract_pattern_from_arg(arg: ast.expr) -> Optional[str]:
    """Extract the string pattern from a decorator's first positional arg.

    Handles:
    * Direct string literal: ``@given('pattern')``
    * ``parsers.parse('pattern')``, ``parsers.re('...')``,
      ``parsers.cfparse('...')`` and similar calls.
    * ``parse('pattern')`` when ``parse`` was imported directly.
    """
    # Direct string constant
    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
        return arg.value

    # Call to parsers.parse(...) / parsers.re(...) / parse(...)
    if isinstance(arg, ast.Call) and arg.args:
        first_inner = arg.args[0]
        if isinstance(first_inner, ast.Constant) and isinstance(first_inner.value, str):
            return first_inner.value

    # JoinedStr (f-string) – we cannot statically resolve, skip
    return None


def _get_docstring(node: ast.FunctionDef) -> Optional[str]:
    """Return single-line docstring of a function or ``None``."""
    if (
        node.body
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
        and isinstance(node.body[0].value.value, str)
    ):
        return node.body[0].value.value.strip()
    return None


def _function_param_names(node: ast.FunctionDef) -> list[str]:
    """Return the list of positional parameter names for a function."""
    return [a.arg for a in node.args.args]


# ---------------------------------------------------------------------------
# File / directory level parsers
# ---------------------------------------------------------------------------


def parse_steps_file(file_path: str) -> list[dict]:
    """Parse one Python file and extract BDD steps using AST.

    Each unique *pattern* on a function becomes its own step entry.  If the
    same pattern appears in several decorators (e.g. ``@step(P)`` +
    ``@given(P)``), their types are merged.  If one function has decorators
    with *different* patterns, each pattern produces a separate step entry
    sharing the same function metadata.
    """
    steps: list[dict] = []
    source_path = Path(file_path)
    try:
        source = source_path.read_text(encoding="utf-8")
    except (IOError, UnicodeDecodeError) as exc:
        print(f"Ошибка чтения файла {file_path}: {exc}")
        return steps

    try:
        tree = ast.parse(source, filename=file_path)
    except SyntaxError as exc:
        print(f"Синтаксическая ошибка в файле {file_path}: {exc}")
        return steps

    source_file = os.path.basename(file_path)

    for node in ast.iter_child_nodes(tree):
        if not isinstance(node, ast.FunctionDef):
            continue

        # Collect (pattern → set of types) from ALL decorators on this function
        pattern_types: dict[str, set[str]] = {}

        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue

            dec_name = _resolve_decorator_name(decorator)
            if dec_name is None:
                continue

            # Extract pattern from the first positional arg
            pat: Optional[str] = None
            if decorator.args:
                pat = _extract_pattern_from_arg(decorator.args[0])
            if pat is None:
                continue

            if pat not in pattern_types:
                pattern_types[pat] = set()

            # Expand @step into all three types
            if dec_name == "step":
                pattern_types[pat].update(["given", "when", "then"])
            else:
                pattern_types[pat].add(dec_name)

        if not pattern_types:
            continue

        # Shared function-level metadata
        param_names = _function_param_names(node)
        requires_datatable = "datatable" in param_names
        requires_docstring = "docstring" in param_names
        func_docstring = _get_docstring(node)

        # Emit one step entry per unique pattern
        for pattern, types in pattern_types.items():
            sorted_types = sorted(types)
            step_type: Union[str, list[str]]
            if len(sorted_types) == 1:
                step_type = sorted_types[0]
            else:
                step_type = sorted_types

            step_info: dict = {
                "type": step_type,
                "pattern": pattern,
                "function_name": node.name,
                "docstring": func_docstring,
                "placeholders": extract_placeholders(pattern),
                "source_file": source_file,
                "line_number": node.lineno,
                "step_id": build_step_id(
                    step_type=step_type,
                    pattern=pattern,
                    source_file=source_file,
                    function_name=node.name,
                ),
            }

            if requires_datatable:
                step_info["requires_datatable"] = True
            if requires_docstring:
                step_info["requires_docstring"] = True

            steps.append(step_info)

    return steps


def parse_steps_directory(directory_path: str) -> dict:
    """Parse all Python files in directory and aggregate step stats."""
    directory = Path(directory_path)
    if not directory.exists():
        raise FileNotFoundError(f"Директория не найдена: {directory_path}")
    if not directory.is_dir():
        raise NotADirectoryError(f"Путь не является директорией: {directory_path}")

    result: dict = {
        "total_steps": 0,
        "steps_by_type": {"given": 0, "when": 0, "then": 0},
        "files_parsed": [],
        "steps": [],
    }

    for py_file in sorted(directory.glob("*.py")):
        file_steps = parse_steps_file(str(py_file))
        if not file_steps:
            continue

        result["files_parsed"].append(
            {"file": py_file.name, "steps_count": len(file_steps)}
        )
        for step in file_steps:
            result["steps"].append(step)

            types = step["type"]
            if isinstance(types, str):
                types = [types]
            for t in types:
                if t in result["steps_by_type"]:
                    result["steps_by_type"][t] += 1

        result["total_steps"] += len(file_steps)

    return result
