"""LLM tool-calling agent for manual-test to strict step-id plans."""

import json
import re
import time
import logging
from typing import Any

from .agent_protocol import FeaturePlan, parse_agent_response
from .llm_compat import build_openai_compatible_client
from .rag_store import StepRAGStore
from .tracing import get_tracer

TRACER = get_tracer(__name__)

SYSTEM_PROMPT = (
    "Ты - агент конвертации ручных тестов в Gherkin сценарии.\n"
    "Ты НЕ пишешь текст шагов вручную. Вместо этого ты выбираешь шаги ТОЛЬКО по step_id.\n"
    "Для поиска подходящих шагов используй tool search_steps.\n"
    "Заверши ответ ТОЛЬКО валидным JSON, без markdown, в формате:\n"
    "{\n"
    '  "feature": "Название Feature",\n'
    '  "tags": ["@tag1"],\n'
    '  "scenarios": [\n'
    "    {\n"
    '      "name": "Название Scenario",\n'
    '      "tags": ["@tag"],\n'
    '      "steps": [\n'
    '        {"keyword":"Given","step_id":"step_xxx","params":{"name":"value"},"docstring":null,"datatable":null}\n'
    "      ]\n"
    "    }\n"
    "  ]\n"
    "}\n"
    "Правила:\n"
    "1) Каждый шаг обязан иметь существующий step_id.\n"
    "2) params должны содержать значения для ВСЕХ плейсхолдеров выбранного шага. ВАЖНО: внимательно проверь pattern шага - каждый плейсхолдер в фигурных скобках {name} требует соответствующего параметра в params.\n"
    "3) КРИТИЧЕСКИ ВАЖНО: Если выбранный pattern оканчивается на ':', шаг ОБЯЗАТЕЛЬНО требует docstring. Ты ДОЛЖЕН передать docstring в JSON, даже если это пустая строка или пробелы - передай хотя бы минимальное содержимое.\n"
    "4) Если шаг требует datatable (в результатах search_steps поле requires_datatable=true), "
    "передай datatable как массив массивов строк, например: "
    '"datatable": [["col1","col2"],["val1","val2"]]. '
    "Это отрендерится как Gherkin datatable: | col1 | col2 |\\n| val1 | val2 |.\n"
    "5) Для SQL-шагов вида 'Выполнить запрос в базу ...' также обязательно передавай SQL в docstring, даже если в pattern нет ':'.\n"
    "6) docstring передавай как обычную JSON-строку с переносами \\n (без тройных кавычек в самом JSON).\n"
    "7) Никаких новых шагов, только найденные через tool.\n"
    "8) Язык названий feature/scenario - русский.\n"
    "9) При выборе шага из результатов search_steps, обязательно извлеки из pattern все плейсхолдеры и заполни их в params на основе контекста ручного теста.\n"
    "10) step_id может начинаться с step_ (универсальный шаг, можно использовать с любым keyword: Given/When/Then/And/But) "
    "или с given_/when_/then_ (привязан к конкретному типу)."
)

TOOL_SPEC = [
    {
        "type": "function",
        "function": {
            "name": "search_steps",
            "description": "Семантический поиск BDD шагов в базе. Возвращает кандидаты с step_id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "step_type": {
                        "type": "string",
                        "enum": ["given", "when", "then"],
                        "description": "Ограничить поиск по типу шага. Можно опустить.",
                    },
                    "top_k": {"type": "integer", "minimum": 1, "maximum": 20},
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    }
]

MAX_TOOL_CALL_ROUNDS = 15
LLM_REQUEST_TIMEOUT_SEC = 60
MAX_LLM_REQUEST_RETRIES = 2
MIN_NATURAL_QUERY_LEN = 8


def get_openai_client(*, llm_provider: str | None = None):
    """Create OpenAI-compatible client from environment."""
    return build_openai_compatible_client(llm_provider=llm_provider)


