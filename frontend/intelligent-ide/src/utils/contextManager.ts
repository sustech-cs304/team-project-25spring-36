import * as vscode from 'vscode';
import { LoginInfo } from '../models/LoginInfo';

/**
 * Manages context variables used for when clauses in package.jso
 */
export class ContextManager {
    /**
     * Update context values related to user login state
     */
    static updateLoginContext(context: vscode.ExtensionContext): void {
        const loginInfo: LoginInfo | undefined = context.globalState.get('loginInfo');

        // Set login status context
        vscode.commands.executeCommand('setContext', 'globalState.loginInfo', !!loginInfo);

        // Set user role context
        if (loginInfo) {
            vscode.commands.executeCommand('setContext', 'globalState.userRole', loginInfo.role);
        } else {
            vscode.commands.executeCommand('setContext', 'globalState.userRole', undefined);
        }
    }
}