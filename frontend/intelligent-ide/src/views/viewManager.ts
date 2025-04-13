import * as vscode from 'vscode';
import { LoginInfo } from '../models/LoginInfo';
import { CourseTreeDataProvider } from '../views/CourseView';

// Store view providers and UI elements
let courseTreeDataProvider: CourseTreeDataProvider | undefined;
let courseTreeView: vscode.TreeView<any> | undefined;
let statusBarItem: vscode.StatusBarItem | undefined;
let context: vscode.ExtensionContext | undefined;

/**
 * View types that can be refreshed
 */
export enum ViewType {
    LOGIN,
    COURSE,
    ALL
}

/**
 * Initialize the view manager with required context and providers
 */
export function initializeViewManager(extContext: vscode.ExtensionContext): CourseTreeDataProvider {
    context = extContext;

    // Register user view (status bar)
    registerUserView(extContext);

    // Register course view
    courseTreeDataProvider = registerCourseView(extContext);

    return courseTreeDataProvider;
}

/**
 * Register user view components (status bar)
 */
function registerUserView(context: vscode.ExtensionContext): void {
    updateLoginView(context);
}

/**
 * Register course tree view
 */
function registerCourseView(context: vscode.ExtensionContext): CourseTreeDataProvider {
    // Create tree data provider
    const treeDataProvider = new CourseTreeDataProvider(context);
    courseTreeDataProvider = treeDataProvider;

    // Create tree view
    courseTreeView = vscode.window.createTreeView('courses', {
        treeDataProvider,
        showCollapseAll: true
    });

    context.subscriptions.push(courseTreeView);

    return treeDataProvider;
}

/**
 * Updates login-related UI components
 */
function updateLoginView(context: vscode.ExtensionContext): void {
    const loginInfo: LoginInfo | undefined = context.globalState.get('loginInfo');

    // Update context variables for when clauses
    updateLoginContext(context);

    if (loginInfo) {
        try {
            // Dispose of previous status bar item if exists
            if (statusBarItem) {
                statusBarItem.dispose();
            }

            // Create and show status bar with login info
            statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
            statusBarItem.text = `$(account) ${loginInfo.username} (${loginInfo.role})`;
            statusBarItem.tooltip = "Logged in user info";
            statusBarItem.command = 'intelligent-ide.switchRole';
            statusBarItem.show();

            context.subscriptions.push(statusBarItem);
        } catch (error) {
            console.error("Error updating status bar:", error);
            vscode.window.showErrorMessage("Failed to update status bar.");
        }
    } else {
        // Clear the status bar
        if (statusBarItem) {
            statusBarItem.dispose();
            statusBarItem = undefined;
        }
    }
}

/**
 * Update context for when clauses in package.json
 */
function updateLoginContext(context: vscode.ExtensionContext): void {
    const loginInfo: LoginInfo | undefined = context.globalState.get('loginInfo');

    // Set login status context
    vscode.commands.executeCommand('setContext', 'globalState.loginInfo', !!loginInfo);

    // Set user role context for when clauses
    if (loginInfo) {
        vscode.commands.executeCommand('setContext', 'globalState.userRole', loginInfo.role);
    } else {
        vscode.commands.executeCommand('setContext', 'globalState.userRole', undefined);
    }
}

/**
 * Refresh specified views
 * @param viewTypes Array of view types to refresh, defaults to ALL
 */
export async function refreshViews(viewTypes: ViewType[] = [ViewType.ALL]): Promise<void> {
    if (!context) {
        console.error('View manager not initialized with context');
        return;
    }

    try {
        const refreshAll = viewTypes.includes(ViewType.ALL);

        // First update context variables
        updateLoginContext(context);

        // Then update UI components
        if (refreshAll || viewTypes.includes(ViewType.LOGIN)) {
            updateLoginView(context);
        }

        if ((refreshAll || viewTypes.includes(ViewType.COURSE)) && courseTreeDataProvider) {
            courseTreeDataProvider.refresh();
        }

    } catch (error) {
        console.error('Error refreshing views:', error);
    }
}

/**
 * Convenience method to refresh all views
 */
export function refreshAllViews(): Promise<void> {
    return refreshViews([ViewType.ALL]);
}

/**
 * Clean up any resources when extension deactivates
 */
export function disposeViews(): void {
    if (statusBarItem) {
        statusBarItem.dispose();
        statusBarItem = undefined;
    }

    if (courseTreeView) {
        courseTreeView.dispose();
        courseTreeView = undefined;
    }

    courseTreeDataProvider = undefined;
    context = undefined;
}