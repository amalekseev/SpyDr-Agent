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

