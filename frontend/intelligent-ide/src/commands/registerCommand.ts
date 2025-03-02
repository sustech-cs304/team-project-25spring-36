import * as vscode from 'vscode';
import { authenticationService } from '../services/userService';

export function registerRegisterCommand(context: vscode.ExtensionContext) {
    const disposable = vscode.commands.registerCommand('intelligent-ide.register', async () => {
        const username = await vscode.window.showInputBox({ prompt: 'Enter new username' });
        const password = await vscode.window.showInputBox({ prompt: 'Enter new password', password: true });

        if (!username || !password) {
            vscode.window.showErrorMessage('Username and password are required.');
            return;
        }

        // Use quick pick to select a role:
        const role = await vscode.window.showQuickPick(['student', 'teacher'], {
            placeHolder: 'Select a role'
        });

        if (!role) {
            vscode.window.showErrorMessage('Role selection is required.');
            return;
        }

        // Call your service to register the new user.
        try {
            const token = await authenticationService.register(username, password, role);
            await context.secrets.store("authToken", token);
            const userInfo = await authenticationService.getUserInfo(token);
            vscode.window.showInformationMessage(`Registration successful for ${username} as ${role}!`);

            // Create and show a status bar item with login info.
            const statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
            statusBarItem.text = `$(account) ${userInfo.username} (${userInfo.role})`;
            statusBarItem.tooltip = "Logged in user info";
            statusBarItem.show();

            // Optionally, add statusBarItem to context.subscriptions so it is disposed on deactivation.
            context.subscriptions.push(statusBarItem);

        } catch (error: any) {
            const detailedError = error.response?.data?.message || error.message;
            vscode.window.showErrorMessage(`Registration failed: ${detailedError}`);
        }
    });
    context.subscriptions.push(disposable);
}