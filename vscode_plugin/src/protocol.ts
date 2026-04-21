export interface ChatConfig {
    project_id: string;
    feature_file_path: string;
    validation_enabled: boolean;
    max_validation_iterations: number;
}

export interface IncomingMessage {
    type: string;
    content?: string;
    path?: string;
    projects?: string[];
    thread_id?: string;
}

export function buildChatMessage(message: string, config: ChatConfig): object {
    return { type: 'chat', message, config };
}

export function buildResetMessage(): object {
    return { type: 'reset' };
}

export function parseMessage(line: string): IncomingMessage | null {
    try {
        return JSON.parse(line) as IncomingMessage;
    } catch {
        return null;
    }
}
