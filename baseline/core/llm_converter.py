"""OpenAI tool-calling agent for manual-test to strict step-id plans."""

import json
import os
import time
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from .agent_protocol import FeaturePlan, parse_agent_response
from .rag_store import StepRAGStore
from .tracing import get_tracer

load_dotenv()
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
    '        {"keyword":"Given","step_id":"given_xxx","params":{"name":"value"},"docstring":null}\n'
    "      ]\n"
    "    }\n"
    "  ]\n"
    "}\n"
    "Правила:\n"
    "1) Каждый шаг обязан иметь существующий step_id.\n"
    "2) params должны содержать значения для ВСЕХ плейсхолдеров выбранного шага. ВАЖНО: внимательно проверь pattern шага - каждый плейсхолдер в фигурных скобках {name} требует соответствующего параметра в params.\n"
    "3) КРИТИЧЕСКИ ВАЖНО: Если выбранный pattern оканчивается на ':', шаг ОБЯЗАТЕЛЬНО требует docstring. Ты ДОЛЖЕН передать docstring в JSON, даже если это пустая строка или пробелы - передай хотя бы минимальное содержимое.\n"
    "4) Если шаг требует docstring или datatable (определяется по сигнатуре step-функции), ты ОБЯЗАН передать docstring в JSON. Без docstring такой шаг не будет работать.\n"
    "5) Для SQL-шагов вида 'Выполнить запрос в базу ...' также обязательно передавай SQL в docstring, даже если в pattern нет ':'.\n"
    "6) docstring передавай как обычную JSON-строку с переносами \\n (без тройных кавычек в самом JSON).\n"
    "7) Никаких новых шагов, только найденные через tool.\n"
    "8) Язык названий feature/scenario - русский.\n"
    "9) При выборе шага из результатов search_steps, обязательно извлеки из pattern все плейсхолдеры и заполни их в params на основе контекста ручного теста."
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


def get_openai_client() -> OpenAI:
    """Create OpenAI client from environment."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY не найден. Установите переменную окружения или создайте .env файл."
        )
    return OpenAI(api_key=api_key)


def build_user_prompt(test_content: str, feature_name: str) -> str:
    """Build user prompt for conversion request."""
    return f"""Конвертируй следующий ручной тест в Gherkin feature файл.

Название Feature: {feature_name}

Содержимое теста для конвертации:
---
{test_content}
---

Используй tool search_steps, затем верни ТОЛЬКО JSON структуры feature/scenarios/steps.
Шаги в JSON задавай через step_id, params и (при необходимости) docstring."""


def _build_repair_prompt(repair_feedback: str) -> str:
    """Build follow-up instruction for repairing invalid/partial plan."""
    return (
        "Исправь предыдущий JSON-план с учетом ошибок валидации.\n"
        "Верни ТОЛЬКО обновленный валидный JSON по той же схеме.\n\n"
        f"Ошибки и контекст:\n{repair_feedback}"
    )


def build_feature_plan(
    client: OpenAI,
    test_content: str,
    feature_name: str,
    model: str,
    rag_store: StepRAGStore,
    rag_top_k: int = 8,
    verbose: bool = False,
    repair_feedback: str | None = None,
) -> tuple[FeaturePlan, int]:
    """Build strict feature plan where each step is selected by step_id."""
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(test_content, feature_name)},
    ]
    if repair_feedback:
        messages.append({"role": "user", "content": _build_repair_prompt(repair_feedback)})

    total_tool_calls = 0
    with TRACER.start_as_current_span("baseline.agent.plan_generation") as span:
        span.set_attribute("llm.model", model)
        span.set_attribute("llm.rag_top_k", rag_top_k)
        for round_idx in range(1, MAX_TOOL_CALL_ROUNDS + 1):
            with TRACER.start_as_current_span("baseline.agent.round") as round_span:
                round_span.set_attribute("llm.round_index", round_idx)
                round_span.set_attribute("llm.messages_count", len(messages))
                if verbose:
                    print(f"    [agent] Раунд {round_idx}: отправка запроса в chat.completions...")
                started_at = time.perf_counter()
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    tools=TOOL_SPEC,
                    tool_choice="auto",
                    response_format={"type": "json_object"},
                    temperature=0,
                )
                elapsed = time.perf_counter() - started_at
                round_span.set_attribute("llm.round_latency_sec", elapsed)
                usage = getattr(response, "usage", None)
                if usage:
                    round_span.set_attribute("llm.prompt_tokens", int(getattr(usage, "prompt_tokens", 0) or 0))
                    round_span.set_attribute(
                        "llm.completion_tokens", int(getattr(usage, "completion_tokens", 0) or 0)
                    )
                    round_span.set_attribute("llm.total_tokens", int(getattr(usage, "total_tokens", 0) or 0))
                if verbose:
                    print(f"    [agent] Раунд {round_idx}: ответ получен за {elapsed:.2f}s")
                message = response.choices[0].message
                tool_calls = message.tool_calls or []
                if not tool_calls:
                    content = message.content or ""
                    if verbose:
                        print("    [agent] Tool-вызовов нет, парсинг финального JSON...")
                    try:
                        return parse_agent_response(content), total_tool_calls
                    except (json.JSONDecodeError, ValueError) as exc:
                        round_span.record_exception(exc)
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
                    tool_result = _execute_tool_call(
                        tool_call_name=tool_call.function.name,
                        tool_call_arguments=tool_call.function.arguments,
                        rag_store=rag_store,
                        rag_top_k=rag_top_k,
                        verbose=verbose,
                    )
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(tool_result, ensure_ascii=False),
                        }
                    )

    raise ValueError("Агент не смог завершить конвертацию: превышено число tool-вызовов.")


def _execute_tool_call(
    *,
    tool_call_name: str,
    tool_call_arguments: str,
    rag_store: StepRAGStore,
    rag_top_k: int,
    verbose: bool = False,
) -> dict[str, Any]:
    """Execute one tool call from the model and return serializable output."""
    with TRACER.start_as_current_span("baseline.agent.tool_call") as span:
        span.set_attribute("tool.name", tool_call_name)
        if tool_call_name != "search_steps":
            return {"error": f"Неизвестный tool: {tool_call_name}"}
        try:
            args = json.loads(tool_call_arguments or "{}")
        except json.JSONDecodeError:
            return {"error": "Аргументы tool должны быть валидным JSON."}
        query = str(args.get("query", "")).strip()
        if not query:
            return {"error": "Аргумент query обязателен."}
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
                    }
                    for step in scenario.steps
                ],
            }
            for scenario in feature_plan.scenarios
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)

