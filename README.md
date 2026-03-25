# auto-spydr

Платформа для автоматической конвертации ручных тестов в Gherkin-сценарии с помощью LLM, а также для экспертной оценки качества генерации.

## Быстрый старт — плагин GigaIDE

Основной способ работы с агентом — плагин для **GigaIDE** (IntelliJ-based).
Плагин сам настраивает Python-окружение при первом запуске.

### 1. Установка плагина

1. Скачайте файл `spydr-plugin-1.0.0.zip` из [Releases](#) (или соберите сами — см. [Сборка из исходников](#сборка-плагина-из-исходников)).
2. Откройте GigaIDE → **Settings → Plugins → ⚙️ → Install Plugin from Disk…**
3. Выберите скачанный `.zip` файл.
4. Перезапустите IDE.

### 2. Настройка API-ключей

Создайте файл `.env` в удобном месте (например, в домашней директории) с нужными переменными:

**OpenAI:**

```env
OPENAI_API_KEY=sk-...
```

**GigaChat (mTLS-сертификаты):**

```env
GIGACHAT_CERT_FILE=/path/to/client.crt
GIGACHAT_KEY_FILE=/path/to/client.key
# Опционально:
# GIGACHAT_KEY_PASSWORD=...
# GIGACHAT_CA_BUNDLE_FILE=/path/to/ca.pem
# GIGACHAT_AUTH_URL=...
# GIGACHAT_BASE_URL=...
```

**База данных (PostgreSQL + pgvector):**

```env
CONNECTION_STRING=postgresql://postgres:password@localhost:5432/postgres
```

Затем укажите путь к этому файлу в настройках плагина:
**Settings → Tools → SpyDR Agent → `.env файл`**

### 3. Использование

1. Откройте панель **SpyDR Agent** (правая боковая панель IDE).
2. При первом запуске плагин автоматически:
   - извлечёт Python-бэкенд,
   - найдёт Python 3 в системе,
   - создаст виртуальное окружение,
   - установит зависимости.
3. Выберите проект и укажите путь к целевому `.feature` файлу в настройках панели.
4. Пишите запросы в чат — агент сгенерирует Gherkin-сценарий и запишет его в файл.
5. Файл автоматически откроется в редакторе IDE.

### Системные требования

| | Требование |
|---|---|
| **IDE** | GigaIDE 2024.1+ (или IntelliJ IDEA 2024.1+) |
| **Python** | 3.10+ (должен быть в PATH) |
| **ОС** | Windows, macOS, Linux |

> **Debian/Ubuntu:** если `python3` установлен, но плагин не может создать venv,
> выполните: `sudo apt install python3-venv`

### Настройки плагина

**Settings → Tools → SpyDR Agent:**

| Поле | Описание |
|---|---|
| **Python** | Путь к интерпретатору. Оставьте пустым — плагин найдёт сам |
| **.env файл** | Путь к файлу с API-ключами и переменными окружения |
| **Feature директория** | Директория по умолчанию для `.feature` файлов |

---

## Сборка плагина из исходников

Для разработчиков и тех, кто хочет собрать плагин самостоятельно.

### Требования

- JDK 17+
- Git

### Команды

```bash
git clone <repo-url>
cd auto-spydr/plugin

# Gradle Wrapper уже в репозитории — Gradle устанавливать не нужно
./gradlew buildPlugin
```

Готовый zip:

```
plugin/build/distributions/spydr-plugin-1.0.0.zip
```

---

## Структура проекта

```
auto-spydr/
├── plugin/                       # GigaIDE плагин (Kotlin/Gradle)
│   ├── build.gradle.kts          # Сборка плагина + бандлинг Python-бэкенда
│   ├── src/main/kotlin/          # Kotlin-исходники плагина
│   │   └── com/spydr/plugin/
│   │       ├── SpydrToolWindowFactory.kt  # Фабрика окна инструментов
│   │       ├── backend/                   # Управление Python-процессом
│   │       │   ├── PythonEnvironmentManager.kt  # Автонастройка окружения
│   │       │   ├── PythonProcessManager.kt      # Запуск и общение с бэкендом
│   │       │   ├── MessageProtocol.kt           # JSON-lines протокол
│   │       │   └── BackendListener.kt           # Интерфейс обратных вызовов
│   │       ├── ui/                        # UI-компоненты
│   │       │   ├── SpydrPanel.kt          # Главная панель
│   │       │   ├── ChatPanel.kt           # Чат с агентом
│   │       │   └── SettingsPanel.kt       # Настройки в панели
│   │       └── settings/                  # Персистентные настройки
│   │           ├── SpydrSettingsState.kt
│   │           └── SpydrSettingsConfigurable.kt
│   └── src/main/resources/
│       └── META-INF/plugin.xml    # Дескриптор плагина
├── src/                           # Python-бэкенд (агент SpyDR)
│   ├── agents/                    # LangGraph-агент
│   │   ├── agent.py               # SpydrAgent — основной класс
│   │   ├── base.py                # Базовый класс агента
│   │   ├── tools.py               # Инструменты (search_steps, add_step и др.)
│   │   ├── models.py              # Состояние агента (AgentState)
│   │   ├── validator.py           # Валидатор сгенерированных feature
│   │   ├── config.yml             # Параметры LLM агента
│   │   └── prompts/               # Промпты агента
│   ├── api/
│   │   ├── stdio_server.py        # JSON-lines сервер (stdin/stdout)
│   │   ├── __main__.py            # Точка входа: python -m src.api
│   │   ├── models.py              # Pydantic-модели ответов
│   │   └── dependencies.py        # Инициализация агента
│   ├── configs/
│   │   └── config.yml             # Глобальный конфиг (RAG, эмбеддинги)
│   └── utils/                     # Утилиты (эмбеддинги, шаги, стриминг)
├── docs/                          # Документация проекта (для RAG)
├── RULES.md                       # Пользовательские правила для агента
└── requirements.txt               # Python-зависимости
```

## Переменные окружения

### Выбор LLM-провайдера

Провайдер и модель задаются в `src/agents/config.yml`:

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

### Авторизация

**OpenAI:**

```bash
OPENAI_API_KEY=sk-...
```

**GigaChat (mTLS):**

```bash
GIGACHAT_CERT_FILE=/path/to/client.crt
GIGACHAT_KEY_FILE=/path/to/client.key
# Опционально:
# GIGACHAT_KEY_PASSWORD=...
# GIGACHAT_CA_BUNDLE_FILE=/path/to/ca.pem
```

### База данных

```bash
CONNECTION_STRING=postgresql://postgres:password@localhost:5432/postgres
```

## Разработка без плагина

Бэкенд можно запустить напрямую (для отладки):

```bash
# Создайте venv и установите зависимости
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Запуск stdio-сервера (общение через JSON-lines в stdin/stdout)
python -m src.api.stdio_server
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
