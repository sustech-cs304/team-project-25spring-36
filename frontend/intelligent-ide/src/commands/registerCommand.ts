import * as vscode from 'vscode';
import { authenticationService } from '../services/userService';
import { displayUserView } from '../views/userView';

export function registerRegisterCommand(context: vscode.ExtensionContext) {
  const disposable = vscode.commands.registerCommand('intelligent-ide.register', async () => {
    // Load the login info from global state
    const loginInfo = context.globalState.get('loginInfo');

    if (loginInfo) {
      const continueRegistration = await vscode.window.showWarningMessage(
        'An account is already logged in. Registering a new account will log out the current account. Continue?',
        'Yes',
        'No'
      );

      if (continueRegistration !== 'Yes') {
        return; // User doesn't want to continue registration
      }
    }

    const username = await vscode.window.showInputBox({ prompt: 'Enter new username' });
    if (!username) {
      vscode.window.showErrorMessage('Username is required.');
      return;
    }

    const email = await vscode.window.showInputBox({ prompt: 'Enter your email address' });
    if (!email) {
      vscode.window.showErrorMessage('Email is required.');
      return;
    }

    // Request verification code
    try {
      await authenticationService.getVerificationCode(email);
      vscode.window.showInformationMessage(`Verification code sent to ${email}`);
    } catch (error: any) {
      const detailedError = error.response?.data?.message || error.message;
      vscode.window.showErrorMessage(`Failed to send verification code: ${detailedError}`);
      return;
    }

    const verificationCode = await vscode.window.showInputBox({
      prompt: 'Enter the verification code sent to your email'
    });
    if (!verificationCode) {
      vscode.window.showErrorMessage('Verification code is required.');
      return;
    }

    const password = await vscode.window.showInputBox({ prompt: 'Enter password', password: true });
    if (!password) {
      vscode.window.showErrorMessage('Password is required.');
      return;
    }

    // Call your service to register the new user.
    try {
      const token = await authenticationService.register(username, email, password, verificationCode.toUpperCase());
      const userInfo = await authenticationService.getUserInfo(token);

      // Store login info in global state
      const newLoginInfo = {
        token: token,
        username: userInfo.username,
        email: userInfo.email
      };
      await context.globalState.update('loginInfo', newLoginInfo);

      // Store token securely as login certificate
      await context.secrets.store("authToken", token);
      vscode.window.showInformationMessage(`Registration successful for ${username} !`);

      // Update the user view
      displayUserView(context);

    } catch (error: any) {
      const detailedError = error.response?.data?.message || error.message;
      vscode.window.showErrorMessage(`Registration failed: ${detailedError}`);
    }
  });
  context.subscriptions.push(disposable);
}