def build_user_prompt(test_content: str, feature_name: str) -> str:
    """Build user prompt for conversion request."""
    return f"""Конвертируй следующий ручной тест в Gherkin feature файл.

Название Feature: {feature_name}

Содержимое теста для конвертации:
---
{test_content}
---

Используй tool search_steps, затем верни ТОЛЬКО JSON структуры feature/scenarios/steps.
Шаги в JSON задавай через step_id, params и (при необходимости) docstring или datatable."""


def _build_repair_prompt(repair_feedback: str) -> str:
    """Build follow-up instruction for repairing invalid/partial plan."""
    return (
        "Исправь предыдущий JSON-план с учетом ошибок валидации.\n"
        "Верни ТОЛЬКО обновленный валидный JSON по той же схеме.\n\n"
        f"Ошибки и контекст:\n{repair_feedback}"
    )


def build_feature_plan(
    client,
    test_content: str,
    feature_name: str,
    model: str,
    rag_store: StepRAGStore,
    rag_top_k: int = 8,
    verbose: bool = False,
    repair_feedback: str | None = None,
) -> tuple[FeaturePlan, int]:
    """Build strict feature plan where each step is selected by step_id."""
    logger = logging.getLogger("baseline.agent")
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(test_content, feature_name)},
    ]
    if repair_feedback:
        messages.append({"role": "user", "content": _build_repair_prompt(repair_feedback)})

    total_tool_calls = 0
    last_validation_error: str | None = None
    with TRACER.start_as_current_span("baseline.agent.plan_generation") as span:
        span.set_attribute("llm.model", model)
        span.set_attribute("llm.rag_top_k", rag_top_k)
        # +1 round is reserved for final answer synthesis after the last tool-call round.
        max_agent_rounds = MAX_TOOL_CALL_ROUNDS + 1
        for round_idx in range(1, max_agent_rounds + 1):
            logger.debug(f"--- Round {round_idx} ---")
            logger.debug(f"Messages: {json.dumps(messages, ensure_ascii=False, indent=2)}")
            with TRACER.start_as_current_span("baseline.agent.round") as round_span:
                round_span.set_attribute("llm.round_index", round_idx)
                round_span.set_attribute("llm.messages_count", len(messages))
                if verbose:
                    print(f"    [agent] Раунд {round_idx}: отправка запроса в chat.completions...")
                started_at = time.perf_counter()
                response = None
                last_request_error: Exception | None = None
                for request_attempt in range(1, MAX_LLM_REQUEST_RETRIES + 1):
                    try:
                        logger.debug(f"Requesting completion from {model} (attempt {request_attempt})...")
                        response = client.chat.completions.create(
                            model=model,
                            messages=messages,
                            tools=TOOL_SPEC,
                            tool_choice="auto",
                            response_format={"type": "json_object"},
                            temperature=0,
                            timeout=LLM_REQUEST_TIMEOUT_SEC,
                        )
                        last_request_error = None
                        break
                    except Exception as request_exc:  # noqa: BLE001 - transport/provider exceptions vary
                        last_request_error = request_exc
                        round_span.record_exception(request_exc)
                        logger.warning(f"LLM request error: {request_exc}")
                        if verbose:
                            print(
                                "    [agent] Ошибка запроса к LLM "
                                f"(попытка {request_attempt}/{MAX_LLM_REQUEST_RETRIES}): {request_exc}"
                            )
                        if request_attempt < MAX_LLM_REQUEST_RETRIES:
                            # Small delay helps with transient transport/provider issues.
                            time.sleep(1)
                if response is None:
                    logger.error(f"Failed to get response after {MAX_LLM_REQUEST_RETRIES} attempts.")
                    raise ValueError(
                        "Не удалось получить ответ от LLM: превышено число попыток "
                        f"({MAX_LLM_REQUEST_RETRIES}), timeout={LLM_REQUEST_TIMEOUT_SEC}s. "
                        f"Последняя ошибка: {last_request_error}"
                    )
                elapsed = time.perf_counter() - started_at
                round_span.set_attribute("llm.round_latency_sec", elapsed)
                usage = getattr(response, "usage", None)
                if usage:
                    usage_dict = {
                        "prompt_tokens": getattr(usage, "prompt_tokens", 0),
                        "completion_tokens": getattr(usage, "completion_tokens", 0),
                        "total_tokens": getattr(usage, "total_tokens", 0),
                    }
                    logger.debug(f"Usage: {usage_dict}")
                    round_span.set_attribute("llm.prompt_tokens", int(getattr(usage, "prompt_tokens", 0) or 0))
                    round_span.set_attribute(
                        "llm.completion_tokens", int(getattr(usage, "completion_tokens", 0) or 0)
                    )
                    round_span.set_attribute("llm.total_tokens", int(getattr(usage, "total_tokens", 0) or 0))
                if verbose:
                    print(f"    [agent] Раунд {round_idx}: ответ получен за {elapsed:.2f}s")
                message = response.choices[0].message
                logger.debug(f"Assistant message: {message.content}")
                tool_calls = message.tool_calls or []
                if not tool_calls:
                    content = message.content or ""
                    if verbose:
                        print("    [agent] Tool-вызовов нет, парсинг финального JSON...")
                    try:
                        plan = parse_agent_response(content)
                        logger.info("Plan generation successful.")
                        return plan, total_tool_calls
                    except (json.JSONDecodeError, ValueError) as exc:
                        last_validation_error = str(exc)
                        round_span.record_exception(exc)
                        logger.warning(f"Invalid JSON from model: {exc}")
                        if verbose:
                            print(f"    [agent] Невалидный JSON от модели: {exc}")
                            print("    [agent] Запрашиваю у модели исправленную JSON-версию ответа...")
                        messages.append(
                            {
                                "role": "assistant",
                                "content": content,
                            }
                        )
                        messages.append(
                            {
                                "role": "user",
                                "content": (
                                    "Ответ не является валидным JSON по заданной схеме. "
                                    "Верни ТОЛЬКО исправленный валидный JSON без пояснений и markdown."
                                ),
                            }
                        )
                        continue

                total_tool_calls += len(tool_calls)
                round_span.set_attribute("llm.tool_calls_count", len(tool_calls))
                if round_idx > MAX_TOOL_CALL_ROUNDS:
                    logger.error(f"Max tool call rounds reached: {MAX_TOOL_CALL_ROUNDS}")
                    raise ValueError(
                        "Агент превысил лимит раундов tool-вызовов "
                        f"({MAX_TOOL_CALL_ROUNDS}) и не смог завершить конвертацию."
                    )
                if verbose:
                    print(f"    [agent] Раунд {round_idx}: tool-вызовов {len(tool_calls)}")
                messages.append(
                    {
                        "role": "assistant",
                        "content": message.content or "",
                        "tool_calls": [
                            {
                                "id": call.id,
                                "type": "function",
                                "function": {
                                    "name": call.function.name,
                                    "arguments": call.function.arguments,
                                },
                            }
                            for call in tool_calls
                        ],
                    }
                )
                for tool_call in tool_calls:
                    logger.debug(f"Executing tool call: {tool_call.function.name} with args: {tool_call.function.arguments}")
                    tool_result = _execute_tool_call(
                        tool_call_name=tool_call.function.name,
                        tool_call_arguments=tool_call.function.arguments,
                        rag_store=rag_store,
                        rag_top_k=rag_top_k,
                        verbose=verbose,
                    )
                    logger.debug(f"Tool result: {json.dumps(tool_result, ensure_ascii=False)}")
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(tool_result, ensure_ascii=False),
                        }
                    )

    if last_validation_error:
        logger.error(f"Agent failed after max rounds. Last validation error: {last_validation_error}")
        raise ValueError(
            "Агент не смог завершить конвертацию: превышен лимит раундов, "
            f"последняя ошибка валидации: {last_validation_error}"
        )
    logger.error("Agent failed after max rounds.")
    raise ValueError("Агент не смог завершить конвертацию: превышен лимит раундов.")


