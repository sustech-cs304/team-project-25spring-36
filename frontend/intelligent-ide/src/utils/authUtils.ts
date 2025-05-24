import * as vscode from 'vscode';
import { LoginInfo } from '../models/LoginInfo';

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
    const loginInfo = context.workspaceState.get<LoginInfo>('loginInfo');
    if (!loginInfo) {
        vscode.window.showWarningMessage('Please log in to proceed.');
        return null;
    }

    return {  token: loginInfo.token, loginInfo };
}