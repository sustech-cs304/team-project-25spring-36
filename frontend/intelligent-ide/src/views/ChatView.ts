import * as vscode from 'vscode';
import * as path from 'path';
import * as ai from '../services/AIService';

let chatViewPanel: vscode.WebviewPanel | undefined;
// Flag to track if response should be terminated
let terminateCurrentResponse = false;

export function updateChatView(context: vscode.ExtensionContext): void {
    if (!chatViewPanel) {
        registerChatView(context);
    } else {
        setChatViewHtml(context);
        chatViewPanel.reveal(vscode.ViewColumn.Two);
    }
}

function registerChatView(context: vscode.ExtensionContext): void {
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

    setChatViewHtml(context);

    chatViewPanel.webview.onDidReceiveMessage(async message => {
        switch (message.command) {
            case 'sendMessage':
                // Reset terminate flag before starting a new response
                terminateCurrentResponse = false;
                await handleUserMessage(chatViewPanel!, message.text, message.attachments || [], context);
                break;
            case 'attachCode':
                await handleCodeAttachment(chatViewPanel!);
                break;
            case 'terminateResponse':
                terminateCurrentResponse = true;
                break;
            case 'dropFiles':
                // Handle files dropped into the chat
                if (message.filePaths && message.filePaths.length > 0) {
                    for (const filePath of message.filePaths) {
                        try {
                            // Handle different file path formats that could come from drag-and-drop
                            let uri: vscode.Uri;

                            // Handle VS Code resource URIs and other formats
                            if (filePath.startsWith('vscode-resource:')) {
                                // Convert vscode-resource URI to a file URI
                                uri = vscode.Uri.parse(filePath.replace('vscode-resource:', 'file:'));
                            } else if (filePath.startsWith('vscode-file:')) {
                                uri = vscode.Uri.parse(filePath);
                            } else if (filePath.startsWith('file:')) {
                                uri = vscode.Uri.parse(filePath);
                            } else if (filePath.startsWith('untitled:')) {
                                // Handle untitled documents
                                uri = vscode.Uri.parse(filePath);
                            } else {
                                // Assume it's a regular file path
                                uri = vscode.Uri.file(filePath);
                            }

                            // Try to find the document if it's open in the editor
                            const allDocs = vscode.workspace.textDocuments;
                            let document = allDocs.find(doc =>
                                doc.uri.toString() === uri.toString() ||
                                doc.fileName === uri.fsPath
                            );

                            // If not found in open editors, try to open it
                            if (!document) {
                                try {
                                    document = await vscode.workspace.openTextDocument(uri);
                                } catch (e) {
                                    console.log(`Could not find or open document for ${filePath}`, e);
                                }
                            }

                            const fileName = path.basename(uri.fsPath || uri.path);
                            const fileType = getFileType(fileName);

                            // Get content if we have a document or can read one
                            let fileContent = null;
                            if (document) {
                                fileContent = document.getText();
                            } else if (fileType === 'code' || fileType === 'text') {
                                try {
                                    document = await vscode.workspace.openTextDocument(uri);
                                    fileContent = document.getText();
                                } catch (e) {
                                    // If can't open as text, just use the reference
                                    console.log(`Could not read file content for ${fileName}`, e);
                                }
                            }

                            chatViewPanel!.webview.postMessage({
                                command: 'fileAttachment',
                                filename: fileName,
                                filePath: uri.fsPath || uri.path,
                                content: fileContent,
                                fileType: fileType
                            });
                        } catch (error: any) {
                            console.error('Error processing dropped file:', error);
                            chatViewPanel!.webview.postMessage({
                                command: 'error',
                                text: `Error attaching dropped file: ${error.message}`
                            });
                        }
                    }
                }
                break;
        }
    });

    chatViewPanel.onDidDispose(() => {
        chatViewPanel = undefined;
    });
}