def _execute_tool_call(
    *,
    tool_call_name: str,
    tool_call_arguments: str,
    rag_store: StepRAGStore,
    rag_top_k: int,
    verbose: bool = False,
) -> dict[str, Any]:
    """Execute one tool call from the model and return serializable output."""
    logger = logging.getLogger("baseline.tool")
    with TRACER.start_as_current_span("baseline.agent.tool_call") as span:
        span.set_attribute("tool.name", tool_call_name)
        if tool_call_name != "search_steps":
            logger.error(f"Unknown tool: {tool_call_name}")
            return {"error": f"Неизвестный tool: {tool_call_name}"}
        try:
            args = json.loads(tool_call_arguments or "{}")
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in tool arguments: {tool_call_arguments}")
            return {"error": "Аргументы tool должны быть валидным JSON."}
        query = str(args.get("query", "")).strip()
        if not query:
            logger.error("Missing query argument in search_steps")
            return {"error": "Аргумент query обязателен."}
        if _looks_like_step_id_or_noise(query):
            span.set_attribute("tool.bad_query", True)
            span.set_attribute("tool.bad_query_reason", "step_id_or_noise")
            logger.warning(f"Rejected query as unnatural: {query!r}")
            if verbose:
                print(f"    [tool] Отклонен query как неестественный: {query!r}")
            return {
                "error": (
                    "Некорректный query для semantic search. "
                    "Передай краткую естественную фразу на русском о действии/проверке, "
                    "а не step_id/технический токен."
                )
            }
        step_type_raw = args.get("step_type")
        step_type = str(step_type_raw).lower() if step_type_raw else None
        top_k = args.get("top_k")
        if not isinstance(top_k, int) or top_k <= 0:
            top_k = rag_top_k
        span.set_attribute("tool.step_type", step_type or "any")
        span.set_attribute("tool.top_k", top_k)
        span.set_attribute("tool.query_preview", query[:200])
        if verbose:
            print(f"    [tool] search_steps(query={query[:120]!r}, step_type={step_type}, top_k={top_k})")
        results = rag_store.search_steps(query=query, step_type=step_type, top_k=top_k, verbose=verbose)
        span.set_attribute("tool.results_count", len(results))
        if verbose:
            print(f"    [tool] search_steps -> найдено кандидатов: {len(results)}")
        return {"results": results}


