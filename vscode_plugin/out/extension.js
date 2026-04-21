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
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
const configWriter_js_1 = require("./configWriter.js");
const pythonManager_js_1 = require("./pythonManager.js");
const sidebarProvider_js_1 = require("./sidebarProvider.js");
function activate(context) {
    const channel = vscode.window.createOutputChannel('SpyDR Agent');
    const manager = new pythonManager_js_1.PythonManager();
    const provider = new sidebarProvider_js_1.SidebarProvider(context.extensionUri, manager);
    context.subscriptions.push(vscode.window.registerWebviewViewProvider('spydr.sidebar', provider, {
        webviewOptions: { retainContextWhenHidden: true },
    }));
    context.subscriptions.push(vscode.commands.registerCommand('spydr.restart', () => {
        manager.stop();
        startBackend(manager, channel);
    }));
    startBackend(manager, channel);
}
function startBackend(manager, channel) {
    manager.setup(channel)
        .then(() => {
        (0, configWriter_js_1.writeConfigs)(pythonManager_js_1.BACKEND_DIR);
        manager.startProcess(channel);
    })
        .catch((err) => {
        channel.appendLine(`[SpyDR] Setup failed: ${err.message}`);
        channel.show(true);
        vscode.window.showErrorMessage(`SpyDR: Backend setup failed — ${err.message}`, 'Show Output').then((choice) => {
            if (choice === 'Show Output') {
                channel.show();
            }
        });
    });
}
function deactivate() { }
//# sourceMappingURL=extension.js.map