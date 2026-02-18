"""Parser for pytest-bdd step decorators from Python files."""

import hashlib
import os
import re
from pathlib import Path
from typing import Optional, Union


PLACEHOLDER_RE = re.compile(r"\{(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)(?::(?P<type>[^}]+))?\}")
DECORATOR_RE = re.compile(r"@(given|when|then|step)\s*\(", re.IGNORECASE)


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


def build_step_id(*, step_type: Union[str, list[str]], pattern: str, source_file: str, function_name: str | None) -> str:
    """Build deterministic step id used for retrieval and rendering."""
    if isinstance(step_type, list):
        type_str = ",".join(sorted(step_type))
    else:
        type_str = step_type

    payload = f"{type_str}|{pattern}|{source_file}|{function_name or ''}"
    digest = hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]
    prefix = "step" if isinstance(step_type, list) else step_type
    return f"{prefix}_{digest}"


def _extract_pattern(decorator_line: str) -> Optional[str]:
    """Extract the step pattern string from a decorator line."""
    parse_match = re.search(r'parsers\.parse\s*\(\s*[\'"](.+?)[\'"]\s*\)', decorator_line)
    if parse_match:
        return parse_match.group(1)

    simple_match = re.search(
        r'@(?:given|when|then|step)\s*\(\s*[\'"](.+?)[\'"]\s*\)',
        decorator_line,
        re.IGNORECASE,
    )
    if simple_match:
        return simple_match.group(1)
    return None


def _extract_decorator_type(decorator_line: str) -> Optional[str]:
    """Extract decorator type (given/when/then/step) from a line."""
    m = DECORATOR_RE.match(decorator_line.strip())
    return m.group(1).lower() if m else None


def parse_steps_file(file_path: str) -> list[dict]:
    """Parse one Python file and extract BDD steps.

    Groups consecutive decorators that belong to the same function into a
    single step entry with a merged ``type`` field.
    """
    steps: list[dict] = []
    try:
        lines = Path(file_path).read_text(encoding="utf-8").splitlines()
    except (IOError, UnicodeDecodeError) as exc:
        print(f"Ошибка чтения файла {file_path}: {exc}")
        return steps

    source_file = os.path.basename(file_path)
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        dec_type = _extract_decorator_type(stripped)
        if dec_type is None:
            i += 1
            continue

        # Collect all consecutive decorator lines for the same function
        collected_types: set[str] = set()
        pattern: Optional[str] = None
        first_line = i + 1  # 1-based

        while i < len(lines):
            stripped = lines[i].strip()
            dt = _extract_decorator_type(stripped)
            if dt is None:
                break
            if dt == "step":
                collected_types.update(["given", "when", "then"])
            else:
                collected_types.add(dt)
            p = _extract_pattern(stripped)
            if p and pattern is None:
                pattern = p
            i += 1

        if not pattern:
            continue

        # Now find the function definition in the next few lines
        function_name = None
        docstring = None
        for j in range(i, min(i + 5, len(lines))):
            func_match = re.match(r"\s*def\s+(\w+)\s*\(", lines[j])
            if func_match:
                function_name = func_match.group(1)
                for k in range(j + 1, min(j + 5, len(lines))):
                    doc_line = lines[k].strip()
                    if doc_line.startswith('"""') or doc_line.startswith("'''"):
                        doc_match = re.match(r'[\'\"]{3}(.+?)[\'\"]{3}', doc_line)
                        docstring = doc_match.group(1) if doc_match else doc_line.strip('"\' ')
                        break
                break

        # Build the merged type field
        sorted_types = sorted(collected_types)
        step_type: Union[str, list[str]]
        if len(sorted_types) == 1:
            step_type = sorted_types[0]
        else:
            step_type = sorted_types

        step_info = {
            "type": step_type,
            "pattern": pattern,
            "function_name": function_name,
            "docstring": docstring,
            "placeholders": extract_placeholders(pattern),
            "source_file": source_file,
            "line_number": first_line,
            "step_id": build_step_id(
                step_type=step_type,
                pattern=pattern,
                source_file=source_file,
                function_name=function_name,
            ),
        }
        steps.append(step_info)

    return steps


def parse_steps_directory(directory_path: str) -> dict:
    """Parse all Python files in directory and aggregate step stats."""
    directory = Path(directory_path)
    if not directory.exists():
        raise FileNotFoundError(f"Директория не найдена: {directory_path}")
    if not directory.is_dir():
        raise NotADirectoryError(f"Путь не является директорией: {directory_path}")

    result = {
        "total_steps": 0,
        "steps_by_type": {"given": 0, "when": 0, "then": 0},
        "files_parsed": [],
        "steps": [],
    }

    for py_file in directory.glob("*.py"):
        file_steps = parse_steps_file(str(py_file))
        if not file_steps:
            continue

        result["files_parsed"].append({"file": py_file.name, "steps_count": len(file_steps)})
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
