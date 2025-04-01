import * as vscode from 'vscode';
import { authenticationService } from '../services/userService';
import { displayUserView } from '../views/userView';

export function registerUpdateCommand(context: vscode.ExtensionContext) {
  const disposable = vscode.commands.registerCommand('intelligent-ide.update', async () => {
    // Load the login info from global state
    const loginInfo = context.globalState.get('loginInfo');
    if (!loginInfo) {
      const continueUpdate = await vscode.window.showWarningMessage(
        'You are not logged in. Do you want to log in before updating?',
        'Yes',
        'No'
      );

      if (continueUpdate === 'Yes') {
        vscode.commands.executeCommand('intelligent-ide.login'); // Redirect to login command
        return;
      } else {
        return; // User doesn't want to log in, so exit update command
      }
    }

    // Retrieve stored token from VS Code secret storage
    const storedToken = await context.secrets.get('authToken');
    if (!storedToken) {
      vscode.window.showErrorMessage('You must log in before updating.');
      return;
    }

    const username = await vscode.window.showInputBox({ prompt: 'Enter new username' });
    const password = await vscode.window.showInputBox({ prompt: 'Enter new password', password: true });

    if (!username || !password) {
      vscode.window.showErrorMessage('At least one field must be provided to update.');
      return;
    }

    // Call the update method with the stored token included
    try {
      const token = await authenticationService.update(username, password, storedToken);
      await authenticationService.getUserInfo(token, context);
      await context.secrets.store('authToken', token);
      displayUserView(context);
      vscode.window.showInformationMessage(`Updated successfully!`);
    } catch (error: any) {
      const detailedError = error.response?.data?.message || error.message;
      vscode.window.showErrorMessage(`Update failed: ${detailedError}`);
    }
  });
  context.subscriptions.push(disposable);
}