def _looks_like_step_id_or_noise(query: str) -> bool:
    """Reject id-like, hash-like or too-technical strings for semantic retrieval."""
    normalized = query.strip().lower()
    if len(normalized) < MIN_NATURAL_QUERY_LEN:
        return True
    if normalized.startswith(("given_", "when_", "then_", "step_")):
        return True
    if re.fullmatch(r"[a-z0-9_\-:/.]+", normalized):
        # Purely technical token without spaces or cyrillic text.
        if " " not in normalized:
            return True
        if _ratio_of_letters_and_digits_only(normalized) > 0.9:
            return True
    if re.fullmatch(r"[a-f0-9]{12,}", normalized):
        return True
    if re.search(r"[а-яё]", normalized):
        return False
    # If no Cyrillic and almost no spaces, this is usually not a user-level phrase in this project.
    return normalized.count(" ") == 0


def _ratio_of_letters_and_digits_only(text: str) -> float:
    allowed = sum(1 for char in text if char.isalnum() or char in {"_", "-", ":", "/", "."})
    return (allowed / max(len(text), 1))


def feature_plan_to_json_text(feature_plan: FeaturePlan) -> str:
    """Serialize plan back to JSON text for repair prompts."""
    payload = {
        "feature": feature_plan.title,
        "tags": feature_plan.tags,
        "scenarios": [
            {
                "name": scenario.name,
                "tags": scenario.tags,
                "steps": [
                    {
                        "keyword": step.keyword,
                        "step_id": step.step_id,
                        "params": step.params,
                        "docstring": step.docstring,
                        "datatable": step.datatable,
                    }
                    for step in scenario.steps
                ],
            }
            for scenario in feature_plan.scenarios
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)

