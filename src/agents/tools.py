"""Stateful scenario builder tools for SpydrAgent."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Optional

from langchain.tools import tool, ToolRuntime
from langchain.messages import ToolMessage
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.types import Command

from src.configs import global_config
from src.utils.streaming import set_status, stream_artifact, stream_text
from src.utils.embeddings import get_vector_store, embed_model
from src.agents.models import ScenarioDraft, StepChoice
from src.agents.utils import (
    normalize_keyword,
    render_feature,
    render_step_preview,
    render_step_text,
)
from src.utils.steps import (
    get_custom_collection_name,
    get_step_def,
    validate_step_params,
)
from src.agents.few_shot_selector import FewShotSelector

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_few_shot_selector: FewShotSelector | None = None


def _get_few_shot_selector() -> FewShotSelector:
    """Lazy-init singleton for the few-shot selector."""
    global _few_shot_selector
    if _few_shot_selector is None:
        few_shots_dir = _PROJECT_ROOT / global_config.rag.few_shots.few_shots_dir
        # Pass LLM params so the selector can summarise the query before search
        from omegaconf import OmegaConf
        agent_cfg_path = Path(__file__).resolve().parent / "config.yml"
        if agent_cfg_path.exists():
            agent_cfg = OmegaConf.load(agent_cfg_path)
            llm_params = dict(agent_cfg.get("llm_params", {}))
        else:
            llm_params = {}
        _few_shot_selector = FewShotSelector(few_shots_dir=few_shots_dir, llm_params=llm_params)
    return _few_shot_selector


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _validate_examples_table(table: list[list[str]]) -> str | None:
    """Validate Examples table structure. Returns error string or None."""
    if len(table) < 2:
        return ("Таблица Examples должна содержать минимум 2 строки: "
                "заголовок (названия колонок) и хотя бы одну строку данных.")
    header_len = len(table[0])
    for ri, row in enumerate(table[1:], start=1):
        if len(row) != header_len:
            return (f"Строка {ri} содержит {len(row)} столбцов, "
                    f"а заголовок — {header_len}. Все строки должны иметь одинаковое количество столбцов.")
    return None


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
    bg_steps: list[StepChoice] = overrides.get("background_steps", state.get("background_steps") or [])
    scenarios: list[ScenarioDraft] = overrides.get("scenarios", state.get("scenarios") or [])
    found_steps: dict[str, dict[str, Any]] = state.get("found_steps") or {}

    if not title:
        logger.debug("_stream_feature_preview: no title, skipping")
        return

    try:
        feature_text = render_feature(title, tags, bg_steps, scenarios, found_steps)
    except Exception as exc:
        logger.warning("_stream_feature_preview: render failed: %s", exc)
        return

    logger.info("_stream_feature_preview: streaming artifact (%d chars)", len(feature_text))
    stream_artifact(feature_text)


# ---------------------------------------------------------------------------
# Planner helpers
# ---------------------------------------------------------------------------

_PROMPTS_DIR = Path(__file__).parent / "prompts"
_RULES_PATH = Path(__file__).resolve().parents[2] / "RULES.md"


def _load_planner_prompt() -> str:
    return (_PROMPTS_DIR / "planner_prompt.md").read_text(encoding="utf-8")


def _load_docs_context() -> str:
    parts = []
    for fname in ("docs_hooks.md", "docs_summary.md"):
        path = _PROMPTS_DIR / fname
        if path.exists():
            content = path.read_text(encoding="utf-8").strip()
            if content:
                parts.append(content)
    return "\n\n".join(parts)


def _load_user_rules() -> str:
    if not _RULES_PATH.exists():
        return ""
    return _RULES_PATH.read_text(encoding="utf-8").strip()


# ---------------------------------------------------------------------------
# 0. create_plan  (LLM-based planning)
# ---------------------------------------------------------------------------

def _extract_human_messages(state: dict[str, Any]) -> list[HumanMessage]:
    """Extract HumanMessage instances from the conversation history."""
    result: list[HumanMessage] = []
    for msg in state.get("messages", []):
        if isinstance(msg, HumanMessage):
            result.append(msg)
        elif isinstance(msg, dict) and msg.get("role") == "user":
            result.append(HumanMessage(content=msg.get("content", "")))
    return result


@tool
async def create_plan(
    runtime: ToolRuntime,
) -> Command:
    """Составить план сборки Feature-файла. Вызывает отдельную LLM, обогащённую
    эталонными примерами (few-shots) и документацией проекта.
    ОБЯЗАТЕЛЬНО вызови этот инструмент ПЕРВЫМ — параметры не нужны,
    запрос пользователя берётся из истории сообщений автоматически.

    Returns:
        Текстовый план сборки Feature.
    """
    set_status("Составляю план…")

    human_msgs = _extract_human_messages(runtime.state)
    if not human_msgs:
        return _cmd(runtime, "Ошибка: не найдено сообщений пользователя в истории.")

    user_request = human_msgs[0].content
    logger.info("create_plan: building plan for request: %s", user_request[:200])

    system_prompt = _load_planner_prompt()

    # --- select few-shots via embedding search ---
    set_status("Подбираю примеры (few-shots)…")
    selector = _get_few_shot_selector()
    try:
        few_shots: list[dict[str, str]] = await selector.select(user_request)
    except Exception as exc:
        logger.warning("create_plan: few-shot selection failed: %s", exc)
        few_shots = []
    logger.info("create_plan: selected %d few-shot(s)", len(few_shots))

    few_shots_block = ""
    if few_shots:
        parts = []
        for fs in few_shots:
            fname = fs.get("file", fs.get("id", "example"))
            content = fs.get("content", "")
            parts.append(f"### {fname}\n```gherkin\n{content}```")
        few_shots_block = (
            "## Эталонные примеры (few-shots)\n\n"
            + "\n\n".join(parts)
        )

    docs_context = _load_docs_context()
    docs_block = ""
    if docs_context:
        docs_block = f"## Контекст из документации проекта\n\n{docs_context}"

    user_rules = _load_user_rules()
    rules_block = ""
    if user_rules:
        rules_block = f"## Пользовательские правила\n\n{user_rules}"

    sections = [
        f"## Запрос пользователя\n\n{user_request}",
        few_shots_block,
        docs_block,
        rules_block,
    ]
    human_content = "\n\n".join(s for s in sections if s)

    from src.agents import config as agent_config
    from src.agents.base import build_chat_model
    llm_params: dict[str, Any] = dict(agent_config.get("llm_params", {}))
    llm = build_chat_model(llm_params)

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_content),
    ]

    logger.info(
        "create_plan: calling LLM with %d few-shots, docs=%s, rules=%s",
        len(few_shots), bool(docs_context), bool(user_rules),
    )
    response = await llm.ainvoke(messages)
    plan_text = response.content

    logger.info("create_plan: plan generated (%d chars)", len(plan_text))
    set_status("План составлен")

    return _cmd(runtime, plan_text, selected_few_shots=few_shots)


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
        queries: Список семантических описаний нужных действий/проверок на русском языке.
            Описывай что нужно сделать своими словами (например: «проверить статус-код ответа»,
            «выполнить SQL-запрос к БД», «кликнуть по кнопке»). НЕ копируй точные названия
            или паттерны шагов — поиск работает по смыслу, а не по точному совпадению.
        top_k: Количество результатов на каждый запрос (по умолчанию берётся из конфига).

    Returns:
        JSON со списком найденных уникальных шагов.
    """
    k = top_k if top_k and top_k > 0 else global_config.rag.steps.top_k
    project_id = ((runtime.config or {}).get("configurable") or {}).get("project_id", "").strip() or None

    logger.info("search_steps: queries=%r, top_k=%d, project=%s", queries, k, project_id)
    set_status(f"Ищу шаги по {len(queries)} запросам…")

    try:
        embeddings = await embed_model.aembed_documents(queries)
    except Exception as e:
        error_msg = f"Ошибка при векторизации запросов: {e}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Search default collection
    default_store = await get_vector_store(global_config.rag.steps.collection_name)

    # Optionally search custom collection for the active project
    custom_store = None
    if project_id:
        custom_coll = get_custom_collection_name(project_id)
        try:
            custom_store = await get_vector_store(custom_coll)
        except Exception:
            logger.warning("Custom collection '%s' not available, skipping.", custom_coll)

    async def _search_one(store, embedding: list[float]) -> list[tuple]:
        return await store.asimilarity_search_with_score_by_vector(
            embedding=embedding, k=k,
        )

    # Build search tasks: default + (optionally) custom for each embedding
    search_tasks = [_search_one(default_store, emb) for emb in embeddings]
    if custom_store is not None:
        search_tasks.extend([_search_one(custom_store, emb) for emb in embeddings])

    try:
        all_results = await asyncio.gather(*search_tasks)
    except Exception as e:
        error_msg = f"Ошибка при поиске шагов: {e}"
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
                "parser_kind": meta.get("parser_kind", "parse"),
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
# 6. add_example
# ---------------------------------------------------------------------------

