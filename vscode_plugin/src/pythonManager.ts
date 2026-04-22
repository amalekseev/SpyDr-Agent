import * as cp from 'child_process';
import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';
import * as readline from 'readline';
import { EventEmitter } from 'events';
import * as vscode from 'vscode';
import { IncomingMessage, parseMessage } from './protocol.js';

const REPO_URL = 'https://github.com/amalekseev/SpyDr-Agent';

export const BASE_DIR = path.join(os.homedir(), '.spydr');
export const BACKEND_DIR = path.join(BASE_DIR, 'backend');
const VENV_DIR = path.join(BACKEND_DIR, '.venv');
const CLONE_MARKER = path.join(BACKEND_DIR, '.cloned');

type LogLevel = 'info' | 'warn' | 'error' | 'stderr';

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
    on(event: 'log', listener: (entry: { level: LogLevel; text: string }) => void): this;
}

export class PythonManager extends EventEmitter {
    private proc: cp.ChildProcess | null = null;

    async setup(channel: vscode.OutputChannel): Promise<void> {
        fs.mkdirSync(BASE_DIR, { recursive: true });

        // Step 1: Clone repo (once)
        if (!fs.existsSync(CLONE_MARKER)) {
            this.log(channel, 'info', 'Cloning repository...');
            if (fs.existsSync(BACKEND_DIR)) {
                fs.rmSync(BACKEND_DIR, { recursive: true, force: true });
            }
            this.exec(['git', 'clone', REPO_URL, BACKEND_DIR], BASE_DIR, channel, 120);
            fs.writeFileSync(CLONE_MARKER, '', 'utf8');
            this.log(channel, 'info', 'Repository cloned.');
        } else {
            this.log(channel, 'info', 'Repository already present.');
        }

        // Patch requirements.txt to fix known broken version pins
        this.patchRequirements(BACKEND_DIR);

        // Step 2: Create venv — recreate if Python version is 3.13+
        if (fs.existsSync(venvPython())) {
            const r = cp.spawnSync(venvPython(), ['--version'], { encoding: 'utf8', timeout: 5000 });
            const ver = (r.stdout + r.stderr).trim();
            const m = ver.match(/Python 3\.(\d+)/);
            if (m && Number(m[1]) >= 13) {
                this.log(channel, 'warn', `Venv uses ${ver} (too new, packages lack wheels). Recreating...`);
                fs.rmSync(VENV_DIR, { recursive: true, force: true });
            } else {
                this.log(channel, 'info', `Virtual environment already exists (${ver}).`);
            }
        }

        if (!fs.existsSync(venvPython())) {
            const sysPython = this.findSystemPython();
            if (!sysPython) {
                throw new Error(
                    'Python 3.10–3.12 not found. Install it and ensure it is in PATH.\n' +
                    (process.platform === 'darwin'
                        ? 'Run: brew install python@3.12'
                        : 'See https://www.python.org/downloads/')
                );
            }
            this.log(channel, 'info', `Creating virtual environment with ${sysPython}...`);
            this.exec([sysPython, '-m', 'venv', VENV_DIR], BACKEND_DIR, channel, 120);
            this.log(channel, 'info', 'Virtual environment created.');
        }

        // Step 3: Install deps (smoke-test import langchain + langchain_openai)
        const check = cp.spawnSync(
            venvPython(),
            ['-c', 'import langchain; import langchain_openai; print("ok")'],
            { cwd: BACKEND_DIR, timeout: 15_000, encoding: 'utf8' }
        );
        if (check.status !== 0 || !check.stdout.includes('ok')) {
            this.log(channel, 'info', 'Installing dependencies (this may take several minutes)...');
            await this.pipInstall(BACKEND_DIR, channel);
            this.log(channel, 'info', 'Dependencies installed.');
        } else {
            this.log(channel, 'info', 'Dependencies already installed.');
        }

        this.log(channel, 'info', 'Setup complete.');
    }

