import * as vscode from 'vscode';
import { LoginInfo } from '../models/LoginInfo';

let statusBarItem: vscode.StatusBarItem | undefined; // Declare statusBarItem outside the function

export function displayUserView(context: vscode.ExtensionContext) {
  // Load the login info from global state
  const loginInfo: LoginInfo | undefined = context.globalState.get('loginInfo');

  if (loginInfo) {
    try {
      // Dispose of the previous status bar item if it exists
      statusBarItem?.dispose();

      // Create and show a status bar item with login info.
      statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
      statusBarItem.text = `$(account) ${loginInfo.username} `;
      statusBarItem.tooltip = "Logged in user info";
      statusBarItem.show();

      // Optionally, add statusBarItem to context.subscriptions so it is disposed on deactivation.
      context.subscriptions.push(statusBarItem);
    } catch (error) {
      console.error("Error updating status bar:", error);
      vscode.window.showErrorMessage("Failed to update status bar.");
    }
  } else {
    // No login info, clear the status bar
    // Dispose of the status bar item if it exists
    statusBarItem?.dispose();
    statusBarItem = undefined; // Reset statusBarItem to undefined
  }
}