import * as vscode from 'vscode';
import { authenticationService } from '../services/userService';
import { ViewType, refreshAllViews, refreshViews } from '../views/viewManager';
import { getAuthDetails } from '../utils/authUtils';
/**
 * Register all user-related commands
 */
export function registerUserCommands(context: vscode.ExtensionContext): void {
    registerLoginCommand(context);
    registerRegisterCommand(context);
    registerUpdateCommand(context);
    registerLogoutCommand(context);
    registerSwitchRoleCommand(context);
}
/**
 * Register the login command
 */
function registerLoginCommand(context: vscode.ExtensionContext): void {
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

                refreshAllViews();
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

/**
 * Register the register command
 */
function registerRegisterCommand(context: vscode.ExtensionContext): void {
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
            await authenticationService.getUserInfo(token, context);

            // Store token securely as login certificate
            await context.secrets.store("authToken", token);
            vscode.window.showInformationMessage(`Registration successful for ${username} !`);

            refreshAllViews();

        } catch (error: any) {
            const detailedError = error.response?.data?.message || error.message;
            vscode.window.showErrorMessage(`Registration failed: ${detailedError}`);
        }
    });
    context.subscriptions.push(disposable);
}

/**
 * Register the update command
 */
function registerUpdateCommand(context: vscode.ExtensionContext): void {
    const disposable = vscode.commands.registerCommand('intelligent-ide.update', async () => {
        const authDetails = await getAuthDetails(context);
        if (!authDetails) {
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

        const username = await vscode.window.showInputBox({ prompt: 'Enter new username' });
        const password = await vscode.window.showInputBox({ prompt: 'Enter your password', password: true });

        if (!username || !password) {
            vscode.window.showErrorMessage('Both fields must be provided to update.');
            return;
        }

        // Call the update method with the stored token included
        try {
            const token = await authenticationService.update(username, password, authDetails.token);
            await authenticationService.getUserInfo(token, context);
            await context.secrets.store('authToken', token);
            refreshViews([ViewType.LOGIN]);
            vscode.window.showInformationMessage(`Updated successfully!`);
        } catch (error: any) {
            const detailedError = error.response?.data?.message || error.message;
            vscode.window.showErrorMessage(`Update failed: ${detailedError}`);
        }
    });
    context.subscriptions.push(disposable);
}

/**
 * Register the logout command
 */
function registerLogoutCommand(context: vscode.ExtensionContext): void {
    const disposable = vscode.commands.registerCommand('intelligent-ide.logout', async () => {
        try {
            const authDetails = await getAuthDetails(context);
            if (!authDetails) {
                return [];
            }


            // Clear login info from global state
            await context.globalState.update('loginInfo', undefined);
            context.globalState.update('userRole', undefined);
            // Remove token from secrets
            await context.secrets.delete('authToken');

            refreshAllViews();

            vscode.window.showInformationMessage('Logout successful!');
        } catch (error: any) {
            console.error('Logout error:', error);
            vscode.window.showErrorMessage(`Logout failed: ${error.message}`);
        }
    });
    context.subscriptions.push(disposable);
}

/**
 * Register the switch role command
 */
function registerSwitchRoleCommand(context: vscode.ExtensionContext): void {
    const disposable = vscode.commands.registerCommand('intelligent-ide.switchRole', async () => {
        try {
            const authDetails = await getAuthDetails(context);
            if (!authDetails) {
                return []; // Auth failed
            }
            const { token, loginInfo } = authDetails;


            // Show a quick pick menu to select role
            const selectedRole = await vscode.window.showQuickPick(
                ['student', 'teacher'],
                {
                    placeHolder: 'Select your role',
                    title: 'Switch Role',
                }
            );

            if (!selectedRole) {
                return; // User cancelled
            }

            // Update the role in the login info
            const updatedLoginInfo = {
                ...loginInfo,
                role: selectedRole
            };

            // Save updated login info
            await context.globalState.update('loginInfo', updatedLoginInfo);

            refreshViews([ViewType.LOGIN, ViewType.COURSE]);


            vscode.window.showInformationMessage(`Role switched to: ${selectedRole}`);
        } catch (error: any) {
            vscode.window.showErrorMessage(`Failed to switch role: ${error.message}`);
        }
    });

    context.subscriptions.push(disposable);
}
