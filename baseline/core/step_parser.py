"""Backward-compatible re-exports from ``src.utils.steps.parser``.

The canonical implementation now lives in ``src/utils/steps/parser.py``.
This module exists so that existing ``baseline`` code and the CLI parser
continue to work without import changes.
"""

from src.utils.steps.parser import (  # noqa: F401
    PLACEHOLDER_RE,
    PARSER_KIND_CFPARSE,
    PARSER_KIND_LITERAL,
    PARSER_KIND_PARSE,
    PARSER_KIND_RE,
    REGEX_NAMED_GROUP_RE,
    StepIdCounter,
    build_step_id,
    extract_placeholders,
    extract_placeholders_auto,
    extract_regex_placeholders,
    parse_steps_directory,
    parse_steps_file,
    substitute_pattern,
)
