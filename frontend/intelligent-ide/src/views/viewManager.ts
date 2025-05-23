import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { LoginInfo } from '../models/LoginInfo';
import { createCourseTreeDataProvider, CourseTreeDataProvider } from '../views/CourseView'; // 合并导入
import { getNonce, updateChatView } from './ChatView';
import {
    registerUserView,
    updateLoginView,
    disposeUserView
} from './userView';

// Store view providers and UI elements
let courseTreeDataProvider: CourseTreeDataProvider | undefined;
let courseTreeView: vscode.TreeView<any> | undefined;
let context: vscode.ExtensionContext | undefined;
let chatViewPanel: vscode.WebviewPanel | undefined;
let qnaViewPanel: vscode.WebviewPanel | undefined;

export enum ViewType {
    LOGIN,
    COURSE,
    CHAT,
    QNA,
    ALL
}

export function initializeViewManager(extContext: vscode.ExtensionContext): CourseTreeDataProvider {
    context = extContext;

    // 合并用户视图注册
    registerUserView(extContext);

    // 使用新的创建方法
    courseTreeDataProvider = createCourseTreeDataProvider(extContext);
    courseTreeView = vscode.window.createTreeView('courses', {
        treeDataProvider: courseTreeDataProvider,
        showCollapseAll: true
    });
    extContext.subscriptions.push(courseTreeView);

    return courseTreeDataProvider;
}

export async function refreshViews(viewTypes: ViewType[] = [ViewType.ALL]): Promise<void> {
    if (!context) {
        console.error('View manager not initialized with context');
        return;
    }

    try {
        const refreshAll = viewTypes.includes(ViewType.ALL);

        // 合并登录视图更新
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

export function refreshAllViews(): Promise<void> {
    return refreshViews([ViewType.ALL]);
}

export function disposeViews(): void {
    // 合并用户视图清理
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

export function getChatViewPanel(): vscode.WebviewPanel | undefined {
    return chatViewPanel;
}

// 保留 QnA 视图相关功能
export function registerQnAView(context: vscode.ExtensionContext): void {
    if (qnaViewPanel) {
        qnaViewPanel.reveal(vscode.ViewColumn.One);
        return;
    }

    qnaViewPanel = vscode.window.createWebviewPanel(
        'qnaWebView',
        'QnA Interface',
        vscode.ViewColumn.One,
        {
            enableScripts: true,
            retainContextWhenHidden: true,
            localResourceRoots: [
                vscode.Uri.joinPath(context.extensionUri, 'src', 'views', 'qnaWebView')
            ]
        }
    );

    updateQnAView(context);

    qnaViewPanel.onDidDispose(() => {
        qnaViewPanel = undefined;
    });
}

function updateQnAView(context: vscode.ExtensionContext): void {
    if (!qnaViewPanel) return;

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

        htmlContent = htmlContent
            .replace('{{cspSource}}', webview.cspSource)
            .replace(/{{nonce}}/g, nonce)
            .replace('{{stylesUri}}', stylesUri.toString())
            .replace('{{scriptUri}}', scriptUri.toString());

        qnaViewPanel.webview.html = htmlContent;
    } catch (error) {
        console.error('Error updating QnA view:', error);
    }
}

// 保留新增的获取课程树方法
export function getCourseTreeProvider(): CourseTreeDataProvider | undefined {
    return courseTreeDataProvider;
}