"""Parser for pytest-bdd step decorators from Python files."""

import hashlib
import os
import re
from pathlib import Path
from typing import Optional


PLACEHOLDER_RE = re.compile(r"\{(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)(?::(?P<type>[^}]+))?\}")


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


def build_step_id(*, step_type: str, pattern: str, source_file: str, function_name: str | None) -> str:
    """Build deterministic step id used for retrieval and rendering."""
    payload = f"{step_type}|{pattern}|{source_file}|{function_name or ''}"
    digest = hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]
    return f"{step_type}_{digest}"


def parse_step_pattern(decorator_line: str, next_lines: list[str]) -> Optional[dict]:
    """Parse decorator line and return structured step info."""
    step_type_match = re.match(r"@(given|when|then|step)\s*\(", decorator_line, re.IGNORECASE)
    if not step_type_match:
        return None

    step_type = step_type_match.group(1).lower()
    pattern = None

    parse_match = re.search(r'parsers\.parse\s*\(\s*[\'"](.+?)[\'"]\s*\)', decorator_line)
    if parse_match:
        pattern = parse_match.group(1)
    else:
        simple_match = re.search(
            r'@(?:given|when|then|step)\s*\(\s*[\'"](.+?)[\'"]\s*\)',
            decorator_line,
            re.IGNORECASE,
        )
        if simple_match:
            pattern = simple_match.group(1)

    if not pattern:
        return None

    function_name = None
    docstring = None
    for i, line in enumerate(next_lines):
        func_match = re.match(r"def\s+(\w+)\s*\(", line)
        if func_match:
            function_name = func_match.group(1)
            for j in range(i + 1, min(i + 5, len(next_lines))):
                doc_line = next_lines[j].strip()
                if doc_line.startswith('"""') or doc_line.startswith("'''"):
                    doc_match = re.match(r'[\'\"]{3}(.+?)[\'\"]{3}', doc_line)
                    docstring = doc_match.group(1) if doc_match else doc_line.strip('"\' ')
                    break
            break

    return {
        "type": step_type,
        "pattern": pattern,
        "function_name": function_name,
        "docstring": docstring,
        "placeholders": extract_placeholders(pattern),
    }


def parse_steps_file(file_path: str) -> list[dict]:
    """Parse one Python file and extract BDD steps."""
    steps: list[dict] = []
    try:
        lines = Path(file_path).read_text(encoding="utf-8").splitlines()
    except (IOError, UnicodeDecodeError) as exc:
        print(f"Ошибка чтения файла {file_path}: {exc}")
        return steps

    for i, line in enumerate(lines):
        stripped = line.strip()
        if re.match(r"@(given|when|then|step)\s*\(", stripped, re.IGNORECASE):
            next_lines = [l.strip() for l in lines[i + 1 : i + 10]]
            step_info = parse_step_pattern(stripped, next_lines)
            if step_info:
                step_info["source_file"] = os.path.basename(file_path)
                step_info["line_number"] = i + 1
                step_info["step_id"] = build_step_id(
                    step_type=step_info["type"],
                    pattern=step_info["pattern"],
                    source_file=step_info["source_file"],
                    function_name=step_info.get("function_name"),
                )
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
        "steps_by_type": {"given": 0, "when": 0, "then": 0, "step": 0},
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
            result["steps_by_type"][step["type"]] += 1
        result["total_steps"] += len(file_steps)

    return result

