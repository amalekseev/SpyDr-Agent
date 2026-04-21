import * as fs from 'fs';
import * as path from 'path';
import * as vscode from 'vscode';

export function writeConfigs(backendDir: string): void {
    const cfg = vscode.workspace.getConfiguration('spydr');
    const model = cfg.get<string>('llmModel', 'gpt-4.1-mini');

    writeAgentConfig(path.join(backendDir, 'src', 'agents', 'config.yml'), model);
    writeGlobalConfig(path.join(backendDir, 'src', 'configs', 'config.yml'));
}

function writeAgentConfig(filePath: string, model: string): void {
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

function writeGlobalConfig(filePath: string): void {
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

function mkdirForFile(filePath: string): void {
    fs.mkdirSync(path.dirname(filePath), { recursive: true });
}