@tool
def add_example(
    runtime: ToolRuntime,
    scenario_index: int,
    examples: list[list[str]],
) -> Command:
    """Установить или заменить таблицу Examples для сценария, превращая его в Scenario Outline.

    Args:
        scenario_index: Индекс сценария (начиная с 0).
        examples: Таблица Examples. Первая строка — заголовки (названия колонок),
                  остальные — строки данных.
                  Например: [["name","request"],["type_a","req_a.json"],["type_b","req_b.json"]].

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

    err = _validate_examples_table(examples)
    if err:
        return _cmd(runtime, json.dumps({"ok": False, "error": err}, ensure_ascii=False))

    scenario = scenarios[scenario_index]
    scenario.examples = examples

    set_status(f"Устанавливаю Examples для сценария {scenario_index}: «{scenario.name[:50]}»…")
    _stream_feature_preview(runtime, scenarios=scenarios)

    content = json.dumps({
        "ok": True, "scenario_index": scenario_index,
        "name": scenario.name,
        "examples_rows": len(examples) - 1,
    }, ensure_ascii=False)
    return _cmd(runtime, content, scenarios=scenarios)


# ---------------------------------------------------------------------------
# 7. remove_example
# ---------------------------------------------------------------------------

@tool
def remove_example(
    runtime: ToolRuntime,
    scenario_index: int,
    row_index: Optional[int] = None,
) -> Command:
    """Удалить таблицу Examples из сценария (или отдельную строку данных).
    Если после удаления строки остаётся только заголовок — таблица удаляется полностью,
    и сценарий перестаёт быть Scenario Outline.

    Args:
        scenario_index: Индекс сценария (начиная с 0).
        row_index: Индекс строки данных для удаления (начиная с 0, не считая заголовок).
                   Если не указан — удаляется вся таблица Examples целиком.

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

    if scenario.examples is None:
        return _cmd(runtime, json.dumps({
            "ok": False,
            "error": f"Сценарий {scenario_index} ('{scenario.name}') не содержит таблицу Examples.",
        }, ensure_ascii=False))

    if row_index is None:
        # Remove the entire Examples table
        scenario.examples = None
        set_status(f"Удаляю Examples из сценария {scenario_index}: «{scenario.name[:50]}»…")
        _stream_feature_preview(runtime, scenarios=scenarios)
        content = json.dumps({
            "ok": True, "scenario_index": scenario_index,
            "message": "Таблица Examples удалена полностью.",
        }, ensure_ascii=False)
        return _cmd(runtime, content, scenarios=scenarios)

    # Remove a specific data row (row_index is 0-based among data rows, header is examples[0])
    data_rows_count = len(scenario.examples) - 1
    if row_index < 0 or row_index >= data_rows_count:
        return _cmd(runtime, json.dumps({
            "ok": False,
            "error": f"Строка данных с индексом {row_index} не существует. "
                     f"Доступные индексы: 0..{data_rows_count - 1}",
        }, ensure_ascii=False))

    removed_row = scenario.examples.pop(row_index + 1)  # +1 because [0] is header

    # If only the header remains, remove the whole table
    if len(scenario.examples) < 2:
        scenario.examples = None
        msg = "Строка удалена. Осталась только шапка — таблица Examples удалена полностью."
    else:
        msg = f"Строка {row_index} удалена. Осталось строк данных: {len(scenario.examples) - 1}."

    set_status(f"Удаляю строку из Examples сценария {scenario_index}…")
    _stream_feature_preview(runtime, scenarios=scenarios)

    content = json.dumps({
        "ok": True, "scenario_index": scenario_index,
        "removed_row": removed_row, "message": msg,
    }, ensure_ascii=False)
    return _cmd(runtime, content, scenarios=scenarios)


