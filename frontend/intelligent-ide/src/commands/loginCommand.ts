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
          return; // User doesn't want to change accounts
        }
      }

      const email = await vscode.window.showInputBox({ prompt: 'Enter email' });
      const password = await vscode.window.showInputBox({ prompt: 'Enter password', password: true });

      if (email && password) {
        const token = await authenticationService.login(email, password);
        const userInfo = await authenticationService.getUserInfo(token);

        // Store login info in global state
        const newLoginInfo = {
          token: token,
          username: userInfo.username,
          email: userInfo.email
        };
        await context.globalState.update('loginInfo', newLoginInfo);

        // Store token securely as login certificate
        await context.secrets.store('authToken', token);
        vscode.window.showInformationMessage('Login successful!');

        // Update the login view
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