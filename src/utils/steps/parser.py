"""AST-based parser for pytest-bdd step decorators.

Extracts step definitions, placeholders, and metadata from Python source
files that use ``@given``, ``@when``, ``@then``, ``@step`` decorators.
Handles ``parsers.parse()``, ``parsers.cfparse()``, ``parsers.re()`` as well
as bare string literals.
"""

from __future__ import annotations

import ast
import os
import re
from pathlib import Path
from typing import Optional, Union

# ---------------------------------------------------------------------------
# Constants & regexes
# ---------------------------------------------------------------------------

#: Matches ``{name}`` or ``{name:type}`` — used by parsers.parse / cfparse.
PLACEHOLDER_RE = re.compile(
    r"\{(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)(?::(?P<type>[^}]+))?\}"
)

#: Matches ``(?P<name>...)`` — named groups used by parsers.re().
REGEX_NAMED_GROUP_RE = re.compile(
    r"\(\?P<(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)>(?P<subpattern>[^)]*)\)"
)

_STEP_DECORATOR_NAMES = frozenset({"given", "when", "then", "step"})

STEP_TYPE_PREFIX = {"given": "G", "when": "W", "then": "T", "step": "S"}

# Parser kinds recognised by the extraction logic.
PARSER_KIND_LITERAL = "literal"
PARSER_KIND_PARSE = "parse"
PARSER_KIND_CFPARSE = "cfparse"
PARSER_KIND_RE = "re"

_PARSER_FUNC_NAMES: dict[str, str] = {
    "parse": PARSER_KIND_PARSE,
    "cfparse": PARSER_KIND_CFPARSE,
    "re": PARSER_KIND_RE,
}

_PARSER_KIND_PRIORITY = {
    PARSER_KIND_LITERAL: 0,
    PARSER_KIND_PARSE: 1,
    PARSER_KIND_CFPARSE: 2,
    PARSER_KIND_RE: 3,
}

# ---------------------------------------------------------------------------
# Step-ID counter
# ---------------------------------------------------------------------------


class StepIdCounter:
    """Sequential counter that produces step IDs like ``G-1``, ``W-2``."""

    def __init__(self, start: int = 1) -> None:
        self._next = start

    def next_id(self, step_type: str) -> str:
        type_prefix = STEP_TYPE_PREFIX.get(step_type.lower(), step_type[0].upper())
        step_id = f"{type_prefix}-{self._next}"
        self._next += 1
        return step_id

    @property
    def current(self) -> int:
        return self._next


# ---------------------------------------------------------------------------
# Placeholder extraction
# ---------------------------------------------------------------------------


def extract_placeholders(pattern: str) -> list[dict]:
    """Extract ``{name}`` / ``{name:Type}`` placeholders (parse/cfparse)."""
    return [
        {"name": m.group("name"), "type": m.group("type") or "str"}
        for m in PLACEHOLDER_RE.finditer(pattern)
    ]


def extract_regex_placeholders(
    pattern: str,
    converters: Optional[dict[str, str]] = None,
) -> list[dict]:
    """Extract ``(?P<name>...)`` placeholders from a regex pattern.

    *converters* (e.g. ``{"start": "int"}``) supplies types; defaults to
    ``"str"`` when absent.
    """
    converters = converters or {}
    return [
        {"name": m.group("name"), "type": converters.get(m.group("name"), "str")}
        for m in REGEX_NAMED_GROUP_RE.finditer(pattern)
    ]


def extract_placeholders_auto(
    pattern: str,
    parser_kind: str,
    converters: Optional[dict[str, str]] = None,
) -> list[dict]:
    """Select the right placeholder extractor based on *parser_kind*."""
    if parser_kind == PARSER_KIND_RE:
        return extract_regex_placeholders(pattern, converters)
    return extract_placeholders(pattern)


# ---------------------------------------------------------------------------
# Pattern rendering (substitution)
# ---------------------------------------------------------------------------


def substitute_pattern(
    pattern: str,
    params: dict[str, object],
    parser_kind: str = PARSER_KIND_PARSE,
) -> str:
    """Replace placeholders in *pattern* with concrete values from *params*.

    Handles both ``{name}`` (parse / cfparse / literal) and ``(?P<name>...)``
    (re) styles.
    """

    def _fmt(val: object) -> str:
        if isinstance(val, bool):
            return "true" if val else "false"
        return "" if val is None else str(val)

    if parser_kind == PARSER_KIND_RE:
        def _replace_re(match: re.Match) -> str:
            return _fmt(params.get(match.group("name"), match.group(0)))
        return REGEX_NAMED_GROUP_RE.sub(_replace_re, pattern)

    def _replace_parse(match: re.Match) -> str:
        return _fmt(params.get(match.group("name"), match.group(0)))
    return PLACEHOLDER_RE.sub(_replace_parse, pattern)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def build_step_id(counter: StepIdCounter) -> str:
    """Build sequential step id like ``S-1``, ``S-2``."""
    return counter.next_id("step")


def _best_parser_kind(a: str, b: str) -> str:
    """Return the more specific parser kind."""
    return a if _PARSER_KIND_PRIORITY.get(a, 0) >= _PARSER_KIND_PRIORITY.get(b, 0) else b


# ---------------------------------------------------------------------------
# AST helpers
# ---------------------------------------------------------------------------


def _resolve_decorator_name(node: ast.expr) -> Optional[str]:
    """Return lowercase decorator name if it is a BDD step decorator call."""
    if isinstance(node, ast.Call):
        node = node.func
    if isinstance(node, ast.Name):
        name = node.id.lower()
    elif isinstance(node, ast.Attribute):
        name = node.attr.lower()
    else:
        return None
    return name if name in _STEP_DECORATOR_NAMES else None


