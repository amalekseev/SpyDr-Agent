"""Static validation of docstring content by language (for BDD step docstrings)."""

from __future__ import annotations

import ast
import json
from xml.etree import ElementTree


def validate_docstring_content(content: str, lang: str) -> list[str]:
    """Statically validate docstring content for the given language.

    Returns a list of error strings (empty if valid).
    Supported languages: python, json, xml, sql.
    """
    content = content or ""
    lang_lower = lang.strip().lower()

    if lang_lower == "json":
        return _validate_json(content)
    if lang_lower == "xml":
        return _validate_xml(content)
    if lang_lower == "python":
        return _validate_python(content)
    if lang_lower == "sql":
        return _validate_sql(content)

    return [f"Unknown docstring language: {lang}"]


def _validate_json(content: str) -> list[str]:
    errors: list[str] = []
    try:
        json.loads(content)
    except json.JSONDecodeError as e:
        errors.append(f"JSON: line {e.lineno}, column {e.colno}: {e.msg}")
    return errors


def _validate_xml(content: str) -> list[str]:
    errors: list[str] = []
    try:
        ElementTree.fromstring(content)
    except ElementTree.ParseError as e:
        errors.append(f"XML: {e}")
    return errors


def _validate_python(content: str) -> list[str]:
    errors: list[str] = []
    try:
        ast.parse(content)
    except SyntaxError as e:
        errors.append(f"Python: line {e.lineno or '?'}: {e.msg}")
    return errors


def _balance_check(
    content: str,
    open_chars: str,
    close_chars: str,
    lang_name: str,
) -> list[str]:
    """Check that bracket/brace counts are balanced. Returns list of errors."""
    errors: list[str] = []
    if len(open_chars) != len(close_chars):
        return errors
    stack: list[tuple[str, int]] = []
    line = 1
    col = 0
    i = 0
    in_single = False
    in_double = False
    escape = False
    while i < len(content):
        c = content[i]
        if escape:
            escape = False
            i += 1
            col += 1
            continue
        if c == "\\" and (in_single or in_double):
            escape = True
            i += 1
            col += 1
            continue
        if not in_single and not in_double:
            if c == "'" and (i == 0 or content[i - 1] != "\\"):
                in_single = True
            elif c == '"':
                in_double = True
            elif c in open_chars:
                idx = open_chars.index(c)
                stack.append((close_chars[idx], line))
            elif c in close_chars:
                if not stack:
                    errors.append(f"{lang_name}: unexpected closing '{c}' at line {line}, column {col}")
                    return errors
                expected, _ = stack.pop()
                if c != expected:
                    errors.append(f"{lang_name}: mismatched bracket at line {line} (expected '{expected}', got '{c}')")
                    return errors
        elif c == "'" and in_single:
            in_single = False
        elif c == '"' and in_double:
            in_double = False
        if c == "\n":
            line += 1
            col = 0
        else:
            col += 1
        i += 1
    if in_single or in_double:
        errors.append(f"{lang_name}: unclosed string literal")
    elif stack:
        _, open_line = stack[-1]
        errors.append(f"{lang_name}: unclosed bracket starting at line {open_line}")
    return errors


def _validate_sql(content: str) -> list[str]:
    return _balance_check(content, "([{", ")]}", "SQL")
