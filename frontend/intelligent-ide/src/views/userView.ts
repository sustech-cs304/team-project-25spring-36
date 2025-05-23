import * as vscode from 'vscode';
import { LoginInfo } from '../models/LoginInfo';

// Module-level variable to store the status bar item for the user view
let statusBarItem: vscode.StatusBarItem | undefined;

/**
 * Initializes and registers the user view components (e.g., status bar).
 * This should be called once during extension activation.
 * @param context vscode.ExtensionContext
 */
export function registerUserView(context: vscode.ExtensionContext): void {
    // Initial update of the login view (which creates the status bar item if needed)
    updateLoginView(context);
}

/**
 * Updates login-related UI components, primarily the status bar item.
 * @param context vscode.ExtensionContext
 */
export function updateLoginView(context: vscode.ExtensionContext): void {
    const loginInfo: LoginInfo | undefined = context.globalState.get('loginInfo');

    // Update context variables for when clauses first
    updateLoginContext(context);

    if (loginInfo) {
        try {
            if (!statusBarItem) {
                // Create status bar item if it doesn't exist
                statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
                context.subscriptions.push(statusBarItem); // Add to subscriptions for proper disposal
            }
            statusBarItem.text = `$(account) ${loginInfo.username} (${loginInfo.role})`;
            statusBarItem.tooltip = "Logged in user info";
            statusBarItem.command = 'intelligent-ide.switchRole'; // Or your relevant command
            statusBarItem.show();
        } catch (error) {
            console.error("Error updating status bar:", error);
            vscode.window.showErrorMessage("Failed to update status bar.");
        }
    } else {
        // If not logged in, hide and dispose of the status bar item
        if (statusBarItem) {
            statusBarItem.hide();
            // We don't dispose it here, as it's managed by context.subscriptions
            // Or, if you prefer to recreate it each time:
            // statusBarItem.dispose();
            // statusBarItem = undefined;
        }
    }
}

/**
 * Update context for when clauses in package.json based on login state.
 * @param context vscode.ExtensionContext
 */
export function updateLoginContext(context: vscode.ExtensionContext): void {
    const loginInfo: LoginInfo | undefined = context.globalState.get('loginInfo');

    vscode.commands.executeCommand('setContext', 'intelligent-ide.loggedIn', !!loginInfo);
    if (loginInfo) {
        vscode.commands.executeCommand('setContext', 'intelligent-ide.userRole', loginInfo.role);
    } else {
        // Explicitly set to undefined or a default role if not logged in
        vscode.commands.executeCommand('setContext', 'intelligent-ide.userRole', undefined);
    }
}

/**
 * Disposes of resources used by the user view, like the status bar item.
 * This should be called when the extension deactivates.
 */
export function disposeUserView(): void {
    if (statusBarItem) {
        statusBarItem.dispose();
        statusBarItem = undefined;
    }
}