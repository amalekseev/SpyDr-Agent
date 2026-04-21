# SpyDR Agent — Инструкция по установке и использованию

SpyDR Agent — плагин для VS Code, который генерирует BDD-тесты в формате `.feature` (Gherkin) на основе описания на естественном языке.

---

## Требования

Перед установкой убедись, что на компьютере установлено:

- **Python 3.10+**
  - macOS: `brew install python3`
  - Windows: скачать с [python.org](https://www.python.org/downloads/) — при установке поставить галочку **"Add to PATH"**
  - Linux: `sudo apt install python3 python3-venv`
- **Git** — [git-scm.com](https://git-scm.com/downloads)
- **VS Code** — [code.visualstudio.com](https://code.visualstudio.com)

Проверить установку:
```bash
python3 --version   # должно быть 3.10 или выше
git --version
```

---

## Установка плагина

### Вариант А — через файл `.vsix`

1. Получи файл `spydr-agent-0.1.0.vsix`
2. Открой VS Code
3. Нажми **Cmd+Shift+P** (macOS) или **Ctrl+Shift+P** (Windows/Linux)
4. Введи: `Extensions: Install from VSIX`
5. Выбери полученный файл `.vsix`
6. Перезапусти VS Code когда появится запрос

### Вариант Б — через репозиторий (для разработчиков)

```bash
git clone https://github.com/D1105/glowing-funicular
cd glowing-funicular/vscode_plugin
npm install
npm run compile
```

Затем открой папку `vscode_plugin` в VS Code и нажми **F5**.

---

## Первый запуск

При первом открытии плагин **автоматически**:
1. Клонирует бэкенд в папку `~/.spydr/backend/`
2. Создаёт виртуальное Python-окружение
3. Устанавливает все зависимости

> ⏳ **Первый запуск занимает 3–7 минут.** Прогресс можно видеть в:
> `View → Output → SpyDR Agent`

---

## Настройка

Открой панель SpyDR (иконка в левом sidebar) → вкладка **Settings**.

| Поле | Описание | Пример |
|---|---|---|
| **OpenAI API Key** | Секретный ключ OpenAI | `sk-...` |
| **Connection String** | Строка подключения к PostgreSQL | `postgresql://user:pass@host/db` |
| **LLM Model** | Модель для генерации | `gpt-4.1-mini` |
| **Output File** | Путь к `.feature` файлу (относительно корня проекта или абсолютный) | `tests/generated.feature` |

Настройки сохраняются автоматически — появится зелёная надпись **Saved**.

> **Где взять OpenAI API Key:** [platform.openai.com/api-keys](https://platform.openai.com/api-keys)

---

## Использование

1. Открой панель **SpyDR Agent** в левом sidebar
2. Дождись пока исчезнет баннер "Starting backend…" и кнопка **Send** станет активной
3. Введи описание теста и нажми **Enter**

### Примеры запросов

```
Пользователь входит в систему с корректными данными и видит главную страницу
```

```
Пользователь вводит неверный пароль и видит сообщение об ошибке
```

```
Незарегистрированный пользователь пытается оформить заказ и попадает на страницу авторизации
```

### Что происходит после отправки

- В баннере появляются статусы: `Ищу шаги…`, `Генерирую сценарии…`
- Агент генерирует `.feature` файл и **открывает его автоматически**
- Ответ агента отображается в чате

---

## Если что-то пошло не так

**Кнопка Send не активируется**
- Проверь `View → Output → SpyDR Agent` — там будет описание ошибки
- Убедись что Python 3.10+ установлен и доступен в PATH
- Заполни OpenAI API Key и Connection String в настройках

**Ошибка "Backend process exited"**
- Открой `View → Output → SpyDR Agent` — там причина
- Чаще всего: неверный API ключ или строка подключения к БД
- После исправления настроек: **Cmd+Shift+P** → `SpyDR: Restart Backend`

**Переустановить бэкенд с нуля**
```bash
rm -rf ~/.spydr/backend
```
Затем **Cmd+Shift+P** → `SpyDR: Restart Backend`