def _resolve_parser_kind(node: ast.expr) -> str:
    """Determine parser kind from the decorator's first positional arg.

    Examples::

        @given("pattern")                    → literal
        @given(parsers.parse("pattern"))     → parse
        @given(parsers.cfparse("pattern"))   → cfparse
        @given(parsers.re(r"pattern"))       → re
        @given(parse("pattern"))             → parse   (direct import)
    """
    if isinstance(node, ast.Constant):
        return PARSER_KIND_LITERAL

    if isinstance(node, ast.Call):
        func = node.func
        if isinstance(func, ast.Attribute):
            kind = _PARSER_FUNC_NAMES.get(func.attr.lower())
            if kind:
                return kind
        if isinstance(func, ast.Name):
            kind = _PARSER_FUNC_NAMES.get(func.id.lower())
            if kind:
                return kind

    return PARSER_KIND_LITERAL


def _extract_pattern_from_arg(arg: ast.expr) -> Optional[str]:
    """Extract the string pattern from a decorator's first positional arg."""
    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
        return arg.value

    if isinstance(arg, ast.Call) and arg.args:
        first_inner = arg.args[0]
        if isinstance(first_inner, ast.Constant) and isinstance(first_inner.value, str):
            return first_inner.value

    return None


def _extract_converters(decorator: ast.Call) -> dict[str, str]:
    """Extract ``converters={...}`` keyword arg from a step decorator.

    Returns a mapping *name → type_name* (e.g. ``{"start": "int"}``).
    """
    converters: dict[str, str] = {}
    for kw in decorator.keywords:
        if kw.arg != "converters":
            continue
        if not isinstance(kw.value, ast.Dict):
            break
        for key_node, val_node in zip(kw.value.keys, kw.value.values):
            if not isinstance(key_node, ast.Constant) or not isinstance(key_node.value, str):
                continue
            if isinstance(val_node, ast.Name):
                converters[key_node.value] = val_node.id
            elif isinstance(val_node, ast.Constant) and isinstance(val_node.value, str):
                converters[key_node.value] = val_node.value
        break
    return converters


def _get_docstring(node: ast.FunctionDef) -> Optional[str]:
    """Return the docstring of a function or ``None``."""
    if (
        node.body
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
        and isinstance(node.body[0].value.value, str)
    ):
        return node.body[0].value.value.strip()
    return None


def _function_param_names(node: ast.FunctionDef) -> list[str]:
    """Return positional parameter names for a function."""
    return [a.arg for a in node.args.args]


# ---------------------------------------------------------------------------
# File / directory level parsing
# ---------------------------------------------------------------------------


def parse_steps_file(
    file_path: str,
    counter: Optional[StepIdCounter] = None,
) -> list[dict]:
    """Parse one Python file and extract BDD steps using AST.

    Each unique *pattern* on a function becomes its own step entry.  If the
    same pattern appears in several decorators (e.g. ``@step(P)`` +
    ``@given(P)``), their types are merged.
    """
    if counter is None:
        counter = StepIdCounter()
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

        # Keyed by pattern string → (types, parser_kind, converters)
        pattern_meta: dict[str, tuple[set[str], str, dict[str, str]]] = {}

        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue

            dec_name = _resolve_decorator_name(decorator)
            if dec_name is None:
                continue

            pat: Optional[str] = None
            parser_kind = PARSER_KIND_LITERAL
            if decorator.args:
                pat = _extract_pattern_from_arg(decorator.args[0])
                parser_kind = _resolve_parser_kind(decorator.args[0])
            if pat is None:
                continue

            converters = _extract_converters(decorator)

            if pat not in pattern_meta:
                pattern_meta[pat] = (set(), parser_kind, converters)

            types_set = pattern_meta[pat][0]
            merged_converters = {**pattern_meta[pat][2], **converters}
            existing_kind = pattern_meta[pat][1]
            best_kind = _best_parser_kind(existing_kind, parser_kind)
            pattern_meta[pat] = (types_set, best_kind, merged_converters)

            if dec_name == "step":
                types_set.update(["given", "when", "then"])
            else:
                types_set.add(dec_name)

        if not pattern_meta:
            continue

        param_names = _function_param_names(node)
        has_datatable = "datatable" in param_names
        has_docstring = "docstring" in param_names
        func_docstring = _get_docstring(node)

        for pattern, (types, p_kind, convs) in pattern_meta.items():
            sorted_types = sorted(types)
            step_type: Union[str, list[str]]
            if len(sorted_types) == 1:
                step_type = sorted_types[0]
            else:
                step_type = sorted_types

            step_info: dict = {
                "type": step_type,
                "pattern": pattern,
                "parser_kind": p_kind,
                "function_name": node.name,
                "docstring": func_docstring,
                "placeholders": extract_placeholders_auto(pattern, p_kind, convs),
                "source_file": source_file,
                "line_number": node.lineno,
                "step_id": build_step_id(counter),
            }

            if convs:
                step_info["converters"] = convs
            if has_datatable:
                step_info["requires_datatable"] = True
            if has_docstring:
                step_info["requires_docstring"] = True

            steps.append(step_info)

    return steps


def parse_steps_directory(directory_path: str, *, start_id: int = 1) -> dict:
    """Parse all Python files in a directory and aggregate step stats.

    Args:
        directory_path: Filesystem path to the directory with step files.
        start_id: First counter value for generated step IDs (default 1).
                  Pass a higher value so custom steps continue numbering
                  after default steps.
    """
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

    counter = StepIdCounter(start=start_id)
    for py_file in sorted(directory.glob("*.py")):
        file_steps = parse_steps_file(str(py_file), counter=counter)
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
