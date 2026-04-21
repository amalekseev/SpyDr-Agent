"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.SidebarProvider = void 0;
const path = __importStar(require("path"));
const vscode = __importStar(require("vscode"));
const protocol_js_1 = require("./protocol.js");
function nonce() {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    return Array.from({ length: 32 }, () => chars[Math.floor(Math.random() * chars.length)]).join('');
}
class SidebarProvider {
    constructor(extensionUri, manager) {
        this.extensionUri = extensionUri;
        this.manager = manager;
    }
    resolveWebviewView(webviewView) {
        this.view = webviewView;
        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this.extensionUri],
        };
        webviewView.webview.html = this.getHtml(webviewView.webview);
        // Forward backend messages to the webview
        this.manager.on('message', (msg) => {
            switch (msg.type) {
                case 'ready':
                    this.post({ type: 'backendReady' });
                    break;
                case 'text':
                    this.post({ type: 'chunk', text: msg.content ?? '' });
                    break;
                case 'status':
                    this.post({ type: 'status', text: msg.content ?? '' });
                    break;
                case 'feature_written':
                    this.post({ type: 'fileSaved', filePath: msg.path ?? msg.content ?? '' });
                    this.openFile(msg.path ?? msg.content ?? '');
                    break;
                case 'done':
                    this.post({ type: 'done' });
                    break;
                case 'error':
                    this.post({ type: 'error', message: msg.content ?? 'Unknown error' });
                    break;
                case 'session_reset':
                    this.post({ type: 'sessionReset' });
                    break;
            }
        });
        this.manager.on('died', (code) => {
            this.post({ type: 'error', message: `Backend process exited (code ${code}). Use "SpyDR: Restart Backend" to reconnect.` });
            this.post({ type: 'backendDead' });
        });
        // Handle messages from the webview
        webviewView.webview.onDidReceiveMessage(async (msg) => {
            switch (msg.type) {
                case 'ready':
                    this.sendInitSettings();
                    if (this.manager.isRunning()) {
                        this.post({ type: 'backendReady' });
                    }
                    break;
                case 'sendPrompt': {
                    const cfg = vscode.workspace.getConfiguration('spydr');
                    const projectId = cfg.get('projectId', '');
                    const featureFilePath = this.resolveFeaturePath(cfg.get('featureFilePath', ''));
                    this.manager.sendLine((0, protocol_js_1.buildChatMessage)(msg.prompt, {
                        project_id: projectId,
                        feature_file_path: featureFilePath,
                        validation_enabled: false,
                        max_validation_iterations: 3,
                    }));
                    break;
                }
                case 'resetThread':
                    this.manager.sendLine((0, protocol_js_1.buildResetMessage)());
                    break;
                case 'saveSettings': {
                    const config = vscode.workspace.getConfiguration('spydr');
                    const updates = [
                        ['openaiApiKey', msg.openaiApiKey],
                        ['connectionString', msg.connectionString],
                        ['featureFilePath', msg.featureFilePath],
                        ['projectId', msg.projectId],
                        ['llmModel', msg.llmModel],
                    ];
                    for (const [key, val] of updates) {
                        if (typeof val === 'string') {
                            await config.update(key, val.trim(), vscode.ConfigurationTarget.Global);
                        }
                    }
                    break;
                }
            }
        });
    }
    post(msg) {
        this.view?.webview.postMessage(msg);
    }
    sendInitSettings() {
        const cfg = vscode.workspace.getConfiguration('spydr');
        this.post({
            type: 'initSettings',
            openaiApiKey: cfg.get('openaiApiKey', ''),
            connectionString: cfg.get('connectionString', ''),
            featureFilePath: cfg.get('featureFilePath', ''),
            projectId: cfg.get('projectId', ''),
            llmModel: cfg.get('llmModel', 'gpt-4.1-mini'),
        });
    }
    resolveFeaturePath(raw) {
        if (!raw.trim()) {
            return '';
        }
        if (path.isAbsolute(raw)) {
            return raw;
        }
        const folders = vscode.workspace.workspaceFolders;
        if (!folders?.length) {
            return raw;
        }
        return path.join(folders[0].uri.fsPath, raw);
    }
    async openFile(filePath) {
        if (!filePath) {
            return;
        }
        try {
            const doc = await vscode.workspace.openTextDocument(filePath);
            await vscode.window.showTextDocument(doc, { preview: false, preserveFocus: true });
        }
        catch { /* ignore */ }
    }
    getHtml(webview) {
        const n = nonce();
        return /* html */ `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="Content-Security-Policy"
  content="default-src 'none'; style-src 'unsafe-inline'; script-src 'nonce-${n}';">
<title>SpyDR Agent</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: var(--vscode-editor-background);
    color: var(--vscode-editor-foreground);
    font-family: var(--vscode-font-family);
    font-size: var(--vscode-font-size);
    height: 100vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  /* Tab bar */
  #tab-bar {
    display: flex;
    border-bottom: 1px solid var(--vscode-panel-border, rgba(255,255,255,0.08));
    background: var(--vscode-sideBar-background, var(--vscode-editor-background));
    flex-shrink: 0;
  }
  .tab-btn {
    flex: 1;
    background: none;
    border: none;
    border-bottom: 2px solid transparent;
    color: var(--vscode-foreground);
    opacity: 0.5;
    padding: 8px 0;
    font-family: var(--vscode-font-family);
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.4px;
    cursor: pointer;
    transition: opacity 0.15s, border-color 0.15s;
  }
  .tab-btn:hover { opacity: 0.8; }
  .tab-btn.active {
    opacity: 1;
    border-bottom-color: var(--vscode-focusBorder, #007fd4);
    color: var(--vscode-focusBorder, #007fd4);
  }

  /* Connecting banner */
  #connecting-banner {
    display: none;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    background: var(--vscode-editor-inactiveSelectionBackground, rgba(255,255,255,0.05));
    border-bottom: 1px solid var(--vscode-panel-border, rgba(255,255,255,0.08));
    font-size: 12px;
    color: var(--vscode-descriptionForeground);
    flex-shrink: 0;
  }
  #connecting-banner.visible { display: flex; }
  #connecting-banner.error {
    background: rgba(244,135,113,0.08);
    border-color: rgba(244,135,113,0.2);
    color: var(--vscode-errorForeground, #f48771);
  }

  /* Tab panels */
  .tab-panel { display: none; flex: 1; flex-direction: column; overflow: hidden; }
  .tab-panel.active { display: flex; }

  /* Messages */
  #messages {
    flex: 1;
    overflow-y: auto;
    padding: 12px 10px;
    display: flex;
    flex-direction: column;
    gap: 14px;
    scroll-behavior: smooth;
  }
  #empty-state {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 10px;
    opacity: 0.45;
    padding: 24px;
    text-align: center;
    pointer-events: none;
  }
  #empty-state .es-icon  { font-size: 36px; }
  #empty-state .es-title { font-size: 14px; font-weight: 600; }
  #empty-state .es-hint  { font-size: 12px; line-height: 1.6; }

  .message { display: flex; flex-direction: column; gap: 4px; }
  .msg-label {
    font-size: 10px; font-weight: 700;
    letter-spacing: 0.6px; text-transform: uppercase; opacity: 0.5;
  }
  .msg-body {
    padding: 9px 11px; border-radius: 6px;
    line-height: 1.55; white-space: pre-wrap; overflow-wrap: break-word;
  }
  .message.user .msg-body {
    background: var(--vscode-input-background);
    border: 1px solid var(--vscode-input-border, rgba(255,255,255,0.08));
  }
  .message.assistant .msg-body {
    background: var(--vscode-editor-inactiveSelectionBackground, rgba(255,255,255,0.04));
    border: 1px solid rgba(255,255,255,0.06);
    font-family: var(--vscode-editor-font-family, 'Menlo','Consolas',monospace);
    font-size: 12px;
  }

  /* Status banner */
  #status-banner {
    display: none;
    margin: 0 10px 6px;
    padding: 8px 12px;
    border-radius: 6px;
    background: var(--vscode-editor-inactiveSelectionBackground, rgba(255,255,255,0.05));
    border: 1px solid var(--vscode-focusBorder, rgba(0,127,212,0.35));
    font-size: 12px;
    color: var(--vscode-descriptionForeground);
    align-items: center;
    gap: 8px;
    min-height: 34px;
  }
  #status-banner.visible { display: flex; }
  .status-spinner {
    width: 14px; height: 14px; flex-shrink: 0;
    border: 2px solid var(--vscode-focusBorder, #007fd4);
    border-top-color: transparent;
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  #status-text { flex: 1; font-style: italic; opacity: 0.85; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

  /* Action buttons */
  .msg-actions { display: flex; align-items: center; gap: 5px; margin-top: 2px; }
  .action-btn {
    background: none;
    border: 1px solid var(--vscode-button-border, rgba(255,255,255,0.15));
    color: var(--vscode-descriptionForeground);
    border-radius: 4px; cursor: pointer; font-size: 12px;
    padding: 2px 8px; transition: background 0.1s, color 0.1s;
    line-height: 1.8; display: flex; align-items: center;
  }
  .action-btn:hover { background: var(--vscode-button-secondaryBackground, rgba(255,255,255,0.08)); color: var(--vscode-foreground); }
  .action-btn.active { background: var(--vscode-button-background); color: var(--vscode-button-foreground); border-color: transparent; }
  .action-btn.copied { color: var(--vscode-terminal-ansiGreen, #4ec9b0); }
  .spacer { flex: 1; }

  .error-msg {
    font-size: 12px;
    color: var(--vscode-errorForeground, #f48771);
    background: rgba(244,135,113,0.08);
    border: 1px solid rgba(244,135,113,0.2);
    border-radius: 6px; padding: 8px 10px;
  }

  /* Input area */
  #input-area {
    padding: 8px 10px 10px;
    border-top: 1px solid var(--vscode-panel-border, rgba(255,255,255,0.08));
    display: flex; flex-direction: column; gap: 6px;
    background: var(--vscode-sideBar-background, var(--vscode-editor-background));
  }
  #prompt-input {
    width: 100%;
    background: var(--vscode-input-background);
    color: var(--vscode-input-foreground);
    border: 1px solid var(--vscode-input-border, rgba(255,255,255,0.12));
    border-radius: 5px; padding: 8px 10px;
    font-family: var(--vscode-font-family);
    font-size: var(--vscode-font-size);
    resize: none; min-height: 68px; max-height: 180px;
    outline: none; line-height: 1.5; transition: border-color 0.15s;
  }
  #prompt-input:focus { border-color: var(--vscode-focusBorder, #007fd4); }
  #prompt-input::placeholder { opacity: 0.45; }
  #input-footer { display: flex; align-items: center; justify-content: space-between; }
  .hint-text { font-size: 11px; opacity: 0.35; }
  #send-btn {
    background: var(--vscode-button-background);
    color: var(--vscode-button-foreground);
    border: none; padding: 5px 14px; border-radius: 4px;
    cursor: pointer; font-size: 13px; font-weight: 500;
    transition: background 0.1s, opacity 0.1s;
  }
  #send-btn:hover:not(:disabled) { background: var(--vscode-button-hoverBackground); }
  #send-btn:disabled { opacity: 0.45; cursor: not-allowed; }

  /* Settings panel */
  #settings-panel {
    padding: 16px 12px;
    display: flex; flex-direction: column; gap: 16px; overflow-y: auto;
  }
  .setting-group { display: flex; flex-direction: column; gap: 6px; }
  .setting-label {
    font-size: 11px; font-weight: 700;
    letter-spacing: 0.5px; text-transform: uppercase; opacity: 0.6;
  }
  .setting-description { font-size: 11px; opacity: 0.5; line-height: 1.5; }
  .setting-input {
    width: 100%;
    background: var(--vscode-input-background);
    color: var(--vscode-input-foreground);
    border: 1px solid var(--vscode-input-border, rgba(255,255,255,0.12));
    border-radius: 5px; padding: 7px 10px;
    font-family: var(--vscode-font-family);
    font-size: var(--vscode-font-size);
    outline: none; transition: border-color 0.15s;
  }
  .setting-input:focus { border-color: var(--vscode-focusBorder, #007fd4); }
  .setting-input::placeholder { opacity: 0.35; }
  .setting-saved { font-size: 11px; color: var(--vscode-terminal-ansiGreen, #4ec9b0); opacity: 0; transition: opacity 0.3s; }
  .setting-saved.show { opacity: 1; }
  .settings-divider { border: none; border-top: 1px solid var(--vscode-panel-border, rgba(255,255,255,0.08)); }
</style>
</head>
<body>

<div id="tab-bar">
  <button class="tab-btn active" data-tab="chat">Chat</button>
  <button class="tab-btn" data-tab="settings">Settings</button>
</div>

<div id="connecting-banner">
  <div class="status-spinner" id="conn-spinner"></div>
  <span id="conn-text">Starting backend…</span>
</div>

<!-- Chat tab -->
<div class="tab-panel active" id="panel-chat">
  <div id="messages">
    <div id="empty-state">
      <div class="es-icon">🧪</div>
      <div class="es-title">SpyDR Agent</div>
      <div class="es-hint">Describe a test scenario and the agent will generate a BDD .feature file for you.</div>
    </div>
  </div>

  <div id="status-banner">
    <div class="status-spinner"></div>
    <div id="status-text">Thinking…</div>
  </div>

  <div id="input-area">
    <textarea id="prompt-input" placeholder="Describe the test scenario… (Enter to send, Shift+Enter for new line)" rows="3"></textarea>
    <div id="input-footer">
      <span class="hint-text">Enter ↵ send · Shift+Enter new line</span>
      <button id="send-btn" disabled>Send ↵</button>
    </div>
  </div>
</div>

<!-- Settings tab -->
<div class="tab-panel" id="panel-settings">
  <div id="settings-panel">

    <div class="setting-group">
      <div class="setting-label">OpenAI API Key</div>
      <input class="setting-input" id="s-apikey" type="password" placeholder="sk-..." autocomplete="off" spellcheck="false" />
      <span class="setting-saved" id="saved-apikey">Saved</span>
    </div>

    <hr class="settings-divider" />

    <div class="setting-group">
      <div class="setting-label">Connection String</div>
      <div class="setting-description">PostgreSQL connection string for RAG / pgvector.</div>
      <input class="setting-input" id="s-conn" type="password" placeholder="postgresql://user:pass@host/db" autocomplete="off" spellcheck="false" />
      <span class="setting-saved" id="saved-conn">Saved</span>
    </div>

    <hr class="settings-divider" />

    <div class="setting-group">
      <div class="setting-label">LLM Model</div>
      <input class="setting-input" id="s-model" type="text" placeholder="gpt-4.1-mini" autocomplete="off" spellcheck="false" />
      <span class="setting-saved" id="saved-model">Saved</span>
    </div>

    <hr class="settings-divider" />

    <div class="setting-group">
      <div class="setting-label">Output File</div>
      <div class="setting-description">Path to the generated .feature file. Relative paths resolve from workspace root.</div>
      <input class="setting-input" id="s-feature" type="text" placeholder="tests/generated.feature" autocomplete="off" spellcheck="false" />
      <span class="setting-saved" id="saved-feature">Saved</span>
    </div>

    <hr class="settings-divider" />

    <div class="setting-group">
      <div class="setting-label">Project ID</div>
      <div class="setting-description">Project identifier (optional, reserved for future use).</div>
      <input class="setting-input" id="s-project" type="text" placeholder="my-project" autocomplete="off" spellcheck="false" />
      <span class="setting-saved" id="saved-project">Saved</span>
    </div>

  </div>
</div>

<script nonce="${n}">
(function () {
  const vscode = acquireVsCodeApi();

  // Tab switching
  document.querySelectorAll('.tab-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      const tab = btn.getAttribute('data-tab');
      document.querySelectorAll('.tab-btn').forEach(function (b) { b.classList.remove('active'); });
      document.querySelectorAll('.tab-panel').forEach(function (p) { p.classList.remove('active'); });
      btn.classList.add('active');
      document.getElementById('panel-' + tab).classList.add('active');
    });
  });

  // Chat refs
  const messagesEl    = document.getElementById('messages');
  const emptyStateEl  = document.getElementById('empty-state');
  const inputEl       = document.getElementById('prompt-input');
  const sendBtn       = document.getElementById('send-btn');
  const statusBanner  = document.getElementById('status-banner');
  const statusText    = document.getElementById('status-text');
  const connBanner    = document.getElementById('connecting-banner');
  const connText      = document.getElementById('conn-text');
  const connSpinner   = document.getElementById('conn-spinner');

  let isStreaming    = false;
  let backendReady   = false;
  let currentMsgEl   = null;
  let currentBodyEl  = null;
  let currentContent = '';

  function setBackendReady(ready) {
    backendReady = ready;
    sendBtn.disabled = !ready || isStreaming;
    if (ready) {
      connBanner.classList.remove('visible', 'error');
    }
  }

  function showConnecting(text, isError) {
    connText.textContent = text;
    connBanner.classList.toggle('error', !!isError);
    connSpinner.style.display = isError ? 'none' : '';
    connBanner.classList.add('visible');
  }

  // Settings refs
  const fields = {
    apikey:  document.getElementById('s-apikey'),
    conn:    document.getElementById('s-conn'),
    model:   document.getElementById('s-model'),
    feature: document.getElementById('s-feature'),
    project: document.getElementById('s-project'),
  };
  const saved = {
    apikey:  document.getElementById('saved-apikey'),
    conn:    document.getElementById('saved-conn'),
    model:   document.getElementById('saved-model'),
    feature: document.getElementById('saved-feature'),
    project: document.getElementById('saved-project'),
  };

  function flashSaved(el) {
    el.classList.add('show');
    setTimeout(function () { el.classList.remove('show'); }, 1800);
  }

  function makeSaveHandler(savedEl) {
    let timer = null;
    return function () {
      clearTimeout(timer);
      timer = setTimeout(function () {
        vscode.postMessage({
          type: 'saveSettings',
          openaiApiKey: fields.apikey.value,
          connectionString: fields.conn.value,
          llmModel: fields.model.value,
          featureFilePath: fields.feature.value,
          projectId: fields.project.value,
        });
        flashSaved(savedEl);
      }, 600);
    };
  }

  fields.apikey.addEventListener('input',  makeSaveHandler(saved.apikey));
  fields.conn.addEventListener('input',    makeSaveHandler(saved.conn));
  fields.model.addEventListener('input',   makeSaveHandler(saved.model));
  fields.feature.addEventListener('input', makeSaveHandler(saved.feature));
  fields.project.addEventListener('input', makeSaveHandler(saved.project));

  // Chat helpers
  function escHtml(s) {
    return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }
  function scrollBottom() { messagesEl.scrollTop = messagesEl.scrollHeight; }

  function setStreaming(val) {
    isStreaming = val;
    sendBtn.disabled = val || !backendReady;
    sendBtn.textContent = val ? 'Generating…' : 'Send ↵';
    if (!val) { hideBanner(); }
  }

  function showBanner(text) {
    statusText.textContent = text || 'Thinking…';
    statusBanner.classList.add('visible');
  }
  function hideBanner() {
    statusBanner.classList.remove('visible');
    statusText.textContent = 'Thinking…';
  }

  function hideEmpty() {
    if (emptyStateEl) { emptyStateEl.style.display = 'none'; }
  }

  function adjustHeight() {
    inputEl.style.height = 'auto';
    inputEl.style.height = Math.min(inputEl.scrollHeight, 180) + 'px';
  }

  function appendUserMsg(text) {
    hideEmpty();
    const el = document.createElement('div');
    el.className = 'message user';
    el.innerHTML = '<div class="msg-label">You</div><div class="msg-body">' + escHtml(text) + '</div>';
    messagesEl.appendChild(el);
    scrollBottom();
  }

  function beginAssistantMsg() {
    hideEmpty();
    const el = document.createElement('div');
    el.className = 'message assistant';
    el.innerHTML = '<div class="msg-label">Agent</div>';
    const body = document.createElement('div');
    body.className = 'msg-body';
    body.style.display = 'none';
    el.appendChild(body);
    messagesEl.appendChild(el);
    currentMsgEl  = el;
    currentBodyEl = body;
    scrollBottom();
  }

  function setFinalText(text) {
    if (!currentBodyEl || !text) { return; }
    currentBodyEl.textContent = text;
    currentBodyEl.style.display = '';
    scrollBottom();
  }

  function finishAssistantMsg(content) {
    const ICON_COPY  = '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/></svg>';
    const ICON_CHECK = '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>';
    const actions = document.createElement('div');
    actions.className = 'msg-actions';
    const copyBtn = document.createElement('button');
    copyBtn.className = 'action-btn';
    copyBtn.title = 'Copy';
    copyBtn.innerHTML = ICON_COPY;
    copyBtn.addEventListener('click', function () {
      navigator.clipboard.writeText(content).then(function () {
        copyBtn.innerHTML = ICON_CHECK;
        copyBtn.classList.add('copied');
        setTimeout(function () { copyBtn.innerHTML = ICON_COPY; copyBtn.classList.remove('copied'); }, 1500);
      });
    });
    actions.appendChild(copyBtn);
    currentMsgEl.appendChild(actions);
  }

  function appendError(message) {
    const el = document.createElement('div');
    el.className = 'error-msg';
    el.textContent = 'Error: ' + message;
    messagesEl.appendChild(el);
    scrollBottom();
  }

  // Send
  function sendMessage() {
    const prompt = inputEl.value.trim();
    if (!prompt || isStreaming || !backendReady) { return; }
    appendUserMsg(prompt);
    inputEl.value = '';
    adjustHeight();
    currentContent = '';
    beginAssistantMsg();
    showBanner('Thinking…');
    setStreaming(true);
    vscode.postMessage({ type: 'sendPrompt', prompt });
  }

  sendBtn.addEventListener('click', sendMessage);
  inputEl.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  });
  inputEl.addEventListener('input', adjustHeight);

  // Extension → WebView messages
  window.addEventListener('message', function (event) {
    const msg = event.data;
    switch (msg.type) {
      case 'initSettings':
        fields.apikey.value  = msg.openaiApiKey || '';
        fields.conn.value    = msg.connectionString || '';
        fields.model.value   = msg.llmModel || '';
        fields.feature.value = msg.featureFilePath || '';
        fields.project.value = msg.projectId || '';
        break;

      case 'backendReady':
        setBackendReady(true);
        break;

      case 'backendDead':
        setBackendReady(false);
        showConnecting('Backend stopped. Restart via command palette.', true);
        break;

      case 'chunk':
        currentContent += msg.text;
        break;

      case 'status':
        showBanner(msg.text);
        break;

      case 'fileSaved':
        showBanner('Saved → ' + msg.filePath.split(/[\\\\/]/).pop());
        break;

      case 'done':
        setFinalText(currentContent);
        if (currentContent) { finishAssistantMsg(currentContent); }
        setStreaming(false);
        break;

      case 'error':
        if (isStreaming) { setStreaming(false); }
        appendError(msg.message);
        break;

      case 'sessionReset':
        break;
    }
  });

  // Init
  showConnecting('Starting backend…', false);
  vscode.postMessage({ type: 'ready' });
})();
</script>
</body>
</html>`;
    }
}
exports.SidebarProvider = SidebarProvider;
//# sourceMappingURL=sidebarProvider.js.map