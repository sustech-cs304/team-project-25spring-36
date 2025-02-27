import * as vscode from 'vscode';
import { authenticationService } from '../services/userService';

export function registerLoginCommand(context: vscode.ExtensionContext) {
  const disposable = vscode.commands.registerCommand('intelligent-ide.login', async () => {
    const username = await vscode.window.showInputBox({ prompt: 'Enter username' });
    const password = await vscode.window.showInputBox({ prompt: 'Enter password', password: true });

    if (username && password) {
      try {
        await authenticationService.login(username, password);
        vscode.window.showInformationMessage('Login successful!');
      } catch (error) {
        vscode.window.showErrorMessage('Login failed!');
      }
    } else {
      vscode.window.showErrorMessage('Username and password are required.');
    }
  });
  context.subscriptions.push(disposable);
}