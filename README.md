# auto-spydr

Платформа для автоматической конвертации ручных тестов в Gherkin-сценарии с помощью LLM, а также для экспертной оценки качества генерации.

## Структура проекта

```
auto-spydr/
├── baseline/                  # Batch-пайплайн конвертации ручных тестов → .feature
│   ├── main.py                # CLI-точка входа пайплайна
│   ├── parser.py              # CLI-парсер pytest-bdd шагов → steps.json
│   ├── core/                  # Ядро пайплайна
│   │   ├── pipeline.py        # Оркестрация конвертации
│   │   ├── llm_converter.py   # Взаимодействие с LLM (agent / tool-calling)
│   │   ├── llm_compat.py      # Адаптеры провайдеров (OpenAI, GigaChat)
│   │   ├── rag_store.py       # Векторное хранилище шагов (pgvector)
│   │   ├── step_parser.py     # Парсинг шагов из pytest-bdd исходников
│   │   ├── step_renderer.py   # Рендер JSON-плана в .feature текст
│   │   ├── steps_catalog.py   # Загрузка и индексация steps.json
│   │   ├── constants.py       # Константы и значения по умолчанию
│   │   ├── models.py          # Pydantic-модели результатов
│   │   ├── tracing.py         # Логирование и OpenTelemetry/Phoenix трейсинг
│   │   └── io_utils.py        # Файловые утилиты
│   ├── features/              # Сгенерированные .feature файлы (выход пайплайна)
│   └── tests/                 # Тесты пайплайна
├── src/                       # Интерактивный агент SpyDR (Streamlit-чат)
│   ├── agents/                # LangGraph-агент
│   │   ├── agent.py           # SpydrAgent — основной класс агента
│   │   ├── base.py            # Базовый класс агента
│   │   ├── tools.py           # Инструменты агента (search_steps, add_step и др.)
│   │   ├── models.py          # Состояние агента (AgentState, ScenarioDraft)
│   │   ├── config.yml         # Параметры LLM агента
│   │   └── prompts/           # Системный промпт агента
│   ├── api/
│   │   ├── streamlit_app.py   # Streamlit UI (чат с агентом)
│   │   └── dependencies.py    # Инициализация агента
│   ├── configs/
│   │   └── config.yml         # Глобальный конфиг (эмбеддинги, docstring-валидация)
│   └── utils/                 # Утилиты (эмбеддинги, шаги, стриминг)
├── gherkin/                   # Эталонные .feature файлы и pytest-bdd шаги
│   ├── features/              # .feature файлы (источник шагов)
│   └── tests/                 # pytest-bdd step-определения и запуск
├── golden_features/           # Эталонные .feature для экспертной оценки
├── manual_tests/              # Ручные тесты (.txt)
│   ├── tests/                 # Входные ручные тесты
│   └── generator/             # Генератор ручных тестов из .feature через LLM
├── metrics_app/               # Streamlit-приложение экспертной оценки
├── metrics_results/           # Результаты экспертных сессий
├── scripts/                   # Вспомогательные скрипты
│   ├── run_metrics_app.py     # Запуск приложения экспертной оценки
│   ├── run_tests_with_metrics.py  # Прогон .feature через pytest-bdd с метриками
│   └── generate_human_tests.py    # Генерация ручных тестов из .feature
├── logs/                      # Логи пайплайна
├── steps.json                 # Каталог BDD-шагов (генерируется парсером)
├── RULES.md                   # Пользовательские правила для агента
└── requirements.txt           # Python-зависимости
```

## Установка

```bash
pip install -r requirements.txt
```

### Требования

- Python 3.11+
- PostgreSQL с расширением pgvector (для RAG-индекса шагов)

## Переменные окружения

### Выбор LLM-провайдера

```bash
export BASELINE_LLM_PROVIDER="openai"           # openai | gigachat
export BASELINE_MODEL="gpt-4.1-nano"
export BASELINE_EMBEDDING_MODEL="text-embedding-3-large"
```

### Авторизация

**OpenAI:**

```bash
export OPENAI_API_KEY="sk-..."
```

**GigaChat (сертификатная аутентификация mTLS):**

```bash
export GIGACHAT_CERT_FILE="/path/to/client.crt"
export GIGACHAT_KEY_FILE="/path/to/client.key"
# Опционально:
# export GIGACHAT_KEY_PASSWORD="..."
# export GIGACHAT_CA_BUNDLE_FILE="/path/to/ca.pem"
```

### База данных

