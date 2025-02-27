import * as vscode from 'vscode';
import { authenticationService } from '../services/userService';

export function registerUpdateCommand(context: vscode.ExtensionContext) {
  const disposable = vscode.commands.registerCommand('intelligent-ide.update', async () => {
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

    // Call your service update the new user.
    try {
      await authenticationService.update(username, password, role);
      vscode.window.showInformationMessage(`Update successful for ${username} as ${role}!`);
    } catch (error) {
      vscode.window.showErrorMessage('Update failed!');
    }
  });
  context.subscriptions.push(disposable);
}