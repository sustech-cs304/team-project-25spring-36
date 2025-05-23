import * as vscode from 'vscode';
import { LoginInfo } from '../models/LoginInfo'; // Adjust the path as necessary

export interface AuthDetails {
    token: string;
    loginInfo: LoginInfo;
}

/**
 * Retrieves authentication token and login information.
 * Shows a warning message and returns null if either is missing.
 * @param context vscode.ExtensionContext
 * @returns AuthDetails object or null if authentication fails.
 */
export async function getAuthDetails(context: vscode.ExtensionContext): Promise<AuthDetails | null> {
    const loginInfo = context.globalState.get<LoginInfo>('loginInfo');
    if (!loginInfo) {
        vscode.window.showWarningMessage('Please log in to proceed.');
        return null;
    }

    const token = await context.secrets.get('authToken');
    if (!token) {
        vscode.window.showWarningMessage('Authentication token not found. Please log in again.');
        return null;
    }

    return { token, loginInfo };
}