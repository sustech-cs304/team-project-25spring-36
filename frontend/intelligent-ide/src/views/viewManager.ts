import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import { LoginInfo } from '../models/LoginInfo';
import { CourseTreeDataProvider } from '../views/CourseView';
import {
    handleUserMessage,
    handleCodeAttachment,
    getNonce
} from './ChatView';
import * as ai from '../services/AIService';

// Store view providers and UI elements
let courseTreeDataProvider: CourseTreeDataProvider | undefined;
let courseTreeView: vscode.TreeView<any> | undefined;
let statusBarItem: vscode.StatusBarItem | undefined;
let context: vscode.ExtensionContext | undefined;
let chatViewPanel: vscode.WebviewPanel | undefined;

/**
 * View types that can be refreshed
 */
export enum ViewType {
    LOGIN,
    COURSE,
    CHAT,
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
 * Register chat view panel and initialize AI service
 */
function registerChatView(context: vscode.ExtensionContext): void {
    // If we already have a panel, show it
    if (chatViewPanel) {
        chatViewPanel.reveal(vscode.ViewColumn.Two);
        return;
    }

    // Initialize AI service early
    initializeAIService(context).catch(error => {
        vscode.window.showErrorMessage(`Failed to initialize AI service: ${error.message}`);
    });

    // Create a new panel
    chatViewPanel = vscode.window.createWebviewPanel(
        'intelliCode.aiChat',
        'AI Assistant',
        vscode.ViewColumn.Two,
        {
            enableScripts: true,
            retainContextWhenHidden: true,
            localResourceRoots: [
                vscode.Uri.joinPath(context.extensionUri, 'src', 'views', 'chatwebview')
            ]
        }
    );

    // Set the initial HTML content
    updateChatView();

    // Handle messages from the webview
    chatViewPanel.webview.onDidReceiveMessage(async message => {
        switch (message.command) {
            case 'sendMessage':
                handleUserMessage(chatViewPanel!, message.text, context);
                break;
            case 'attachCode':
                handleCodeAttachment(chatViewPanel!);
                break;
        }
    });

    // Handle panel disposal
    chatViewPanel.onDidDispose(() => {
        chatViewPanel = undefined;
    }, null, context.subscriptions);
}

/**
 * Initialize the AI service
 */
async function initializeAIService(context: vscode.ExtensionContext): Promise<void> {
    try {
        const apiKey = await ai.getOpenAIKey(context);
        ai.initializeAIService(apiKey);
    } catch (error) {
        console.error('Error initializing AI service:', error);
        throw error;
    }
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

        // For chat view, we need special handling
        if (refreshAll || viewTypes.includes(ViewType.CHAT)) {
            // If panel doesn't exist, create it
            if (!chatViewPanel) {
                registerChatView(context);
            } else {
                // Otherwise just update existing panel
                updateChatView();
                // Make sure to reveal it since it might be hidden
                chatViewPanel.reveal(vscode.ViewColumn.Two);
            }
        }

    } catch (error) {
        console.error('Error refreshing views:', error);
    }
}

/**
 * Update chat view (refresh)
 */
function updateChatView(): void {
    if (!chatViewPanel || !context) { return; }

    try {
        // Read the HTML template
        const htmlPath = path.join(context.extensionUri.fsPath, 'src', 'views', 'chatwebview', 'index.html');
        let htmlContent = fs.readFileSync(htmlPath, 'utf8');

        // Get web resources
        const webview = chatViewPanel.webview;
        const stylesUri = webview.asWebviewUri(vscode.Uri.joinPath(context.extensionUri, 'src', 'views', 'chatwebview', 'styles.css'));
        const scriptUri = webview.asWebviewUri(vscode.Uri.joinPath(context.extensionUri, 'src', 'views', 'chatwebview', 'main.js'));
        const nonce = getNonce();

        // Replace placeholders in the HTM
        htmlContent = htmlContent
            .replace('{{cspSource}}', webview.cspSource)
            .replace(/{{nonce}}/g, nonce)
            .replace('{{stylesUri}}', stylesUri.toString())
            .replace('{{scriptUri}}', scriptUri.toString());

        // Set the webview HTML content
        chatViewPanel.webview.html = htmlContent;
        chatViewPanel.reveal(vscode.ViewColumn.Two);

    } catch (error) {
        console.error('Error updating chat view:', error);
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