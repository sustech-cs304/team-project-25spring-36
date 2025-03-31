import * as vscode from 'vscode';
import { displayUserView } from '../views/userView';

export function registerLogoutCommand(context: vscode.ExtensionContext) {
  const disposable = vscode.commands.registerCommand('intelligent-ide.logout', async () => {
    try {
       const loginInfo = context.globalState.get('loginInfo');
          if (!loginInfo) {
           await vscode.window.showWarningMessage(
              'You are not logged in.'
            );
        }

      // Clear login info from global state
      await context.globalState.update('loginInfo', undefined);

      // Remove token from secrets
      await context.secrets.delete('authToken');

      // Update the user view
      displayUserView(context);

      vscode.window.showInformationMessage('Logout successful!');
    } catch (error: any) {
      console.error('Logout error:', error);
      vscode.window.showErrorMessage(`Logout failed: ${error.message}`);
    }
  });
  context.subscriptions.push(disposable);
}