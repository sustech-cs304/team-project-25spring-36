import * as vscode from 'vscode';
import { authenticationService } from '../services/userService';

export function registerLoginCommand(context: vscode.ExtensionContext) {
  const disposable = vscode.commands.registerCommand('intelligent-ide.login', async () => {
    const username = await vscode.window.showInputBox({ prompt: 'Enter username' });
    const password = await vscode.window.showInputBox({ prompt: 'Enter password', password: true });

    if (username && password) {
      try {
        const token = await authenticationService.login(username, password);
        // Store token securely as login certificate
        await context.secrets.store('authToken', token);
        vscode.window.showInformationMessage('Login successful!');
        
        const userInfo = await authenticationService.getUserInfo(token);
        // Create and show a status bar item with login info.
        const statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
        statusBarItem.text = `$(account) ${userInfo.username} (${userInfo.role})`;
        statusBarItem.tooltip = "Logged in user info";
        statusBarItem.show();

        // Optionally, add statusBarItem to context.subscriptions so it is disposed on deactivation.
        context.subscriptions.push(statusBarItem);
      } catch (error: any) {
        // Check if axios error contains response data for additional details
        const detailedError = error.response?.data?.message || error.message;
        vscode.window.showErrorMessage(`Login failed: ${detailedError}`);
      }
    } else {
      vscode.window.showErrorMessage('Username and password are required.');
    }
  });
  context.subscriptions.push(disposable);
}