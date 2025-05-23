import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { LoginInfo } from '../models/LoginInfo';
import { CourseTreeDataProvider } from '../views/CourseView';
import { getNonce, updateChatView } from './ChatView';

// Store view providers and UI elements
let courseTreeDataProvider: CourseTreeDataProvider | undefined;
let courseTreeView: vscode.TreeView<any> | undefined;
let statusBarItem: vscode.StatusBarItem | undefined;
let context: vscode.ExtensionContext | undefined;
let chatViewPanel: vscode.WebviewPanel | undefined;
let qnaViewPanel: vscode.WebviewPanel | undefined;

/**
 * View types that can be refreshed
 */
export enum ViewType {
    LOGIN,
    COURSE,
    CHAT,
    QNA,
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

    // Don't automatically create the chat view panel on startup
    // Just initialize any necessary chat-related setup that doesn't create a panel
    // registerChatView(extContext);

    return courseTreeDataProvider;
}

/**
 * Register user view components (status bar
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

        // For chat view, just call updateChatView from ChatView.ts
        if (refreshAll || viewTypes.includes(ViewType.CHAT)) {
            updateChatView(context);
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

    if (chatViewPanel) {
        chatViewPanel.dispose();
        chatViewPanel = undefined;
    }

    courseTreeDataProvider = undefined;
    context = undefined;
}

/**
 * Add this function to export access to the chat panel
 */
export function getChatViewPanel(): vscode.WebviewPanel | undefined {
    return chatViewPanel;
}

/**
 * Register QnA Webview
 */
export function registerQnAView(context: vscode.ExtensionContext): void {
    // If the panel already exists, reveal it
    if (qnaViewPanel) {
        qnaViewPanel.reveal(vscode.ViewColumn.One);
        return;
    }

    // Create a new Webview panel
    qnaViewPanel = vscode.window.createWebviewPanel(
        'qnaWebView', // Internal identifier
        'QnA Interface', // Title of the panel
        vscode.ViewColumn.One, // Show in the first column
        {
            enableScripts: true, // Allow JavaScript in the Webview
            retainContextWhenHidden: true, // Keep the Webview state when hidden
            localResourceRoots: [
                vscode.Uri.joinPath(context.extensionUri, 'src', 'views', 'qnaWebView')
            ]
        }
    );

    // Set the initial HTML content
    updateQnAView(context);

    // Handle panel disposal
    qnaViewPanel.onDidDispose(() => {
        qnaViewPanel = undefined;
    });
}

/**
 * Update QnA Webview content
 */
function updateQnAView(context: vscode.ExtensionContext): void {
    if (!qnaViewPanel) {
        return;
    }

    try {
        const webviewFolder = 'qnaWebView';
        const htmlPath = path.join(context.extensionUri.fsPath, 'src', 'views', webviewFolder, 'index.html');
        let htmlContent = fs.readFileSync(htmlPath, 'utf8');

        const webview = qnaViewPanel.webview;
        const stylesUri = webview.asWebviewUri(
            vscode.Uri.joinPath(context.extensionUri, 'src', 'views', webviewFolder, 'style.css')
        );
        const scriptUri = webview.asWebviewUri(
            vscode.Uri.joinPath(context.extensionUri, 'src', 'views', webviewFolder, 'main.js')
        );
        const nonce = getNonce();

        // Replace placeholders in the HTML
        htmlContent = htmlContent
            .replace('{{cspSource}}', webview.cspSource)
            .replace(/{{nonce}}/g, nonce)
            .replace('{{stylesUri}}', stylesUri.toString())
            .replace('{{scriptUri}}', scriptUri.toString());

        // Set the Webview HTML content
        qnaViewPanel.webview.html = htmlContent;
    } catch (error) {
        console.error('Error updating QnA view:', error);
    }
}

