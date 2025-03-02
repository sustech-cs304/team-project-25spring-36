import * as vscode from 'vscode';
import { authenticationService } from '../services/userService';

export function registerUpdateCommand(context: vscode.ExtensionContext) {
  const disposable = vscode.commands.registerCommand('intelligent-ide.update', async () => {
    // Retrieve stored token from VS Code secret storage
    const storedToken = await context.secrets.get('authToken');
    if (!storedToken) {
      vscode.window.showErrorMessage('You must log in before updating.');
      return;
    }

    const username = await vscode.window.showInputBox({ prompt: 'Enter new username' });
    const password = await vscode.window.showInputBox({ prompt: 'Enter new password', password: true });

    if (!username || !password) {
      vscode.window.showErrorMessage('Username and password are required.');
      return;
    }

    const role = await vscode.window.showQuickPick(['student', 'teacher'], {
      placeHolder: 'Select a role'
    });

    if (!role) {
      vscode.window.showErrorMessage('Role selection is required.');
      return;
    }

    // Call the update method with the stored token included
    try {
      const token = await authenticationService.update(username, password, role, storedToken);
      await context.secrets.store('authToken', token);
      vscode.window.showInformationMessage(`Updated ${username} successfully!`);
    } catch (error: any) {
      const detailedError = error.response?.data?.message || error.message;
      vscode.window.showErrorMessage(`Update failed: ${detailedError}`);
    }
  });
  context.subscriptions.push(disposable);
}