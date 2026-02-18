# auto-spydr baseline: быстрый запуск

```bash
# 1) Установка зависимостей
pip install -r requirements.txt

# 2) Выбор LLM-провайдера и моделей через конфиг (ENV)
export BASELINE_LLM_PROVIDER="openai"           # openai | gigachat
export BASELINE_MODEL="gpt-4.1-nano"
export BASELINE_EMBEDDING_MODEL="text-embedding-3-large"

# 3) Авторизация провайдера
# OpenAI:
export OPENAI_API_KEY="your_openai_api_key"
# GigaChat (только сертификатная аутентификация mTLS):
export GIGACHAT_CERT_FILE="/path/to/client.crt"
export GIGACHAT_KEY_FILE="/path/to/client.key"
# опционально:
# export GIGACHAT_KEY_PASSWORD="..."
# export GIGACHAT_CA_BUNDLE_FILE="/path/to/ca.pem"

# 4) URL PostgreSQL с pgvector (пример под ваше окружение)
export BASELINE_RAG_DB_URL="postgresql://postgres:mypassword@localhost:5488/postgres"

# 5) Первый запуск: переиндексация шагов + конвертация
python baseline/main.py manual_tests/tests \
  --reindex-steps \
  --db-url "$BASELINE_RAG_DB_URL"

# 6) Обычный запуск без переиндексации
python baseline/main.py manual_tests/tests \
  --db-url "$BASELINE_RAG_DB_URL"

# 7) Переключение через CLI (переопределяет ENV)
python baseline/main.py manual_tests/tests \
  --llm-provider gigachat \
  --model GigaChat-2-Max \
  --embedding-model Embeddings \
  --db-url "$BASELINE_RAG_DB_URL" \
  --reindex-steps

# 8) Запуск с другой моделью эмбеддингов
python baseline/main.py manual_tests/tests \
  --db-url "$BASELINE_RAG_DB_URL" \
  --embedding-model text-embedding-3-large \
  --reindex-steps

# 9) Запуск с Phoenix tracing (детально по запросам и tool-calls)
python baseline/main.py manual_tests/tests \
  --db-url "$BASELINE_RAG_DB_URL" \
  --trace-phoenix \
  --phoenix-endpoint http://127.0.0.1:6006/v1/traces \
  --phoenix-service-name baseline-rag-agent \
  -v
```

## Expert Metrics App

Simple Streamlit app for expert evaluation in a blind single-answer mode:
for each manual test the app shows only one `.feature` file (golden or generated).

### Data layout

- Manual tests: `manual_tests/tests/*.txt`
- Golden reference features: `golden_features/*.feature`
- Optional preset candidates: any folder with `*.feature` files
- Results sessions: `metrics_results/<session_id>/`

### Install

```bash
pip install -r requirements.txt
```

### Run

```bash
python scripts/run_metrics_app.py \
  --manual-tests-dir manual_tests/tests \
  --golden-features-dir golden_features \
  --preset-features-dir baseline/features \
  --results-dir metrics_results
```

Then open the URL shown by Streamlit (default `http://localhost:8501`).

Notes:

- The expert does not choose source type in UI.
- For each test, app automatically shows one file:
  - golden reference, or
  - generated candidate (preset if available, otherwise live generation).
- Golden-vs-generated sampling probability is controlled by hidden config
  `METRICS_GOLDEN_SAMPLE_PROB` (default `0.5`).

### Session output format

Each session writes:

- `metrics_results/<session_id>/evaluations.jsonl` - full per-test detailed records
- `metrics_results/<session_id>/summary.csv` - flattened table for quick analysis
- `metrics_results/<session_id>/metadata.json` - session metadata (expert, dirs, timestamps, schema version)

The report also stores which exact file was evaluated and whether it was golden.

Share the whole `metrics_results/<session_id>/` folder after expert review is done.