    startProcess(channel: vscode.OutputChannel): void {
        const cfg = vscode.workspace.getConfiguration('spydr');
        const env: NodeJS.ProcessEnv = {
            ...process.env,
            OPENAI_API_KEY: cfg.get<string>('openaiApiKey', ''),
            CONNECTION_STRING: cfg.get<string>('connectionString', ''),
        };

        this.log(channel, 'info', 'Starting backend process...');

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
                this.emit('log', { level: 'info', text: line });
            }
        });

        const errRl = readline.createInterface({ input: this.proc.stderr! });
        errRl.on('line', (line) => {
            channel.appendLine(`[stderr] ${line}`);
            this.emit('log', { level: 'stderr', text: line });
        });

        this.proc.on('exit', (code) => {
            const msg = `Process exited with code ${code}`;
            channel.appendLine(`[SpyDR] ${msg}`);
            this.emit('log', { level: code === 0 ? 'info' : 'error', text: `--- ${msg} ---` });
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

    private log(channel: vscode.OutputChannel, level: LogLevel, text: string): void {
        channel.appendLine(`[SpyDR] ${text}`);
        this.emit('log', { level, text });
    }

    private findSystemPython(): string | null {
        const preferred = ['python3.12', 'python3.11', 'python3.10', 'python3', 'python'];
        const absPaths = process.platform === 'win32'
            ? []
            : [
                '/opt/homebrew/bin/python3.12', '/opt/homebrew/bin/python3.11', '/opt/homebrew/bin/python3.10',
                '/usr/local/bin/python3.12',    '/usr/local/bin/python3.11',    '/usr/local/bin/python3.10',
                '/usr/local/bin/python3',       '/usr/bin/python3',
            ];

        for (const cmd of [...preferred, ...absPaths]) {
            if (absPaths.includes(cmd) && !fs.existsSync(cmd)) { continue; }
            try {
                const r = cp.spawnSync(cmd, ['--version'], { timeout: 5000, encoding: 'utf8' });
                const version = (r.stdout + r.stderr).trim();
                if (r.status !== 0 || !version.includes('Python 3')) { continue; }
                const m = version.match(/Python 3\.(\d+)/);
                if (m && Number(m[1]) >= 10 && Number(m[1]) <= 12) { return cmd; }
            } catch { /* skip */ }
        }
        for (const cmd of ['python3', 'python']) {
            try {
                const r = cp.spawnSync(cmd, ['--version'], { timeout: 5000, encoding: 'utf8' });
                if (r.status === 0 && (r.stdout + r.stderr).includes('Python 3')) { return cmd; }
            } catch { /* skip */ }
        }
        return null;
    }

    private pipInstall(backendDir: string, channel: vscode.OutputChannel): Promise<void> {
        return new Promise((resolve, reject) => {
            const proc = cp.spawn(
                venvPip(),
                ['install', '-r', 'requirements.txt', '--timeout', '120'],
                { cwd: backendDir, encoding: 'utf8' } as cp.SpawnOptions
            );

            const rl = readline.createInterface({ input: proc.stdout as NodeJS.ReadableStream });
            rl.on('line', (line) => {
                channel.appendLine(line);
                this.emit('log', { level: 'info', text: line });
            });

            const errRl = readline.createInterface({ input: proc.stderr as NodeJS.ReadableStream });
            errRl.on('line', (line) => {
                channel.appendLine(line);
                this.emit('log', { level: 'info', text: line });
            });

            proc.on('exit', (code) => {
                if (code === 0) {
                    resolve();
                } else {
                    reject(new Error(`pip install failed (exit ${code})`));
                }
            });
            proc.on('error', reject);
        });
    }

    private patchRequirements(backendDir: string): void {
        const reqPath = path.join(backendDir, 'requirements.txt');
        if (!fs.existsSync(reqPath)) { return; }
        let content = fs.readFileSync(reqPath, 'utf8');
        let patched = content
            .replace(/psycopg\[binary\]>=3\.2\.9/g, 'psycopg[binary]>=3.2.10')
            .replace(/psycopg-binary==3\.2\.9/g,    'psycopg-binary>=3.2.10')
            .replace(/langchain==1\.2\.10/g,         'langchain==1.2.15');
        if (!/langchain[_-]openai/i.test(patched)) {
            patched = patched.trimEnd() + '\nlangchain-openai>=0.3.0\n';
        }
        if (patched !== content) {
            fs.writeFileSync(reqPath, patched, 'utf8');
        }
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
