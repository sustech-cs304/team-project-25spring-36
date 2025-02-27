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
            await authenticationService.register(username, password, role);
            vscode.window.showInformationMessage(`Registration successful for ${username} as ${role}!`);
        } catch (error) {
            vscode.window.showErrorMessage('Registration failed!');
        }
    });
    context.subscriptions.push(disposable);
}