```bash
export BASELINE_RAG_DB_URL="postgresql://postgres:mypassword@localhost:5488/postgres"
```

## Использование

### 1. Парсинг шагов

Извлечение BDD-шагов из pytest-bdd исходников в `steps.json`:

```bash
python baseline/parser.py gherkin/tests/steps -o steps.json -v
```

### 2. Batch-конвертация (baseline)

Конвертация папки с ручными тестами в `.feature` файлы через LLM.

**Первый запуск** (с переиндексацией шагов в pgvector):

```bash
python baseline/main.py manual_tests/tests \
  --reindex-steps \
  --db-url "$BASELINE_RAG_DB_URL"
```

**Обычный запуск** (без переиндексации):

```bash
python baseline/main.py manual_tests/tests \
  --db-url "$BASELINE_RAG_DB_URL"
```

**Переключение провайдера через CLI** (переопределяет ENV):

```bash
python baseline/main.py manual_tests/tests \
  --llm-provider gigachat \
  --model GigaChat-2-Max \
  --embedding-model Embeddings \
  --db-url "$BASELINE_RAG_DB_URL" \
  --reindex-steps
```

**С Phoenix трейсингом:**

```bash
python baseline/main.py manual_tests/tests \
  --db-url "$BASELINE_RAG_DB_URL" \
  --trace-phoenix \
  --phoenix-endpoint http://127.0.0.1:6006/v1/traces \
  --phoenix-service-name baseline-rag-agent \
  -v
```

Все доступные аргументы: `python baseline/main.py --help`

### 3. Интерактивный агент SpyDR (Streamlit-чат)

Чат-интерфейс для пошаговой сборки `.feature` файлов с помощью LLM-агента.
Агент ищет подходящие BDD-шаги через RAG и собирает сценарий через tool-calling.

```bash
streamlit run src/api/streamlit_app.py
```

После запуска откройте `http://localhost:8501`.

#### Переключение провайдера

Провайдер LLM и модель задаются в `src/agents/config.yml`:

**OpenAI (по умолчанию):**

```yaml
llm_params:
  provider: openai
  model: gpt-4.1-mini
  temperature: 0
```

**GigaChat:**

```yaml
llm_params:
  provider: gigachat
  model: GigaChat-2-Max
  temperature: 0
```

Для GigaChat необходимо также задать переменные окружения с сертификатами
(см. раздел «Авторизация» выше).

Провайдер эмбеддингов настраивается отдельно в `src/configs/config.yml`:

```yaml
embeddings:
  provider: gigachat          # openai | gigachat
  params:
    model: Embeddings
```

### 4. Прогон сгенерированных тестов

Запуск `.feature` файлов через pytest-bdd с подсчётом метрик (pass rate, число запущенных/пропущенных сценариев):

```bash
python scripts/run_tests_with_metrics.py
```

Скрипт автоматически фильтрует неисполняемые сценарии (шаги без реализации) и выводит итоговую статистику.

### 5. Генерация ручных тестов из .feature

Обратная генерация: из эталонных `.feature` файлов создаются описания ручных тестов (`.txt`) через LLM:

```bash
python scripts/generate_human_tests.py \
  --features-dir gherkin/features \
  --output-dir manual_tests/tests
```

## Экспертная оценка (Metrics App)

Streamlit-приложение для слепой экспертной оценки качества генерации.
Для каждого ручного теста эксперту показывается один `.feature` файл — либо эталонный, либо сгенерированный — без указания источника.

### Запуск

```bash
python scripts/run_metrics_app.py \
  --manual-tests-dir manual_tests/tests \
  --golden-features-dir golden_features \
  --preset-features-dir baseline/features \
  --results-dir metrics_results
```

После запуска откройте `http://localhost:8501`.

Другой порт: `--server-port 8502`

### Как это работает

- Для каждого теста приложение автоматически показывает один файл: эталонный или сгенерированный.
- Вероятность показа эталона задаётся переменной `METRICS_GOLDEN_SAMPLE_PROB` (по умолчанию `0.5`).
- Если предзаготовленного `.feature` нет, запускается генерация «на лету» через baseline-пайплайн.

### Результаты сессии

Каждая сессия записывает:

- `metrics_results/<session_id>/evaluations.jsonl` — детализированные записи по каждому тесту
- `metrics_results/<session_id>/summary.csv` — сводная таблица для анализа
- `metrics_results/<session_id>/metadata.json` — метаданные сессии (эксперт, пути, таймстемпы)
