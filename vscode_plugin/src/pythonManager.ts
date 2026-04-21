import * as cp from 'child_process';
import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';
import * as readline from 'readline';
import { EventEmitter } from 'events';
import * as vscode from 'vscode';
import { IncomingMessage, parseMessage } from './protocol.js';

const REPO_URL = 'https://github.com/D1105/glowing-funicular';

export const BASE_DIR = path.join(os.homedir(), '.spydr');
export const BACKEND_DIR = path.join(BASE_DIR, 'backend');
const VENV_DIR = path.join(BACKEND_DIR, '.venv');
const CLONE_MARKER = path.join(BACKEND_DIR, '.cloned');

function venvPython(): string {
    if (process.platform === 'win32') {
        return path.join(VENV_DIR, 'Scripts', 'python.exe');
    }
    const py3 = path.join(VENV_DIR, 'bin', 'python3');
    return fs.existsSync(py3) ? py3 : path.join(VENV_DIR, 'bin', 'python');
}

function venvPip(): string {
    if (process.platform === 'win32') {
        return path.join(VENV_DIR, 'Scripts', 'pip.exe');
    }
    return path.join(VENV_DIR, 'bin', 'pip');
}

export declare interface PythonManager {
    on(event: 'message', listener: (msg: IncomingMessage) => void): this;
    on(event: 'died', listener: (code: number | null) => void): this;
}

export class PythonManager extends EventEmitter {
    private proc: cp.ChildProcess | null = null;

    async setup(channel: vscode.OutputChannel): Promise<void> {
        fs.mkdirSync(BASE_DIR, { recursive: true });

        // Step 1: Clone repo (once)
        if (!fs.existsSync(CLONE_MARKER)) {
            channel.appendLine(`[SpyDR] Cloning repository...`);
            if (fs.existsSync(BACKEND_DIR)) {
                fs.rmSync(BACKEND_DIR, { recursive: true, force: true });
            }
            this.exec(['git', 'clone', REPO_URL, BACKEND_DIR], BASE_DIR, channel, 120);
            fs.writeFileSync(CLONE_MARKER, '', 'utf8');
            channel.appendLine('[SpyDR] Repository cloned.');
        } else {
            channel.appendLine('[SpyDR] Repository already present.');
        }

        // Step 2: Create venv (if missing)
        if (!fs.existsSync(venvPython())) {
            channel.appendLine('[SpyDR] Creating virtual environment...');
            const sysPython = this.findSystemPython();
            if (!sysPython) {
                throw new Error(
                    'Python 3 not found. Install Python 3.10+ and ensure it is in PATH.\n' +
                    (process.platform === 'darwin'
                        ? 'Run: brew install python3'
                        : 'See https://www.python.org/downloads/')
                );
            }
            this.exec([sysPython, '-m', 'venv', VENV_DIR], BACKEND_DIR, channel, 120);
            channel.appendLine('[SpyDR] Virtual environment created.');
        } else {
            channel.appendLine('[SpyDR] Virtual environment already exists.');
        }

        // Step 3: Install deps (smoke-test import langchain)
        const check = cp.spawnSync(
            venvPython(),
            ['-c', 'import langchain; print("ok")'],
            { cwd: BACKEND_DIR, timeout: 15_000, encoding: 'utf8' }
        );
        if (check.status !== 0 || !check.stdout.includes('ok')) {
            channel.appendLine('[SpyDR] Installing dependencies (this may take a few minutes)...');
            this.exec([venvPip(), 'install', '-r', 'requirements.txt', '--quiet'], BACKEND_DIR, channel, 600);
            channel.appendLine('[SpyDR] Dependencies installed.');
        } else {
            channel.appendLine('[SpyDR] Dependencies already installed.');
        }

        channel.appendLine('[SpyDR] Setup complete.');
    }

    startProcess(channel: vscode.OutputChannel): void {
        const cfg = vscode.workspace.getConfiguration('spydr');
        const env: NodeJS.ProcessEnv = {
            ...process.env,
            OPENAI_API_KEY: cfg.get<string>('openaiApiKey', ''),
            CONNECTION_STRING: cfg.get<string>('connectionString', ''),
        };

        this.proc = cp.spawn(venvPython(), ['-m', 'src.api.stdio_server'], {
            cwd: BACKEND_DIR,
            env,
            stdio: ['pipe', 'pipe', 'pipe'],
        });

        const rl = readline.createInterface({ input: this.proc.stdout! });
        rl.on('line', (line) => {
            line = line.trim();
            if (!line) { return; }
            const msg = parseMessage(line);
            if (msg) {
                this.emit('message', msg);
            } else {
                channel.appendLine(`[stdout] ${line}`);
            }
        });

        const errRl = readline.createInterface({ input: this.proc.stderr! });
        errRl.on('line', (line) => channel.appendLine(`[stderr] ${line}`));

        this.proc.on('exit', (code) => {
            channel.appendLine(`[SpyDR] Process exited with code ${code}`);
            this.emit('died', code);
        });
    }

    sendLine(obj: object): void {
        if (!this.proc?.stdin?.writable) { return; }
        this.proc.stdin.write(JSON.stringify(obj) + '\n');
    }

    stop(): void {
        this.proc?.kill();
        this.proc = null;
    }

    isRunning(): boolean {
        return this.proc !== null && !this.proc.killed;
    }

    private findSystemPython(): string | null {
        const candidates = process.platform === 'win32'
            ? ['python', 'python3', 'py']
            : ['python3', 'python'];
        const absPaths = process.platform === 'win32'
            ? []
            : ['/usr/local/bin/python3', '/usr/bin/python3', '/opt/homebrew/bin/python3'];

        for (const cmd of [...candidates, ...absPaths]) {
            if (absPaths.includes(cmd) && !fs.existsSync(cmd)) { continue; }
            try {
                const r = cp.spawnSync(cmd, ['--version'], { timeout: 5000, encoding: 'utf8' });
                if (r.status === 0 && (r.stdout + r.stderr).includes('Python 3')) { return cmd; }
            } catch { /* skip */ }
        }
        return null;
    }

    private exec(
        cmd: string[],
        cwd: string,
        channel: vscode.OutputChannel,
        timeoutSec: number,
    ): void {
        fs.mkdirSync(cwd, { recursive: true });
        const r = cp.spawnSync(cmd[0], cmd.slice(1), {
            cwd,
            timeout: timeoutSec * 1000,
            encoding: 'utf8',
        });
        if (r.stdout) { channel.appendLine(r.stdout.trimEnd()); }
        if (r.stderr) { channel.appendLine(r.stderr.trimEnd()); }
        if (r.status !== 0) {
            throw new Error(
                `Command failed (exit ${r.status}): ${cmd.join(' ')}\n${r.stderr ?? ''}`
            );
        }
    }
}
