import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from baseline.core.agent_protocol import parse_agent_response
from baseline.core.step_parser import StepIdCounter, build_step_id, extract_placeholders
from baseline.core.step_renderer import render_feature_from_plan


def test_step_id_format():
    counter = StepIdCounter()
    first = build_step_id(counter)
    second = build_step_id(counter)
    third = build_step_id(counter)
    fourth = build_step_id(counter)
    assert first == "S-1"
    assert second == "S-2"
    assert third == "S-3"
    assert fourth == "S-4"

    multi = build_step_id(counter)
    assert multi == "S-5"


def test_render_feature_uses_step_id_and_params():
    payload = {
        "feature": "Проверка API",
        "scenarios": [
            {
                "name": "Базовый вызов",
                "steps": [
                    {
                        "keyword": "Given",
                        "step_id": "S-1",
                        "params": {"url": "http://localhost:8080"},
                    }
                ],
            }
        ],
    }
    plan = parse_agent_response(str(payload).replace("'", '"'))
    steps_index = {
        "S-1": {
            "pattern": 'установлен базовый URL "{url}"',
            "placeholders": extract_placeholders('установлен базовый URL "{url}"'),
        }
    }
    feature_text, metrics = render_feature_from_plan(feature_plan=plan, steps_index=steps_index)
    assert 'Given установлен базовый URL "http://localhost:8080"' in feature_text
    assert metrics["rag_unresolved_steps"] == 0


def test_render_feature_fails_on_missing_param():
    payload = {
        "feature": "Проверка API",
        "scenarios": [
            {
                "name": "Неполный шаг",
                "steps": [
                    {
                        "keyword": "Given",
                        "step_id": "S-1",
                        "params": {},
                    }
                ],
            }
        ],
    }
    plan = parse_agent_response(str(payload).replace("'", '"'))
    steps_index = {
        "S-1": {
            "pattern": 'установлен базовый URL "{url}"',
            "placeholders": extract_placeholders('установлен базовый URL "{url}"'),
        }
    }
    try:
        render_feature_from_plan(feature_plan=plan, steps_index=steps_index)
    except ValueError as exc:
        assert "Отсутствуют параметры" in str(exc)
    else:
        raise AssertionError("Ожидали ValueError при отсутствии обязательного параметра")


def test_render_feature_renders_docstring_for_colon_steps():
    payload = {
        "feature": "Проверка SQL",
        "scenarios": [
            {
                "name": "Запрос в базу",
                "steps": [
                    {
                        "keyword": "When",
                        "step_id": "S-1",
                        "params": {"db_name": "postgres_mock_raw"},
                        "docstring": "sql\nselect 1;",
                    }
                ],
            }
        ],
    }
    plan = parse_agent_response(str(payload).replace("'", '"'))
    steps_index = {
        "S-1": {
            "pattern": 'Выполнить запрос в базу "{db_name}":',
            "placeholders": extract_placeholders('Выполнить запрос в базу "{db_name}":'),
        }
    }
    feature_text, _ = render_feature_from_plan(feature_plan=plan, steps_index=steps_index)
    assert 'When Выполнить запрос в базу "postgres_mock_raw":' in feature_text
    assert '"""' in feature_text
    assert "select 1;" in feature_text


def test_render_feature_fails_when_docstring_missing_for_colon_step():
    payload = {
        "feature": "Проверка SQL",
        "scenarios": [
            {
                "name": "Запрос в базу без тела",
                "steps": [
                    {
                        "keyword": "When",
                        "step_id": "S-1",
                        "params": {"db_name": "postgres_mock_raw"},
                    }
                ],
            }
        ],
    }
    plan = parse_agent_response(str(payload).replace("'", '"'))
    steps_index = {
        "S-1": {
            "pattern": 'Выполнить запрос в базу "{db_name}":',
            "placeholders": extract_placeholders('Выполнить запрос в базу "{db_name}":'),
        }
    }
    try:
        render_feature_from_plan(feature_plan=plan, steps_index=steps_index)
    except ValueError as exc:
        assert "требует docstring" in str(exc)
    else:
        raise AssertionError("Ожидали ValueError при отсутствии docstring")


def test_render_feature_fails_when_docstring_missing_for_signature_required_step():
    payload = {
        "feature": "Проверка SQL",
        "scenarios": [
            {
                "name": "Запрос без SQL",
                "steps": [
                    {
                        "keyword": "When",
                        "step_id": "S-2",
                        "params": {"db_name": "postgres_mock_raw"},
                    }
                ],
            }
        ],
    }
    plan = parse_agent_response(str(payload).replace("'", '"'))
    steps_index = {
        "S-2": {
            "pattern": 'Выполнить запрос в базу "{db_name}"',
            "placeholders": extract_placeholders('Выполнить запрос в базу "{db_name}"'),
            "requires_docstring": True,
        }
    }
    try:
        render_feature_from_plan(feature_plan=plan, steps_index=steps_index)
    except ValueError as exc:
        assert "требует docstring" in str(exc)
    else:
        raise AssertionError("Ожидали ValueError при отсутствии docstring для шага с requires_docstring")

