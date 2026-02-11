# auto-spydr baseline: быстрый запуск

```bash
# 1) Установка зависимостей
pip install -r requirements.txt

# 2) Экспорт ключа OpenAI (если еще не в .env)
export OPENAI_API_KEY="your_openai_api_key"

# 3) URL PostgreSQL с pgvector (пример под ваше окружение)
export BASELINE_RAG_DB_URL="postgresql://postgres:mypassword@localhost:5488/postgres"

# 4) Первый запуск: переиндексация шагов + конвертация
python baseline/main.py manual_tests/tests \
  --reindex-steps \
  --db-url "$BASELINE_RAG_DB_URL"

# 5) Обычный запуск без переиндексации
python baseline/main.py manual_tests/tests \
  --db-url "$BASELINE_RAG_DB_URL"

# 6) Запуск с другой моделью эмбеддингов
python baseline/main.py manual_tests/tests \
  --db-url "$BASELINE_RAG_DB_URL" \
  --embedding-model text-embedding-3-large \
  --reindex-steps

# 7) Запуск с Phoenix tracing (детально по запросам и tool-calls)
python baseline/main.py manual_tests/tests \
  --db-url "$BASELINE_RAG_DB_URL" \
  --trace-phoenix \
  --phoenix-endpoint http://127.0.0.1:6006/v1/traces \
  --phoenix-service-name baseline-rag-agent \
  -v
```

