import * as vscode from 'vscode';
import { createCourseTreeDataProvider, CourseTreeDataProvider } from '../views/CourseView'; // Updated import
import { updateChatView } from './ChatView';
import {
    registerUserView,
    updateLoginView,
    disposeUserView
} from './userView';

// Store view providers and UI elements
let courseTreeDataProvider: CourseTreeDataProvider | undefined;
let courseTreeView: vscode.TreeView<any> | undefined; // 'any' can be replaced with CourseTreeItem if preferred
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
    courseTreeDataProvider = createCourseTreeDataProvider(extContext);
    courseTreeView = vscode.window.createTreeView('courses', {
        treeDataProvider: courseTreeDataProvider,
        showCollapseAll: true
    });
    extContext.subscriptions.push(courseTreeView);

    return courseTreeDataProvider;
}

// Removed the local registerCourseView function from viewManager.ts as its logic is now integrated above.

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

        if (refreshAll || viewTypes.includes(ViewType.LOGIN)) {
            updateLoginView(context);
        }

        if ((refreshAll || viewTypes.includes(ViewType.COURSE)) && courseTreeDataProvider) {
            courseTreeDataProvider.refresh();
        }
        if (viewTypes.includes(ViewType.CHAT)) {
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
    disposeUserView();


    if (courseTreeView) {
        courseTreeView = undefined;
    }
    courseTreeDataProvider = undefined;

    if (chatViewPanel) {
        chatViewPanel.dispose();
        chatViewPanel = undefined;
    }
    if (qnaViewPanel) {
        qnaViewPanel.dispose();
        qnaViewPanel = undefined;
    }

    context = undefined;
}

/**
 * Add this function to export access to the chat panel
 */
export function getChatViewPanel(): vscode.WebviewPanel | undefined {
    return chatViewPanel;
}
