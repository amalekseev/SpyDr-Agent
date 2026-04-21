"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.buildChatMessage = buildChatMessage;
exports.buildResetMessage = buildResetMessage;
exports.parseMessage = parseMessage;
function buildChatMessage(message, config) {
    return { type: 'chat', message, config };
}
function buildResetMessage() {
    return { type: 'reset' };
}
function parseMessage(line) {
    try {
        return JSON.parse(line);
    }
    catch {
        return null;
    }
}
//# sourceMappingURL=protocol.js.map