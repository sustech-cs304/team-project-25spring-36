import * as vscode from 'vscode';
import { authenticationService } from '../services/userService';
import { displayUserView } from '../views/userView'; // Import the login view logic

export function registerLoginCommand(context: vscode.ExtensionContext) {
  const disposable = vscode.commands.registerCommand('intelligent-ide.login', async () => {
    try {
      // Load the login info from global state
      const loginInfo = context.globalState.get('loginInfo');

      if (loginInfo) {
        const changeAccount = await vscode.window.showWarningMessage(
          'An account is already logged in. Do you want to log in with a different account?',
          'Yes',
          'No'
        );

        if (changeAccount !== 'Yes') {
          return;
        }
        vscode.commands.executeCommand('intelligent-ide.logout');
      }

      const email = await vscode.window.showInputBox({ prompt: 'Enter email' });
      const password = await vscode.window.showInputBox({ prompt: 'Enter password', password: true });

      if (email && password) {
        const token = await authenticationService.login(email, password);
        await authenticationService.getUserInfo(token, context);

        // Store token securely as login certificate
        await context.secrets.store('authToken', token);
        vscode.window.showInformationMessage('Login successful!');

        // Uplogin the login view
        displayUserView(context);
      } else {
        vscode.window.showErrorMessage('Username and password are required.');
      }
    } catch (error: any) {
      // Check if axios error contains response data for additional details
      const detailedError = error.response?.data?.message || error.message;
      vscode.window.showErrorMessage(`Login failed: ${detailedError}`);
    }
  });
  context.subscriptions.push(disposable);
}