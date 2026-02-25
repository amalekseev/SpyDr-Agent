"""Static validation of docstring content by language (for BDD step docstrings)."""

from __future__ import annotations

import ast
import json
from xml.etree import ElementTree

import sqlglot


def validate_docstring_content(content: str, lang: str) -> list[str]:
    """Statically validate docstring content for the given language.

    Returns a list of error strings (empty if valid).
    Validator is resolved by convention: _validate_{lang}().
    """
    content = content or ""
    lang_lower = lang.strip().lower()

    validator = globals().get(f"_validate_{lang_lower}")
    if validator is None:
        return [f"Unknown docstring language: {lang}"]
    return validator(content)


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


def _validate_sql(content: str) -> list[str]:
    errors: list[str] = []
    try:
        parsed = sqlglot.transpile(content, error_level=sqlglot.ErrorLevel.RAISE)
    except sqlglot.errors.ParseError as e:
        for err in e.errors:
            desc = err.get("description", str(e))
            line = err.get("line")
            col = err.get("col")
            loc = f"line {line}, col {col}: " if line is not None else ""
            errors.append(f"SQL: {loc}{desc}")
    if not errors:
        if not parsed or all(not s.strip() for s in parsed):
            errors.append("SQL: empty or blank statement")
    return errors
