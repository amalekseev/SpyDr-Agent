# SpyDR Agent — VS Code Plugin

AI-powered BDD test generation. Describe a test scenario in plain language — the agent generates a ready-to-use Gherkin `.feature` file.

---

## Prerequisites

Before installing the plugin, make sure you have:

| Requirement | Version | How to check |
|---|---|---|
| **Python** | 3.10 or newer | `python3 --version` |
| **Git** | any | `git --version` |
| **OpenAI API key** | — | [platform.openai.com](https://platform.openai.com/api-keys) |
| **PostgreSQL** | 14+ with pgvector | connection string like `postgresql://user:pass@host/db` |

> **macOS:** if Python is not installed, run `brew install python3`  
> **Windows:** download from [python.org](https://www.python.org/downloads/)

---

## Installation

### Option A — Install from `.vsix` file (recommended for end users)

1. Download the latest `spydr-agent-*.vsix` from the releases page.
2. Open VS Code.
3. Open the Command Palette (`Cmd+Shift+P` / `Ctrl+Shift+P`).
4. Type **"Extensions: Install from VSIX..."** and select the downloaded file.
5. Reload VS Code when prompted.

### Option B — Install from source (for developers)

```bash
git clone https://github.com/D1105/glowing-funicular
cd glowing-funicular/vscode_plugin   # adjust path if needed

npm install
npm run compile

# Install vsce if you don't have it
npm install -g @vscode/vsce

# Package
vsce package

# Install
code --install-extension spydr-agent-0.1.0.vsix
```

---

## First-time setup

The plugin sets itself up **automatically** on first launch:

1. Clones the backend repository to `~/.spydr/backend/`
2. Creates a Python virtual environment at `~/.spydr/backend/.venv`
3. Installs all Python dependencies

> **First launch may take 2–5 minutes** depending on your internet connection. Progress is shown in the **SpyDR Agent** output channel (`View → Output → SpyDR Agent`).

---

## Configuration

Open the plugin sidebar (click the SpyDR icon in the Activity Bar), then switch to the **Settings** tab.

| Setting | Description | Example |
|---|---|---|
| **OpenAI API Key** | Your OpenAI secret key | `sk-...` |
| **Connection String** | PostgreSQL connection string | `postgresql://user:pass@localhost/spydr` |
| **LLM Model** | Model to use for generation | `gpt-4.1-mini` |
| **Output File** | Path to save the `.feature` file. Relative paths resolve from workspace root | `tests/generated.feature` |
| **Project ID** | Project identifier (reserved, optional) | `my-project` |

All settings are saved automatically after a short pause — you will see a green **Saved** indicator.

---

## Usage

1. Open the **SpyDR Agent** panel from the Activity Bar (left sidebar).
2. Wait for the banner to disappear — the backend is ready when the **Send** button becomes active.
3. Type your test scenario in the chat box and press **Enter** (or click **Send**).
4. The agent will:
   - Show live status updates while thinking
   - Generate a `.feature` file and open it automatically
   - Display its response in the chat

**Example prompts:**

```
User logs in with valid credentials and sees the dashboard
```

```
User tries to log in with wrong password and sees an error message
```

---

## Commands

Open the Command Palette (`Cmd+Shift+P` / `Ctrl+Shift+P`) and search for:

| Command | Description |
|---|---|
| **SpyDR: Restart Backend** | Stop and restart the Python backend process. Use this if the backend crashes or hangs. |

---

## Troubleshooting

**The Send button stays disabled after launch**

- Open `View → Output → SpyDR Agent` to see setup progress.
- Make sure Python 3.10+ is installed and available in your PATH.
- Make sure your **OpenAI API Key** and **Connection String** are filled in the Settings tab.

**Setup fails with "Python 3 not found"**

- macOS: `brew install python3`
- Windows: install from [python.org](https://www.python.org/downloads/) and check "Add to PATH"
- Linux: `sudo apt install python3 python3-venv`

**"Backend process exited" error**

- Open `View → Output → SpyDR Agent` — the error details are printed there.
- Most common cause: missing or incorrect **OpenAI API Key** or **Connection String**.
- Use the command **SpyDR: Restart Backend** after fixing the settings.

**Re-install the backend from scratch**

```bash
rm -rf ~/.spydr/backend
```

Then use **SpyDR: Restart Backend** — the plugin will clone and set up everything again.

---

## How it works

```
VS Code Plugin (TypeScript)
        │  JSON-lines over stdio
        ▼
Python Backend (~/.spydr/backend/)
        │  LangGraph agent
        ▼
  OpenAI API  +  pgvector (RAG)
        │
        ▼
  .feature file written to disk
```

The plugin communicates with the Python backend via stdin/stdout using newline-delimited JSON. No HTTP server is required — everything runs locally.
