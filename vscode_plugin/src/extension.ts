import * as vscode from 'vscode';
import { writeConfigs } from './configWriter.js';
import { BACKEND_DIR, PythonManager } from './pythonManager.js';
import { SidebarProvider } from './sidebarProvider.js';

export function activate(context: vscode.ExtensionContext): void {
    const channel = vscode.window.createOutputChannel('SpyDR Agent');
    const manager = new PythonManager();
    const provider = new SidebarProvider(context.extensionUri, manager);

    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider('spydr.sidebar', provider, {
            webviewOptions: { retainContextWhenHidden: true },
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('spydr.restart', () => {
            manager.stop();
            startBackend(manager, channel);
        })
    );

    startBackend(manager, channel);
}

function startBackend(manager: PythonManager, channel: vscode.OutputChannel): void {
    manager.setup(channel)
        .then(() => {
            writeConfigs(BACKEND_DIR);
            manager.startProcess(channel);
        })
        .catch((err: Error) => {
            channel.appendLine(`[SpyDR] Setup failed: ${err.message}`);
            channel.show(true);
            vscode.window.showErrorMessage(
                `SpyDR: Backend setup failed — ${err.message}`,
                'Show Output'
            ).then((choice) => {
                if (choice === 'Show Output') { channel.show(); }
            });
        });
}

export function deactivate(): void { /* nothing */ }
