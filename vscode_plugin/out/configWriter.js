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
exports.writeConfigs = writeConfigs;
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const vscode = __importStar(require("vscode"));
function writeConfigs(backendDir) {
    const cfg = vscode.workspace.getConfiguration('spydr');
    const model = cfg.get('llmModel', 'gpt-4.1-mini');
    writeAgentConfig(path.join(backendDir, 'src', 'agents', 'config.yml'), model);
    writeGlobalConfig(path.join(backendDir, 'src', 'configs', 'config.yml'));
}
function writeAgentConfig(filePath, model) {
    const yaml = [
        'llm_params:',
        `  provider: openai`,
        `  model: ${model}`,
        '  temperature: 0',
        '',
        'validation:',
        '  max_iterations: 3',
        '  llm_params:',
        `    provider: openai`,
        `    model: ${model}`,
        '    temperature: 0',
        '',
    ].join('\n');
    mkdirForFile(filePath);
    fs.writeFileSync(filePath, yaml, 'utf8');
}
function writeGlobalConfig(filePath) {
    const yaml = [
        'rag:',
        '  provider: openai',
        '  params:',
        '    model: text-embedding-3-large',
        '',
        '  steps:',
        '    collection_name: bdd_steps',
        '    top_k: 8',
        '',
        '  docs:',
        '    collection_name: project_docs',
        '    path: docs',
        '    top_k: 5',
        '    chunk_size: 1000',
        '    chunk_overlap: 200',
        '',
        '  few_shots:',
        '    collection_name: few_shots',
        '    top_k: 3',
        '    index_path: src/configs/few_shots_index.json',
        '    few_shots_dir: few_shots',
        '    batch_size: 100',
        '',
        'docstring:',
        '  supported_langs:',
        '    - python',
        '    - json',
        '    - xml',
        '    - sql',
        '',
    ].join('\n');
    mkdirForFile(filePath);
    fs.writeFileSync(filePath, yaml, 'utf8');
}
function mkdirForFile(filePath) {
    fs.mkdirSync(path.dirname(filePath), { recursive: true });
}
//# sourceMappingURL=configWriter.js.map