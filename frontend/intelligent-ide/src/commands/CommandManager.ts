import * as vscode from 'vscode';
import { registerUserCommands } from './UserCommands';
import { registerCourseCommands } from './CourseCommands';
import { registerChatCommands } from './ChatCommands';
import { CourseTreeDataProvider } from '../views/CourseView';
import { registerQnAView } from '../views/viewManager';
import { ViewType, refreshViews } from '../views/viewManager';
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
        this.registerQnACommands(); // Register QnA commands
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
}
