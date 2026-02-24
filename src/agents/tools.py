"""Stateful scenario builder tools for SpydrAgent."""

from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any, Optional

from langchain.tools import tool, ToolRuntime
from langchain.messages import ToolMessage
from langgraph.types import Command

from src.configs import global_config
from src.utils.streaming import set_status, stream_artifact, stream_text
from src.utils.embeddings import get_vector_store, embed_model
from src.agents.models import ScenarioDraft, StepChoice
from src.utils.steps import (
    get_step_def,
    get_steps_index,
    validate_step_params,
    requires_docstring,
    requires_datatable,
    PLACEHOLDER_RE,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cmd(runtime: ToolRuntime, content: str, **state_updates) -> Command:
    """Build a Command that updates state fields and returns a ToolMessage."""
    return Command(
        update={
            **state_updates,
            "messages": [
                ToolMessage(content=content, tool_call_id=runtime.tool_call_id)
            ],
        }
    )


def _stream_feature_preview(runtime: ToolRuntime, **overrides: Any) -> None:
    """Render current feature state and stream it as an artifact.

    Merges *overrides* (the about-to-be-committed state updates) on top of
    the current runtime state so the preview reflects the latest change.
    Silently skips if the feature cannot be rendered yet (no title, etc.).
    """
    state = runtime.state
    title: str = overrides.get("feature_title", state.get("feature_title", ""))
    tags: list[str] = overrides.get("feature_tags", state.get("feature_tags", []))
    scenarios: list[ScenarioDraft] = overrides.get("scenarios", state.get("scenarios") or [])

    if not title:
        logger.debug("_stream_feature_preview: no title, skipping")
        return

    steps_index = get_steps_index()

    try:
        feature_text = _render_feature(title, tags, scenarios, steps_index)
    except Exception as exc:
        logger.warning("_stream_feature_preview: render failed: %s", exc)
        return

    logger.info("_stream_feature_preview: streaming artifact (%d chars)", len(feature_text))
    stream_artifact(feature_text)


# ---------------------------------------------------------------------------
# 1. search_steps  (read-only)
# ---------------------------------------------------------------------------

@tool
async def search_steps(
    runtime: ToolRuntime,
    queries: list[str],
    top_k: Optional[int] = None,
) -> Command:
    """Семантический поиск BDD шагов в векторной базе по нескольким запросам одновременно.
    Результаты дедуплицируются по step_id и сохраняются в состояние агента.

    Args:
        queries: Список описаний нужных шагов на русском языке.
        top_k: Количество результатов на каждый запрос (по умолчанию берётся из конфига).

    Returns:
        JSON со списком найденных уникальных шагов.
    """
    k = top_k if top_k and top_k > 0 else global_config.embeddings.top_k

    logger.info("search_steps: queries=%r, top_k=%d", queries, k)
    set_status(f"Ищу шаги по {len(queries)} запросам…")

    try:
        embeddings = await embed_model.aembed_documents(queries)
    except Exception as e:
        error_msg = f"Ошибка при векторизации запросов: {e}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    vector_store = await get_vector_store(global_config.embeddings.collection_name)

    async def _search_one(embedding: list[float]) -> list[tuple]:
        return await vector_store.asimilarity_search_with_score_by_vector(
            embedding=embedding, k=k,
        )

    try:
        all_results = await asyncio.gather(*[_search_one(emb) for emb in embeddings])
    except Exception as e:
        error_msg = f"Ошибка при поиске в коллекции {global_config.embeddings.collection_name}: {e}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    seen: dict[str, dict[str, Any]] = {}
    for docs_with_scores in all_results:
        for doc, distance in docs_with_scores:
            meta = doc.metadata or {}
            sid = meta.get("step_id", "")
            if not sid or sid in seen:
                continue
            entry = {
                "step_id": sid,
                "type": meta.get("step_type", ""),
                "pattern": meta.get("pattern", ""),
                "placeholders": meta.get("placeholders", None),
                "docstring": meta.get("docstring"),
                "requires_docstring": bool(meta.get("requires_docstring", None)),
                "requires_datatable": bool(meta.get("requires_datatable", None)),
            }
            seen[sid] = {k_: v for k_, v in entry.items() if v}

    results = list(seen.values())
    set_status(f"Найдено {len(results)} уникальных шагов")
    logger.info("search_steps: найдено %d уникальных результатов", len(results))

    content = json.dumps({"steps": results}, ensure_ascii=False)
    return _cmd(runtime, content, found_steps=seen)


# ---------------------------------------------------------------------------
# 2. set_feature_meta
# ---------------------------------------------------------------------------

@tool
def set_feature_meta(
    runtime: ToolRuntime,
    title: str,
    tags: Optional[list[str]] = None,
) -> Command:
    """Установить или обновить название Feature и теги.

    Args:
        title: Название Feature (на русском).
        tags: Список тегов, например ["@smoke", "@api"]. Необязательно.

    Returns:
        Подтверждение с обновлёнными данными.
    """
    set_status("Устанавливаю метаданные Feature…")
    title = title.strip()
    norm_tags = [t if t.startswith("@") else f"@{t}" for t in tags] if tags else []

    _stream_feature_preview(runtime, feature_title=title, feature_tags=norm_tags)

    content = json.dumps({"ok": True, "title": title, "tags": norm_tags}, ensure_ascii=False)
    return _cmd(runtime, content, feature_title=title, feature_tags=norm_tags)


# ---------------------------------------------------------------------------
# 3. add_scenario
# ---------------------------------------------------------------------------

@tool
def add_scenario(
    runtime: ToolRuntime,
    name: str,
    tags: Optional[list[str]] = None,
) -> Command:
    """Добавить новый сценарий в Feature.

    Args:
        name: Название сценария (на русском).
        tags: Список тегов сценария. Необязательно.

    Returns:
        JSON с индексом нового сценария.
    """
    set_status(f"Добавляю сценарий «{name.strip()[:50]}»…")
    scenarios: list[ScenarioDraft] = list(runtime.state.get("scenarios") or [])
    norm_tags = [t if t.startswith("@") else f"@{t}" for t in tags] if tags else []
    scenario = ScenarioDraft(name=name.strip(), tags=norm_tags)
    scenarios.append(scenario)
    idx = len(scenarios) - 1

    _stream_feature_preview(runtime, scenarios=scenarios)

    content = json.dumps({"ok": True, "scenario_index": idx, "name": scenario.name}, ensure_ascii=False)
    return _cmd(runtime, content, scenarios=scenarios)


# ---------------------------------------------------------------------------
# 4. edit_scenario
# ---------------------------------------------------------------------------

@tool
def edit_scenario(
    runtime: ToolRuntime,
    scenario_index: int,
    name: Optional[str] = None,
    tags: Optional[list[str]] = None,
) -> Command:
    """Редактировать метаданные существующего сценария (название и/или теги).
    Обновляются только переданные поля.

    Args:
        scenario_index: Индекс сценария (начиная с 0).
        name: Новое название сценария. Необязательно.
        tags: Новый список тегов сценария. Необязательно.

    Returns:
        JSON с подтверждением или ошибкой.
    """
    scenarios: list[ScenarioDraft] = list(runtime.state.get("scenarios") or [])

    if scenario_index < 0 or scenario_index >= len(scenarios):
        return _cmd(runtime, json.dumps({
            "ok": False,
            "error": f"Сценарий с индексом {scenario_index} не существует. "
                     f"Доступные индексы: 0..{len(scenarios) - 1}",
        }, ensure_ascii=False))

    scenario = scenarios[scenario_index]

    if name is not None:
        scenario.name = name.strip()
    if tags is not None:
        scenario.tags = [t if t.startswith("@") else f"@{t}" for t in tags]

    set_status(f"Обновляю сценарий {scenario_index}: «{scenario.name[:50]}»…")
    _stream_feature_preview(runtime, scenarios=scenarios)

    content = json.dumps({
        "ok": True, "scenario_index": scenario_index,
        "name": scenario.name, "tags": scenario.tags,
    }, ensure_ascii=False)
    return _cmd(runtime, content, scenarios=scenarios)


# ---------------------------------------------------------------------------
# 5. remove_scenario
# ---------------------------------------------------------------------------

@tool
def remove_scenario(
    runtime: ToolRuntime,
    scenario_index: int,
) -> Command:
    """Удалить сценарий из Feature.

    Args:
        scenario_index: Индекс сценария для удаления.

    Returns:
        JSON с подтверждением.
    """
    scenarios: list[ScenarioDraft] = list(runtime.state.get("scenarios") or [])

    if scenario_index < 0 or scenario_index >= len(scenarios):
        return _cmd(runtime, json.dumps({
            "ok": False,
            "error": f"Сценарий с индексом {scenario_index} не существует. "
                     f"Доступные индексы: 0..{len(scenarios) - 1}",
        }, ensure_ascii=False))

    removed = scenarios.pop(scenario_index)
    set_status(f"Удаляю сценарий «{removed.name[:50]}»…")
    _stream_feature_preview(runtime, scenarios=scenarios)

    content = json.dumps({
        "ok": True, "removed_name": removed.name,
        "remaining_scenarios": len(scenarios),
    }, ensure_ascii=False)
    return _cmd(runtime, content, scenarios=scenarios)


# ---------------------------------------------------------------------------
# 6. add_step
# ---------------------------------------------------------------------------

@tool
def add_step(
    runtime: ToolRuntime,
    scenario_index: int,
    keyword: str,
    step_id: str,
    params: Optional[dict[str, Any]] = None,
    docstring: Optional[str] = None,
    datatable: Optional[list[list[str]]] = None,
) -> Command:
    """Добавить шаг в сценарий. Валидирует step_id, параметры, docstring/datatable.

    Args:
        scenario_index: Индекс сценария (начиная с 0).
        keyword: Ключевое слово Gherkin: Given, When, Then, And, But.
        step_id: Идентификатор шага из каталога (например "S-1").
        params: Значения плейсхолдеров. Необязательно, если плейсхолдеров нет.
        docstring: Многострочный текст (docstring). Обязателен если pattern заканчивается на ':'.
        datatable: Таблица данных как массив строк. Обязателен если requires_datatable=true.

    Returns:
        JSON с подтверждением и отрендеренным текстом шага, или ошибка валидации.
    """
    scenarios: list[ScenarioDraft] = list(runtime.state.get("scenarios") or [])
    if params is None:
        params = {}

    if scenario_index < 0 or scenario_index >= len(scenarios):
        return _cmd(runtime, json.dumps({
            "ok": False,
            "error": f"Сценарий с индексом {scenario_index} не существует. "
                     f"Доступные индексы: 0..{len(scenarios) - 1}",
        }, ensure_ascii=False))

    step_def = get_step_def(step_id)
    if step_def is None:
        return _cmd(runtime, json.dumps({
            "ok": False, "error": f"Шаг с id '{step_id}' не найден в каталоге.",
        }, ensure_ascii=False))

    found = runtime.state.get("found_steps") or {}
    if step_id not in found:
        return _cmd(runtime, json.dumps({
            "ok": False,
            "error": f"step_id '{step_id}' не был найден через search_steps. "
                     "Сначала найди шаг через search_steps, затем используй step_id из результатов.",
        }, ensure_ascii=False))

    keyword_norm = _normalize_keyword(keyword)
    if keyword_norm is None:
        return _cmd(runtime, json.dumps({
            "ok": False,
            "error": f"Невалидное ключевое слово '{keyword}'. Допустимые: Given, When, Then, And, But.",
        }, ensure_ascii=False))

    errors = validate_step_params(step_def, params, docstring, datatable)
    if errors:
        return _cmd(runtime, json.dumps({
            "ok": False, "errors": errors, "hint": "Исправь параметры и вызови add_step снова.",
        }, ensure_ascii=False))

    step = StepChoice(
        keyword=keyword_norm, step_id=step_id,
        params=params, docstring=docstring, datatable=datatable,
    )
    scenarios[scenario_index].steps.append(step)
    step_idx = len(scenarios[scenario_index].steps) - 1

    rendered = _render_step_preview(step_def, step)
    step_text = _render_step_text(
        pattern=str(step_def.get("pattern", "")),
        placeholders=step_def.get("placeholders", []),
        params=step.params,
    )
    set_status(f"Добавляю шаг: {keyword_norm} {step_text}")
    _stream_feature_preview(runtime, scenarios=scenarios)

    content = json.dumps({
        "ok": True, "scenario_index": scenario_index,
        "step_index": step_idx, "rendered": rendered,
    }, ensure_ascii=False)
    return _cmd(runtime, content, scenarios=scenarios)


# ---------------------------------------------------------------------------
# 7. edit_step
# ---------------------------------------------------------------------------

@tool
def edit_step(
    runtime: ToolRuntime,
    scenario_index: int,
    step_index: int,
    keyword: Optional[str] = None,
    step_id: Optional[str] = None,
    params: Optional[dict[str, Any]] = None,
    docstring: Optional[str] = None,
    datatable: Optional[list[list[str]]] = None,
) -> Command:
    """Редактировать существующий шаг. Обновляются только переданные поля.

    Args:
        scenario_index: Индекс сценария.
        step_index: Индекс шага внутри сценария.
        keyword: Новое ключевое слово (Given/When/Then/And/But). Необязательно.
        step_id: Новый step_id. Необязательно.
        params: Новые параметры. Необязательно.
        docstring: Новый docstring. Необязательно.
        datatable: Новая datatable. Необязательно.

    Returns:
        JSON с подтверждением или ошибкой.
    """
    set_status(f"Редактирую шаг {step_index} в сценарии {scenario_index}…")
    scenarios: list[ScenarioDraft] = list(runtime.state.get("scenarios") or [])

    if scenario_index < 0 or scenario_index >= len(scenarios):
        return _cmd(runtime, json.dumps({
            "ok": False, "error": f"Сценарий с индексом {scenario_index} не существует.",
        }, ensure_ascii=False))

    scenario = scenarios[scenario_index]
    if step_index < 0 or step_index >= len(scenario.steps):
        return _cmd(runtime, json.dumps({
            "ok": False,
            "error": f"Шаг с индексом {step_index} не существует в сценарии {scenario_index}. "
                     f"Доступные: 0..{len(scenario.steps) - 1}",
        }, ensure_ascii=False))

    cur = scenario.steps[step_index]

    new_keyword = cur.keyword
    if keyword is not None:
        kw = _normalize_keyword(keyword)
        if kw is None:
            return _cmd(runtime, json.dumps({
                "ok": False, "error": f"Невалидное ключевое слово '{keyword}'.",
            }, ensure_ascii=False))
        new_keyword = kw

    new_step_id = step_id if step_id is not None else cur.step_id
    new_params = params if params is not None else cur.params
    new_docstring = docstring if docstring is not None else cur.docstring
    new_datatable = datatable if datatable is not None else cur.datatable

    sdef = get_step_def(new_step_id)
    if sdef is None:
        return _cmd(runtime, json.dumps({
            "ok": False, "error": f"Шаг с id '{new_step_id}' не найден в каталоге.",
        }, ensure_ascii=False))

    errors = validate_step_params(sdef, new_params, new_docstring, new_datatable)
    if errors:
        return _cmd(runtime, json.dumps({
            "ok": False, "errors": errors, "hint": "Исправь параметры и вызови edit_step снова.",
        }, ensure_ascii=False))

    scenario.steps[step_index] = StepChoice(
        keyword=new_keyword, step_id=new_step_id,
        params=new_params, docstring=new_docstring, datatable=new_datatable,
    )

    rendered = _render_step_preview(sdef, scenario.steps[step_index])
    _stream_feature_preview(runtime, scenarios=scenarios)

    content = json.dumps({
        "ok": True, "scenario_index": scenario_index,
        "step_index": step_index, "rendered": rendered,
    }, ensure_ascii=False)
    return _cmd(runtime, content, scenarios=scenarios)


# ---------------------------------------------------------------------------
# 8. remove_step
# ---------------------------------------------------------------------------

@tool
def remove_step(
    runtime: ToolRuntime,
    scenario_index: int,
    step_index: int,
) -> Command:
    """Удалить шаг из сценария.

    Args:
        scenario_index: Индекс сценария.
        step_index: Индекс шага для удаления.

    Returns:
        JSON с подтверждением.
    """
    set_status(f"Удаляю шаг {step_index} из сценария {scenario_index}…")
    scenarios: list[ScenarioDraft] = list(runtime.state.get("scenarios") or [])

    if scenario_index < 0 or scenario_index >= len(scenarios):
        return _cmd(runtime, json.dumps({
            "ok": False, "error": f"Сценарий с индексом {scenario_index} не существует.",
        }, ensure_ascii=False))

    scenario = scenarios[scenario_index]
    if step_index < 0 or step_index >= len(scenario.steps):
        return _cmd(runtime, json.dumps({
            "ok": False, "error": f"Шаг с индексом {step_index} не существует в сценарии {scenario_index}.",
        }, ensure_ascii=False))

    removed = scenario.steps.pop(step_index)
    _stream_feature_preview(runtime, scenarios=scenarios)

    content = json.dumps({
        "ok": True, "removed_step_id": removed.step_id,
        "remaining_steps": len(scenario.steps),
    }, ensure_ascii=False)
    return _cmd(runtime, content, scenarios=scenarios)


# ---------------------------------------------------------------------------
# 9. show_state  (read-only)
# ---------------------------------------------------------------------------

@tool
def show_state(runtime: ToolRuntime) -> str:
    """Показать текущее состояние собранного Feature (сценарии, шаги, параметры).

    Returns:
        JSON-представление текущего состояния Feature.
    """
    set_status("Проверяю Feature…")
    state = runtime.state
    payload = {
        "feature_title": state.get("feature_title", ""),
        "feature_tags": state.get("feature_tags", []),
        "scenarios": [s.model_dump() for s in (state.get("scenarios") or [])],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# 10. generate_feature  (read-only)
# ---------------------------------------------------------------------------

@tool
def generate_feature(runtime: ToolRuntime) -> str:
    """Валидировать и сгенерировать итоговый .feature файл из накопленного состояния.
    Feature файл показывается пользователю автоматически в виде gherkin-блока.

    Returns:
        Подтверждение генерации или список ошибок валидации.
    """
    set_status("Генерирую feature файл…")

    state = runtime.state
    title: str = state.get("feature_title", "")
    tags: list[str] = state.get("feature_tags", [])
    scenarios: list[ScenarioDraft] = state.get("scenarios") or []
    steps_index = get_steps_index()

    if not title:
        return json.dumps({"ok": False, "error": "Feature title не задан. Вызови set_feature_meta."}, ensure_ascii=False)
    if not scenarios:
        return json.dumps({"ok": False, "error": "Нет ни одного сценария. Вызови add_scenario."}, ensure_ascii=False)

    all_errors: list[str] = []
    for si, scenario in enumerate(scenarios):
        if not scenario.steps:
            all_errors.append(f"Сценарий {si} ('{scenario.name}') не содержит шагов.")
        for sti, step in enumerate(scenario.steps):
            sdef = steps_index.get(step.step_id)
            if not sdef:
                all_errors.append(f"Сценарий {si}, шаг {sti}: step_id '{step.step_id}' не найден.")
                continue
            for e in validate_step_params(sdef, step.params, step.docstring, step.datatable):
                all_errors.append(f"Сценарий {si}, шаг {sti}: {e}")

    if all_errors:
        return json.dumps({
            "ok": False, "errors": all_errors,
            "hint": "Исправь ошибки и вызови generate_feature снова.",
        }, ensure_ascii=False)

    try:
        feature_text = _render_feature(title, tags, scenarios, steps_index)
    except ValueError as exc:
        return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)

    stream_text(f"\n```gherkin\n{feature_text}```\n")

    return json.dumps({
        "ok": True,
        "message": "Feature файл сгенерирован и показан пользователю.",
    }, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------

def _render_feature(
    title: str,
    tags: list[str],
    scenarios: list[ScenarioDraft],
    steps_index: dict[str, dict[str, Any]],
) -> str:
    lines: list[str] = []
    if tags:
        lines.append(" ".join(tags))
    lines.append(f"Feature: {title}")
    lines.append("")

    for scenario in scenarios:
        if scenario.tags:
            lines.append("  " + " ".join(scenario.tags))
        lines.append(f"  Scenario: {scenario.name}")

        for step in scenario.steps:
            step_def = steps_index[step.step_id]
            step_text = _render_step_text(
                pattern=str(step_def.get("pattern", "")),
                placeholders=step_def.get("placeholders", []),
                params=step.params,
            )
            lines.append(f"    {step.keyword} {step_text}")

            if requires_datatable(step_def):
                if step.datatable:
                    lines.extend(_render_datatable_block(step.datatable))
                elif step.docstring and step.docstring.strip():
                    parsed = _parse_datatable_from_string(step.docstring)
                    if parsed:
                        lines.extend(_render_datatable_block(parsed))
                    else:
                        lines.extend(_render_docstring_block(step.docstring))
            elif requires_docstring(step_def):
                if step.docstring and step.docstring.strip():
                    lines.extend(_render_docstring_block(step.docstring))
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _render_step_text(
    *, pattern: str, placeholders: list[dict[str, Any]], params: dict[str, Any],
) -> str:
    def replace(match: re.Match) -> str:
        key = match.group("name")
        val = params[key]
        if isinstance(val, bool):
            return "true" if val else "false"
        return "" if val is None else str(val)
    return PLACEHOLDER_RE.sub(replace, pattern)


def _render_step_preview(step_def: dict[str, Any], step: StepChoice) -> str:
    text = _render_step_text(
        pattern=str(step_def.get("pattern", "")),
        placeholders=step_def.get("placeholders", []),
        params=step.params,
    )
    preview = f"{step.keyword} {text}"
    if step.docstring:
        preview += '\n      """\n'
        for line in step.docstring.splitlines():
            preview += f"      {line}\n" if line else "      \n"
        preview += '      """'
    if step.datatable:
        for row in step.datatable:
            preview += "\n      | " + " | ".join(row) + " |"
    return preview


def _render_docstring_block(docstring: str) -> list[str]:
    lines = ['      """']
    for raw_line in docstring.splitlines():
        lines.append(f"      {raw_line}" if raw_line else "      ")
    lines.append('      """')
    return lines


def _render_datatable_block(datatable: list[list[str]]) -> list[str]:
    if not datatable:
        return []
    num_cols = max(len(row) for row in datatable)
    col_widths = [0] * num_cols
    for row in datatable:
        for ci, cell in enumerate(row):
            col_widths[ci] = max(col_widths[ci], len(cell))
    lines: list[str] = []
    for row in datatable:
        cells = []
        for ci in range(num_cols):
            cell = row[ci] if ci < len(row) else ""
            cells.append(f" {cell:<{col_widths[ci]}} ")
        lines.append("      |" + "|".join(cells) + "|")
    return lines


def _parse_datatable_from_string(text: str) -> list[list[str]] | None:
    rows: list[list[str]] = []
    for line in text.strip().splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            return None
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        rows.append(cells)
    return rows if rows else None


def _normalize_keyword(raw: str) -> str | None:
    aliases = {
        "given": "Given", "when": "When", "then": "Then",
        "and": "And", "but": "But",
        "допустим": "Given", "если": "Given",
        "когда": "When", "то": "Then", "и": "And", "но": "But",
    }
    cleaned = raw.strip().strip(":")
    if cleaned in {"Given", "When", "Then", "And", "But"}:
        return cleaned
    return aliases.get(cleaned.lower())


# ---------------------------------------------------------------------------
# All tools for agent registration
# ---------------------------------------------------------------------------

ALL_TOOLS = [
    search_steps,
    set_feature_meta,
    add_scenario,
    edit_scenario,
    remove_scenario,
    add_step,
    edit_step,
    remove_step,
    show_state,
    # generate_feature,
]