# ---------------------------------------------------------------------------
# 8. add_background_step
# ---------------------------------------------------------------------------

@tool
def add_background_step(
    runtime: ToolRuntime,
    keyword: str,
    step_id: str,
    params: Optional[dict[str, Any]] = None,
    docstring: Optional[str] = None,
    docstring_lang: Optional[str] = None,
    datatable: Optional[list[list[str]]] = None,
    pos: int = -1,
) -> Command:
    """Добавить шаг в блок Background. Background-шаги выполняются перед каждым сценарием.

    Args:
        keyword: Ключевое слово Gherkin: Given, When, Then, And, But.
        step_id: Идентификатор шага из каталога (например "S-1").
        params: Значения плейсхолдеров. Необязательно, если плейсхолдеров нет.
        docstring: Многострочный текст (docstring). Обязателен если pattern заканчивается на ':'.
        docstring_lang: Язык содержимого docstring для статической валидации. ОБЯЗАТЕЛЕН если содержимое docstring синтаксически соответствует любому поддерживаемому языку (список см. в системном промпте).
        datatable: Таблица данных как массив строк. Обязателен если requires_datatable=true.
        pos: Позиция вставки шага (0-based). По умолчанию -1 (вставка в конец). Если >= 0, шаг вставляется перед элементом с этим индексом.

    Returns:
        JSON с подтверждением и отрендеренным текстом шага, или ошибка валидации.
    """
    bg_steps: list[StepChoice] = list(runtime.state.get("background_steps") or [])
    if params is None:
        params = {}

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

    keyword_norm = normalize_keyword(keyword)
    if keyword_norm is None:
        return _cmd(runtime, json.dumps({
            "ok": False,
            "error": f"Невалидное ключевое слово '{keyword}'. Допустимые: Given, When, Then, And, But.",
        }, ensure_ascii=False))

    errors = validate_step_params(step_def, params, docstring, datatable, docstring_lang)
    if errors:
        return _cmd(runtime, json.dumps({
            "ok": False, "errors": errors, "hint": "Исправь параметры и вызови add_background_step снова.",
        }, ensure_ascii=False))

    step = StepChoice(
        keyword=keyword_norm, step_id=step_id,
        params=params, docstring=docstring, docstring_lang=docstring_lang, datatable=datatable,
    )
    if pos < 0 or pos >= len(bg_steps):
        bg_steps.append(step)
        step_idx = len(bg_steps) - 1
    else:
        bg_steps.insert(pos, step)
        step_idx = pos

    rendered = render_step_preview(step_def, step)
    step_text = render_step_text(
        pattern=str(step_def.get("pattern", "")),
        placeholders=step_def.get("placeholders", []),
        params=step.params,
    )
    set_status(f"Добавляю Background шаг: {keyword_norm} {step_text}")
    _stream_feature_preview(runtime, background_steps=bg_steps)

    content = json.dumps({
        "ok": True, "step_index": step_idx, "rendered": rendered,
    }, ensure_ascii=False)
    return _cmd(runtime, content, background_steps=bg_steps)