function setChatViewHtml(context: vscode.ExtensionContext): void {
    if (!chatViewPanel) return;
    const webview = chatViewPanel.webview;
    const extensionUri = context.extensionUri;
    const stylesUri = webview.asWebviewUri(vscode.Uri.joinPath(extensionUri, 'src', 'views', 'chatwebview', 'styles.css'));
    const highlightCssUri = webview.asWebviewUri(vscode.Uri.joinPath(extensionUri, 'src', 'views', 'chatwebview', 'github.min.css'));
    const scriptUri = webview.asWebviewUri(vscode.Uri.joinPath(extensionUri, 'src', 'views', 'chatwebview', 'main.js'));
    const showdownUri = webview.asWebviewUri(vscode.Uri.joinPath(extensionUri, 'src', 'views', 'chatwebview', 'showdown.min.js'));
    const highlightUri = webview.asWebviewUri(vscode.Uri.joinPath(extensionUri, 'src', 'views', 'chatwebview', 'highlight.min.js'));
    const dompurifyUri = webview.asWebviewUri(vscode.Uri.joinPath(extensionUri, 'src', 'views', 'chatwebview', 'dompurify.min.js'));
    const nonce = getNonce();

    chatViewPanel.webview.html = `
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta http-equiv="Content-Security-Policy"
            content="default-src 'none'; style-src ${webview.cspSource}; script-src 'nonce-${nonce}'; img-src ${webview.cspSource} data:;">
        <link rel="stylesheet" href="${stylesUri}">
        <link rel="stylesheet" href="${highlightCssUri}">
        <title>AI Assistant</title>
    </head>
    <body>
        <div id="chat-container"></div>
        <div id="input-container">
            <div id="attachments-panel"></div>
            <textarea id="message-input" placeholder="Ask me anything..." rows="3"></textarea>
            <div class="button-container">
                <button id="attach-button">Attach Files</button>
                <button id="send-button">Send</button>
            </div>
        </div>
        <script nonce="${nonce}" src="${showdownUri}"></script>
        <script nonce="${nonce}" src="${highlightUri}"></script>
        <script nonce="${nonce}" src="${dompurifyUri}"></script>
        <script nonce="${nonce}" src="${scriptUri}"></script>
    </body>
    </html>
    `;
}

/**
 * Generate a nonce for script security
 */
export function getNonce(): string {
    let text = '';
    const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    for (let i = 0; i < 32; i++) {
        text += possible.charAt(Math.floor(Math.random() * possible.length));
    }
    return text;
}

/**
 * Process user message and get streaming AI response
 */
export async function handleUserMessage(
    panel: vscode.WebviewPanel,
    text: string,
    attachments: any[],
    context: vscode.ExtensionContext
): Promise<void> {
    try {
        panel.webview.postMessage({ command: 'aiResponseStart' });
        await ai.getChatResponseStream(
            text,
            attachments,
            context,
            (chunk: string) => {
                // Check if termination was requested
                if (terminateCurrentResponse) {
                    throw new Error('TERMINATED');
                }
                panel.webview.postMessage({ command: 'aiResponseChunk', text: chunk });
            }
        );
        panel.webview.postMessage({ command: 'aiResponseComplete' });
    } catch (error: any) {
        if (error.message === 'TERMINATED') {
            // Handle termination gracefully
            panel.webview.postMessage({ command: 'aiResponseTerminated' });
        } else {
            panel.webview.postMessage({ command: 'error', text: `Error: ${error.message}` });
        }
    }
}

/**
 * Handle file attachments from current editor or file system
 */
export async function handleCodeAttachment(panel: vscode.WebviewPanel): Promise<void> {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        // If no editor is active, allow user to select a file
        const fileUris = await vscode.window.showOpenDialog({
            canSelectMany: true,
            openLabel: 'Attach',
            filters: {
                'All Files': ['*']
            }
        });

        if (fileUris && fileUris.length > 0) {
            for (const uri of fileUris) {
                try {
                    const fileName = path.basename(uri.fsPath);
                    const fileType = getFileType(fileName);

                    // For code and text files, get the content
                    let fileContent = null;
                    if (fileType === 'code' || fileType === 'text') {
                        try {
                            const document = await vscode.workspace.openTextDocument(uri);
                            fileContent = document.getText();
                        } catch (e) {
                            // If can't open as text, just use the reference
                            console.log(`Could not read file content for ${fileName}`, e);
                        }
                    }

                    panel.webview.postMessage({
                        command: 'fileAttachment',
                        filename: fileName,
                        filePath: uri.fsPath,
                        content: fileContent,
                        fileType: fileType
                    });
                } catch (error: any) {
                    panel.webview.postMessage({
                        command: 'error',
                        text: `Error attaching file: ${error.message}`
                    });
                }
            }
        }
        return;
    }

    // If editor is active, use its content
    const document = editor.document;
    const selection = editor.selection;
    const text = selection.isEmpty ? document.getText() : document.getText(selection);

    panel.webview.postMessage({
        command: 'codeAttachment',
        filename: path.basename(document.fileName),
        filePath: document.fileName,
        content: text,
        fileType: 'code'
    });
}

/**
 * Determine file type based on extension
 */
function getFileType(fileName: string): string {
    const ext = path.extname(fileName).toLowerCase();
    if (['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'].includes(ext)) {
        return 'image';
    } else if (ext === '.pdf') {
        return 'pdf';
    } else if (['.js', '.ts', '.py', '.java', '.html', '.css', '.json', '.md', '.h', '.c'].includes(ext)) {
        return 'code';
    } else if (['.txt', '.log', '.csv', '.xml'].includes(ext)) {
        return 'text';
    } else {
        return 'unknown';
    }
}