import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import PDFDocument from 'pdfkit';
import { registerUserCommands } from './UserCommands';
import { registerCourseCommands } from './CourseCommands';
import { registerChatCommands } from './ChatCommands';
import { CourseTreeDataProvider } from '../views/CourseView';
import { ViewType, refreshViews, registerQnAView } from '../views/viewManager';
import { registerAssignmentCommands } from './AssignmentCommands';

/**
 * Centralized command registration manager
 * Handles all command registrations in the extension
 */
export class CommandManager {
    private context: vscode.ExtensionContext;
    private courseTreeDataProvider?: CourseTreeDataProvider;

    constructor(context: vscode.ExtensionContext, courseTreeDataProvider?: CourseTreeDataProvider) {
        this.context = context;
        this.courseTreeDataProvider = courseTreeDataProvider;
    }

    /**
     * Register all commands for the extension
     */
    public registerAllCommands(): void {
        this.registerGlobalCommands();
        this.registerUserCommands();
        this.registerCourseCommands();
        this.registerChatCommands();
        this.registerAssignmentCommands();
        this.registerQnACommands();
        this.registerNotebookCommands();
    }


    /**
    * Register QnA-related commands
    */
    private registerQnACommands(): void {
        const qnaDisposable = vscode.commands.registerCommand('intelligent-ide.qna.open', () => {
            // Delegate to ViewManager to handle the Webview creation
            registerQnAView(this.context);
        });

        this.context.subscriptions.push(qnaDisposable);
    }


    /**
     * Register global/utility commands
     */
    private registerGlobalCommands(): void {
        const refreshDisposable = vscode.commands.registerCommand(
            'intelligent-ide.views.refresh',
            async (viewTypes?: ViewType[]) => {
                await refreshViews(viewTypes);
            }
        );

        this.context.subscriptions.push(refreshDisposable);
    }

    /**
     * Register user-related commands
     */
    private registerUserCommands(): void {
        registerUserCommands(this.context);
    }

    /**
     * Register course-related commands
     */
    private registerCourseCommands(): void {
        registerCourseCommands(this.context, this.courseTreeDataProvider);
    }

    private registerChatCommands(): void {
        registerChatCommands(this.context);
    }

    private registerAssignmentCommands(): void {
        registerAssignmentCommands(this.context);
    }

    /**
     * Register notebook-related commands
     */
    private registerNotebookCommands(): void {
        const exportToPdfDisposable = vscode.commands.registerCommand('intelligent-ide.notebook.exportToPdf', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showErrorMessage('No active notebook to export.');
                return;
            }

            const content = editor.document.getText();
            const saveUri = await vscode.window.showSaveDialog({
                filters: { 'PDF Files': ['pdf'] },
                defaultUri: vscode.Uri.file(path.join(this.context.extensionPath, 'notebook.pdf')),
            });

            if (!saveUri) {
                vscode.window.showInformationMessage('Export canceled.');
                return;
            }

            try {
                const pdfDoc = new PDFDocument();
                const writeStream = fs.createWriteStream(saveUri.fsPath);
                pdfDoc.pipe(writeStream);

                pdfDoc.text(content, { align: 'left' });
                pdfDoc.end();

                writeStream.on('finish', () => {
                    vscode.window.showInformationMessage(`Notebook exported to PDF: ${saveUri.fsPath}`);
                });
            } catch (error) {
                const errorMessage = error instanceof Error ? error.message : String(error);
                vscode.window.showErrorMessage(`Failed to export notebook: ${errorMessage}`);
            }
        });

        this.context.subscriptions.push(exportToPdfDisposable);
    }
}