# ---------------------------------------------------------------------------
# 7. edit_background_step
# ---------------------------------------------------------------------------

@tool
def edit_background_step(
    runtime: ToolRuntime,
    pos: int,
    keyword: Optional[str] = None,
    step_id: Optional[str] = None,
    params: Optional[dict[str, Any]] = None,
    docstring: Optional[str] = None,
    docstring_lang: Optional[str] = None,
    datatable: Optional[list[list[str]]] = None,
) -> Command:
    """Редактировать существующий шаг в блоке Background. Обновляются только переданные поля.

    Args:
        pos: Позиция шага внутри Background (0-based).
        keyword: Новое ключевое слово (Given/When/Then/And/But). Необязательно.
        step_id: Новый step_id. Необязательно.
        params: Новые параметры. Необязательно.
        docstring: Новый docstring. Необязательно.
        docstring_lang: Язык docstring для валидации. ОБЯЗАТЕЛЕН если содержимое docstring синтаксически соответствует любому поддерживаемому языку (список см. в системном промпте).
        datatable: Новая datatable. Необязательно.

    Returns:
        JSON с подтверждением или ошибкой.
    """
    set_status(f"Редактирую Background шаг {pos}…")
    bg_steps: list[StepChoice] = list(runtime.state.get("background_steps") or [])

    if pos < 0 or pos >= len(bg_steps):
        return _cmd(runtime, json.dumps({
            "ok": False,
            "error": f"Background шаг с позицией {pos} не существует. "
                     f"Доступные позиции: 0..{len(bg_steps) - 1}",
        }, ensure_ascii=False))

    cur = bg_steps[pos]

    new_keyword = cur.keyword
    if keyword is not None:
        kw = normalize_keyword(keyword)
        if kw is None:
            return _cmd(runtime, json.dumps({
                "ok": False, "error": f"Невалидное ключевое слово '{keyword}'.",
            }, ensure_ascii=False))
        new_keyword = kw

    new_step_id = step_id if step_id is not None else cur.step_id
    new_params = params if params is not None else cur.params
    new_docstring = docstring if docstring is not None else cur.docstring
    new_docstring_lang = docstring_lang if docstring_lang is not None else cur.docstring_lang
    new_datatable = datatable if datatable is not None else cur.datatable

    sdef = get_step_def(new_step_id)
    if sdef is None:
        return _cmd(runtime, json.dumps({
            "ok": False, "error": f"Шаг с id '{new_step_id}' не найден в каталоге.",
        }, ensure_ascii=False))

    errors = validate_step_params(sdef, new_params, new_docstring, new_datatable, new_docstring_lang)
    if errors:
        return _cmd(runtime, json.dumps({
            "ok": False, "errors": errors, "hint": "Исправь параметры и вызови edit_background_step снова.",
        }, ensure_ascii=False))

    bg_steps[pos] = StepChoice(
        keyword=new_keyword, step_id=new_step_id,
        params=new_params, docstring=new_docstring, docstring_lang=new_docstring_lang, datatable=new_datatable,
    )

    rendered = render_step_preview(sdef, bg_steps[pos])
    _stream_feature_preview(runtime, background_steps=bg_steps)

    content = json.dumps({
        "ok": True, "pos": pos, "rendered": rendered,
    }, ensure_ascii=False)
    return _cmd(runtime, content, background_steps=bg_steps)


