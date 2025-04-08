import * as vscode from 'vscode';
import { courseService } from '../services/CourseService';
import { refreshLoginView } from '../views/userView';
import { LoginInfo } from '../models/LoginInfo';
import { CourseTreeDataProvider, CourseTreeItem } from '../views/CourseView';

/**
 * Register all course-related commands
 */
export function registerCourseCommands(context: vscode.ExtensionContext, treeDataProvider?: CourseTreeDataProvider): void {
    registerCreateCourseCommand(context);
    registerDeleteCourseCommand(context);
    registerRefreshCommand(context, treeDataProvider);
    registerOpenFileCommand(context);
}

/**
 * Register command to create a new course
 */
function registerCreateCourseCommand(context: vscode.ExtensionContext): void {
    const disposable = vscode.commands.registerCommand('intelligent-ide.course.post', async () => {
        try {
            // Get login info from global state
            const loginInfo: LoginInfo | undefined = context.globalState.get('loginInfo');
            if (!loginInfo) {
                vscode.window.showErrorMessage('You must log in to create a course.');
                return;
            }

            // Get token from secure storage
            const token = await context.secrets.get('authToken');
            if (!token) {
                vscode.window.showErrorMessage('Authentication token not found. Please log in again.');
                return;
            }

            // Check if user has teacher role
            if (loginInfo.role !== 'teacher') {
                const switchToTeacher = await vscode.window.showWarningMessage(
                    'You must be a teacher to create courses. Switch to teacher role?',
                    'Yes',
                    'No'
                );

                if (switchToTeacher === 'Yes') {
                    // Update role to teacher
                    await context.globalState.update('loginInfo', {
                        ...loginInfo,
                        role: 'teacher'
                    });
                    refreshLoginView(context);
                } else {
                    return; // User cancelled
                }
            }

            // Prompt for course name
            const name = await vscode.window.showInputBox({
                prompt: 'Enter course name',
                placeHolder: 'e.g., Introduction to Computer Science'
            });
            if (!name) {
                return; // User cancelled
            }

            // Prompt for course description
            const description = await vscode.window.showInputBox({
                prompt: 'Enter course description',
                placeHolder: 'e.g., Learn the fundamentals of computer science'
            });
            if (!description) {
                return; // User cancelled
            }
            await courseService.createCourse(token, name, description);
            vscode.window.showInformationMessage(`Course "${name}" created successfully.`);
            await vscode.commands.executeCommand('intelligent-ide.course.refresh');

        } catch (error: any) {
            vscode.window.showErrorMessage(`Error creating course: ${error.message}`);
        }
    });

    context.subscriptions.push(disposable);
}

/**
 * Register command to delete a cours
 */
function registerDeleteCourseCommand(context: vscode.ExtensionContext): void {
    const disposable = vscode.commands.registerCommand(
        'intelligent-ide.course.delete',
        async (courseItem?: { itemId?: number | string, label?: string }) => {
            try {
                // Get login info from global state
                const loginInfo: LoginInfo | undefined = context.globalState.get('loginInfo');
                if (!loginInfo) {
                    vscode.window.showErrorMessage('You must log in to delete a course.');
                    return;
                }

                // Get token from secure storage
                const token = await context.secrets.get('authToken');
                if (!token) {
                    vscode.window.showErrorMessage('Authentication token not found. Please log in again.');
                    return;
                }

                // Check if user has teacher role
                if (loginInfo.role !== 'teacher') {
                    vscode.window.showErrorMessage('Only teachers can delete courses.');
                    return;
                }

                // Use the passed parameter if available, otherwise prompt
                let courseId: number;

                if (courseItem && courseItem.itemId) {
                    // Use the ID from the passed parameter
                    courseId = typeof courseItem.itemId === 'number'
                        ? courseItem.itemId
                        : parseInt(courseItem.itemId.toString(), 10);

                    // Confirm deletion with course name if available
                    if (courseItem.label) {
                        const confirmation = await vscode.window.showWarningMessage(
                            `Are you sure you want to delete the course "${courseItem.label}"?`,
                            'Yes', 'No'
                        );

                        if (confirmation !== 'Yes') {
                            return; // User cancelled
                        }
                    }
                } else {
                    // Prompt for course ID if not provided
                    const courseIdInput = await vscode.window.showInputBox({
                        prompt: 'Enter the Course ID to delete',
                        placeHolder: 'e.g., 123',
                        validateInput: (text) => {
                            if (!text) {
                                return 'Course ID is required';
                            }
                            if (!/^\d+$/.test(text)) {
                                return 'Course ID must be a number';
                            }
                            return null; // No validation error
                        }
                    });

                    if (!courseIdInput) {
                        return; // User cancelled
                    }

                    courseId = parseInt(courseIdInput, 10);
                }

                // Proceed with deletion using courseId
                await courseService.deleteCourse(token, courseId);
                vscode.window.showInformationMessage(`Course deleted successfully.`);
                await vscode.commands.executeCommand('intelligent-ide.course.refresh');

            } catch (error: any) {
                vscode.window.showErrorMessage(`Error deleting course: ${error.message}`);
            }
        }
    );

    context.subscriptions.push(disposable);
}

/**
 * Register command to refresh the course tree view
 */
function registerRefreshCommand(context: vscode.ExtensionContext, treeDataProvider?: CourseTreeDataProvider): void {
    const disposable = vscode.commands.registerCommand('intelligent-ide.course.refresh', () => {
        if (treeDataProvider) {
            treeDataProvider.refresh();
        }
    });

    context.subscriptions.push(disposable);
}

/**
 * Register command to open a course file
 */
function registerOpenFileCommand(context: vscode.ExtensionContext): void {
    const disposable = vscode.commands.registerCommand('intelligent-ide.course.openFile', async (item: CourseTreeItem) => {
        if (!item.entry || item.isDirectory) {
            return;
        }

        try {
            const token = await context.secrets.get('authToken');
            if (!token) {
                vscode.window.showErrorMessage('Authentication token not found. Please log in again.');
                return;
            }

            // Here you would implement file downloading and opening
            vscode.window.showInformationMessage(`File would be downloaded: ${item.path}`);

            //TODO: Implement file download and open logic
            // Example implementation for downloading and opening the file
            // const fileContent = await courseService.downloadEntry(token, item.entry.id);
            // ... create a temporary file and open it
        } catch (error: any) {
            vscode.window.showErrorMessage(`Error opening file: ${error.message}`);
        }
    });

    context.subscriptions.push(disposable);
}

