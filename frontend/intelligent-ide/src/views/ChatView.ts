import * as vscode from 'vscode';
import * as path from 'path';
import * as ai from '../services/AIService';

/**
 * Process user message and get streaming AI response
 */
export async function handleUserMessage(panel: vscode.WebviewPanel, text: string, context: vscode.ExtensionContext): Promise<void> {
    try {
        // First, send a message to create a placeholder for the AI response
        panel.webview.postMessage({
            command: 'aiResponseStart'
        });

        // Get AI response with streaming
        await ai.getChatResponseStream(
            text,
            context,
            (chunk: string) => {
                // Send each chunk to the webview
                panel.webview.postMessage({
                    command: 'aiResponseChunk',
                    text: chunk
                });
            }
        );

        // Signal that the response is complete
        panel.webview.postMessage({
            command: 'aiResponseComplete'
        });

    } catch (error: any) {
        panel.webview.postMessage({
            command: 'error',
            text: `Error: ${error.message}`
        });
    }
}

/**
 * Handle code attachment from current editor
 */
export async function handleCodeAttachment(panel: vscode.WebviewPanel): Promise<void> {
    const editor = vscode.window.activeTextEditor;

    if (!editor) {
        panel.webview.postMessage({
            command: 'error',
            text: 'No active editor'
        });
        return;
    }

    const document = editor.document;
    const selection = editor.selection;

    // Get selected text or entire document
    const text = selection.isEmpty
        ? document.getText()
        : document.getText(selection);

    // Send the attachment to webview
    panel.webview.postMessage({
        command: 'codeAttachment',
        filename: document.fileName,
        text: text
    });
}


/**
 * Generate a nonce for script security
 */
export function getNonce(): string {
    let text = '';
    const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    for (let i = 0; i < 32; i++) {
        text += possible.charAt(Math.floor(Math.random() * possible.length));
    }
    return text;
}

/**
 * Get AI response for user message
 */
async function getAIResponse(text: string, context: vscode.ExtensionContext): Promise<string> {
    try {
        // Use the AIService to get a response
        return await ai.getChatResponse(text, context);
    } catch (error: any) {
        console.error('Error getting AI response:', error);
        throw error;
    }
}