# ---------------------------------------------------------------------------
# 8. remove_background_step
# ---------------------------------------------------------------------------

@tool
def remove_background_step(
    runtime: ToolRuntime,
    pos: int,
) -> Command:
    """Удалить шаг из блока Background.

    Args:
        pos: Позиция шага для удаления (0-based).

    Returns:
        JSON с подтверждением.
    """
    set_status(f"Удаляю Background шаг {pos}…")
    bg_steps: list[StepChoice] = list(runtime.state.get("background_steps") or [])

    if pos < 0 or pos >= len(bg_steps):
        return _cmd(runtime, json.dumps({
            "ok": False,
            "error": f"Background шаг с позицией {pos} не существует. "
                     f"Доступные позиции: 0..{len(bg_steps) - 1}",
        }, ensure_ascii=False))

    removed = bg_steps.pop(pos)
    _stream_feature_preview(runtime, background_steps=bg_steps)

    content = json.dumps({
        "ok": True, "removed_step_id": removed.step_id,
        "remaining_background_steps": len(bg_steps),
    }, ensure_ascii=False)
    return _cmd(runtime, content, background_steps=bg_steps)


# ---------------------------------------------------------------------------
# 9. add_step
# ---------------------------------------------------------------------------

@tool
def add_step(
    runtime: ToolRuntime,
    scenario_index: int,
    keyword: str,
    step_id: str,
    params: Optional[dict[str, Any]] = None,
    docstring: Optional[str] = None,
    docstring_lang: Optional[str] = None,
    datatable: Optional[list[list[str]]] = None,
    pos: int = -1,
) -> Command:
    """Добавить шаг в сценарий. Валидирует step_id, параметры, docstring/datatable.

    Args:
        scenario_index: Индекс сценария (начиная с 0).
        keyword: Ключевое слово Gherkin: Given, When, Then, And, But.
        step_id: Идентификатор шага из каталога (например "S-1").
        params: Значения плейсхолдеров. Необязательно, если плейсхолдеров нет.
        docstring: Многострочный текст (docstring). Обязателен если pattern заканчивается на ':'.
        docstring_lang: Язык содержимого docstring для статической валидации. ОБЯЗАТЕЛЕН если содержимое docstring синтаксически соответствует любому поддерживаемому языку (список см. в системном промпте).
        datatable: Таблица данных как массив строк. Обязателен если requires_datatable=true.
        pos: Позиция вставки шага (0-based). По умолчанию -1 (вставка в конец). Если >= 0, шаг вставляется перед элементом с этим индексом.

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

    keyword_norm = normalize_keyword(keyword)
    if keyword_norm is None:
        return _cmd(runtime, json.dumps({
            "ok": False,
            "error": f"Невалидное ключевое слово '{keyword}'. Допустимые: Given, When, Then, And, But.",
        }, ensure_ascii=False))

    errors = validate_step_params(step_def, params, docstring, datatable, docstring_lang)
    if errors:
        return _cmd(runtime, json.dumps({
            "ok": False, "errors": errors, "hint": "Исправь параметры и вызови add_step снова.",
        }, ensure_ascii=False))

    step = StepChoice(
        keyword=keyword_norm, step_id=step_id,
        params=params, docstring=docstring, docstring_lang=docstring_lang, datatable=datatable,
    )
    steps_list = scenarios[scenario_index].steps
    if pos < 0 or pos >= len(steps_list):
        steps_list.append(step)
        step_idx = len(steps_list) - 1
    else:
        steps_list.insert(pos, step)
        step_idx = pos

    rendered = render_step_preview(step_def, step)
    step_text = render_step_text(
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
    pos: int,
    keyword: Optional[str] = None,
    step_id: Optional[str] = None,
    params: Optional[dict[str, Any]] = None,
    docstring: Optional[str] = None,
    docstring_lang: Optional[str] = None,
    datatable: Optional[list[list[str]]] = None,
) -> Command:
    """Редактировать существующий шаг. Обновляются только переданные поля.

    Args:
        scenario_index: Индекс сценария.
        pos: Позиция шага внутри сценария (0-based).
        keyword: Новое ключевое слово (Given/When/Then/And/But). Необязательно.
        step_id: Новый step_id. Необязательно.
        params: Новые параметры. Необязательно.
        docstring: Новый docstring. Необязательно.
        docstring_lang: Язык docstring для валидации. ОБЯЗАТЕЛЕН если содержимое docstring синтаксически соответствует любому поддерживаемому языку (список см. в системном промпте).
        datatable: Новая datatable. Необязательно.

    Returns:
        JSON с подтверждением или ошибкой.
    """
    set_status(f"Редактирую шаг {pos} в сценарии {scenario_index}…")
    scenarios: list[ScenarioDraft] = list(runtime.state.get("scenarios") or [])

    if scenario_index < 0 or scenario_index >= len(scenarios):
        return _cmd(runtime, json.dumps({
            "ok": False, "error": f"Сценарий с индексом {scenario_index} не существует.",
        }, ensure_ascii=False))

    scenario = scenarios[scenario_index]
    if pos < 0 or pos >= len(scenario.steps):
        return _cmd(runtime, json.dumps({
            "ok": False,
            "error": f"Шаг с позицией {pos} не существует в сценарии {scenario_index}. "
                     f"Доступные: 0..{len(scenario.steps) - 1}",
        }, ensure_ascii=False))

    cur = scenario.steps[pos]

    new_keyword = cur.keyword
    if keyword is not None:
        kw = normalize_keyword(keyword)
        if kw is None:
            return _cmd(runtime, json.dumps({
                "ok": False, "error": f"Невалидное ключевое слово '{keyword}'.",
            }, ensure_ascii=False))
        new_keyword = kw

    new_step_id = step_id if step_id is not None else cur.step_id
    new_params = params if params is not None else cur.params
    new_docstring = docstring if docstring is not None else cur.docstring
    new_docstring_lang = docstring_lang if docstring_lang is not None else cur.docstring_lang
    new_datatable = datatable if datatable is not None else cur.datatable

    sdef = get_step_def(new_step_id)
    if sdef is None:
        return _cmd(runtime, json.dumps({
            "ok": False, "error": f"Шаг с id '{new_step_id}' не найден в каталоге.",
        }, ensure_ascii=False))

    errors = validate_step_params(sdef, new_params, new_docstring, new_datatable, new_docstring_lang)
    if errors:
        return _cmd(runtime, json.dumps({
            "ok": False, "errors": errors, "hint": "Исправь параметры и вызови edit_step снова.",
        }, ensure_ascii=False))

    scenario.steps[pos] = StepChoice(
        keyword=new_keyword, step_id=new_step_id,
        params=new_params, docstring=new_docstring, docstring_lang=new_docstring_lang, datatable=new_datatable,
    )

    rendered = render_step_preview(sdef, scenario.steps[pos])
    _stream_feature_preview(runtime, scenarios=scenarios)

    content = json.dumps({
        "ok": True, "scenario_index": scenario_index,
        "pos": pos, "rendered": rendered,
    }, ensure_ascii=False)
    return _cmd(runtime, content, scenarios=scenarios)


# ---------------------------------------------------------------------------
# 8. remove_step
# ---------------------------------------------------------------------------

@tool
def remove_step(
    runtime: ToolRuntime,
    scenario_index: int,
    pos: int,
) -> Command:
    """Удалить шаг из сценария.

    Args:
        scenario_index: Индекс сценария.
        pos: Позиция шага для удаления (0-based).

    Returns:
        JSON с подтверждением.
    """
    set_status(f"Удаляю шаг {pos} из сценария {scenario_index}…")
    scenarios: list[ScenarioDraft] = list(runtime.state.get("scenarios") or [])

    if scenario_index < 0 or scenario_index >= len(scenarios):
        return _cmd(runtime, json.dumps({
            "ok": False, "error": f"Сценарий с индексом {scenario_index} не существует.",
        }, ensure_ascii=False))

    scenario = scenarios[scenario_index]
    if pos < 0 or pos >= len(scenario.steps):
        return _cmd(runtime, json.dumps({
            "ok": False, "error": f"Шаг с позицией {pos} не существует в сценарии {scenario_index}.",
        }, ensure_ascii=False))

    removed = scenario.steps.pop(pos)
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
        "background_steps": [s.model_dump() for s in (state.get("background_steps") or [])],
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
    bg_steps: list[StepChoice] = state.get("background_steps") or []
    scenarios: list[ScenarioDraft] = state.get("scenarios") or []
    found_steps: dict[str, dict[str, Any]] = state.get("found_steps") or {}

    if not title:
        return json.dumps({"ok": False, "error": "Feature title не задан. Вызови set_feature_meta."}, ensure_ascii=False)
    if not scenarios:
        return json.dumps({"ok": False, "error": "Нет ни одного сценария. Вызови add_scenario."}, ensure_ascii=False)

    all_errors: list[str] = []

    for bsi, step in enumerate(bg_steps):
        sdef = found_steps.get(step.step_id)
        if not sdef:
            all_errors.append(f"Background, шаг {bsi}: step_id '{step.step_id}' не найден.")
            continue
        for e in validate_step_params(sdef, step.params, step.docstring, step.datatable, step.docstring_lang):
            all_errors.append(f"Background, шаг {bsi}: {e}")

    for si, scenario in enumerate(scenarios):
        if not scenario.steps:
            all_errors.append(f"Сценарий {si} ('{scenario.name}') не содержит шагов.")
        for sti, step in enumerate(scenario.steps):
            sdef = found_steps.get(step.step_id)
            if not sdef:
                all_errors.append(f"Сценарий {si}, шаг {sti}: step_id '{step.step_id}' не найден.")
                continue
            for e in validate_step_params(sdef, step.params, step.docstring, step.datatable, step.docstring_lang):
                all_errors.append(f"Сценарий {si}, шаг {sti}: {e}")

        if scenario.examples is not None:
            if len(scenario.examples) < 2:
                all_errors.append(
                    f"Сценарий {si} ('{scenario.name}'): таблица Examples должна содержать "
                    f"минимум 2 строки (заголовок + данные)."
                )
            else:
                header_len = len(scenario.examples[0])
                for ri, row in enumerate(scenario.examples[1:], start=1):
                    if len(row) != header_len:
                        all_errors.append(
                            f"Сценарий {si} ('{scenario.name}'): строка {ri} в Examples "
                            f"содержит {len(row)} столбцов, а заголовок — {header_len}."
                        )

    if all_errors:
        return json.dumps({
            "ok": False, "errors": all_errors,
            "hint": "Исправь ошибки и вызови generate_feature снова.",
        }, ensure_ascii=False)

    try:
        feature_text = render_feature(title, tags, bg_steps, scenarios, found_steps)
    except ValueError as exc:
        return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)

    stream_text(f"\n```gherkin\n{feature_text}```\n")

    return json.dumps({
        "ok": True,
        "message": "Feature файл сгенерирован и показан пользователю.",
    }, ensure_ascii=False)


# ---------------------------------------------------------------------------
# 11. search_info  (project docs RAG)
# ---------------------------------------------------------------------------

@tool
async def search_info(
    runtime: ToolRuntime,
    query: str,
    top_k: Optional[int] = None,
) -> Command:
    """Семантический поиск по проектной документации (docs/).
    Результаты дедуплицируются по содержимому и накапливаются между вызовами.

    Args:
        query: Поисковый запрос на естественном языке.
        top_k: Количество результатов (по умолчанию берётся из конфига).

    Returns:
        JSON с найденными фрагментами документации.
    """
    cfg = global_config.rag.docs
    k = top_k if top_k and top_k > 0 else cfg.top_k

    logger.info("search_info: query=%r, top_k=%d", query, k)
    set_status("Ищу информацию в документации…")

    vector_store = await get_vector_store(cfg.collection_name)

    try:
        results = await vector_store.asimilarity_search_with_score(query, k=k)
    except Exception as e:
        error_msg = f"Ошибка при поиске в коллекции {cfg.collection_name}: {e}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    already_known: dict[str, dict[str, Any]] = runtime.state.get("found_docs") or {}
    new_docs: dict[str, dict[str, Any]] = {}

    for doc, distance in results:
        text = doc.page_content
        chunk_hash = hashlib.md5(text.encode()).hexdigest()[:12]
        score = round(1.0 - distance, 4)
        entry = {
            "text": text,
            "source": (doc.metadata or {}).get("source", ""),
            "score": score,
        }
        new_docs[chunk_hash] = entry

    only_new = {h: v for h, v in new_docs.items() if h not in already_known}

    set_status(f"Найдено {len(new_docs)} фрагмент(ов), из них новых: {len(only_new)}")
    logger.info(
        "search_info: total=%d, new=%d", len(new_docs), len(only_new),
    )

    response_items = [
        {"chunk_id": h, **v} for h, v in only_new.items()
    ] if only_new else [
        {"chunk_id": h, **v} for h, v in new_docs.items()
    ]

    content = json.dumps(
        {"docs": response_items, "total_known": len(already_known) + len(only_new)},
        ensure_ascii=False,
    )
    return _cmd(runtime, content, found_docs=new_docs)


# ---------------------------------------------------------------------------
# All tools for agent registration
# ---------------------------------------------------------------------------

ALL_TOOLS = [
    create_plan,
    search_steps,
    search_info,
    set_feature_meta,
    add_scenario,
    edit_scenario,
    remove_scenario,
    add_example,
    remove_example,
    add_background_step,
    edit_background_step,
    remove_background_step,
    add_step,
    edit_step,
    remove_step,
    show_state,
    # generate_feature,
]
