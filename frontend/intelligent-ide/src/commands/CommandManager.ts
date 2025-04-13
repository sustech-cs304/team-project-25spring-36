import * as vscode from 'vscode';
import { registerUserCommands } from './UserCommands';
import { registerCourseCommands } from './CourseCommands';
import { CourseTreeDataProvider } from '../views/CourseView';
import { ViewType, refreshViews } from '../views/viewManager';

/**
 * Centralized command registration manager
 * Handles all command registrations in the extensio
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
    }

    /**
     * Register global/utility commands
     */
    private registerGlobalCommands(): void {
        // Register the global view refresh command
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
}