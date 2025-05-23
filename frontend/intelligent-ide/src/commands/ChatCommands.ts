import * as vscode from 'vscode';
import { ViewType, refreshViews, getChatViewPanel } from '../views/viewManager';
import * as ai from '../services/AIService';
import { getAuthDetails } from '../utils/authUtils';

/**
 * Register all chat-related commands
 */
export function registerChatCommands(context: vscode.ExtensionContext): void {
    registerOpenChatCommand(context);
    registerClearConversationCommand(context);
}

/**
 * Register command to open the chat panel
 */
function registerOpenChatCommand(context: vscode.ExtensionContext): void {
    const disposable = vscode.commands.registerCommand('intelligent-ide.chat.open', async () => {
        try {
            const authDetails = await getAuthDetails(context);
            if (!authDetails) {
                return []; // Auth failed, return empty
            }
            const { token, loginInfo } = authDetails;
            
            // Refresh the CHAT view type which will create the panel if it doesn't exist
            // or bring it to focus if it already exists
            await refreshViews([ViewType.CHAT]);

            vscode.window.showInformationMessage(`Chat assistant ready to help you!`);

        } catch (error: any) {
            vscode.window.showErrorMessage(`Failed to open chat: ${error.message}`);
        }
    });

    context.subscriptions.push(disposable);
}

/**
 * Register command to clear the chat conversation history
 */
function registerClearConversationCommand(context: vscode.ExtensionContext): void {
    const disposable = vscode.commands.registerCommand('intelligent-ide.chat.clear',async () => {
        try {
            const authDetails = await getAuthDetails(context);
            if (!authDetails) {
                return []; // Auth failed, return empty
            }
            const { token, loginInfo } = authDetails;
            
            // Clear the conversation history in the AI service
            ai.clearConversation();

            // Find any open chat view and clear its UI
            const panel = getChatViewPanel();
            if (panel) {
                panel.webview.postMessage({ command: 'clear' });
            }

            vscode.window.showInformationMessage(`AI conversation history cleared`);

        } catch (error: any) {
            vscode.window.showErrorMessage(`Failed to clear conversation: ${error.message}`);
        }
    });

    context.subscriptions.push(disposable);
}