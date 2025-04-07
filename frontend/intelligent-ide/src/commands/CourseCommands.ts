import * as vscode from 'vscode';
import { courseService } from '../services/CourseService';
import { ICourse } from '../models/CourseModels';
import { displayUserView } from '../views/userView';
import { LoginInfo } from '../models/LoginInfo';
import { CourseListCache } from '../models/CourseModels';

/**
 * Register all course-related commands
 */
export function registerCourseCommands(context: vscode.ExtensionContext): void {
    registerCreateCourseCommand(context);
    registerDeleteCourseCommand(context);
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
                    displayUserView(context);
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

        } catch (error: any) {
            vscode.window.showErrorMessage(`Error creating course: ${error.message}`);
        }
    });

    context.subscriptions.push(disposable);
}

/**
 * Register command to delete a course
 */
function registerDeleteCourseCommand(context: vscode.ExtensionContext): void {
    const disposable = vscode.commands.registerCommand('intelligent-ide.course.delete', async () => {
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

            // Get the course list from cache
            const courseListCache = context.globalState.get('courseListCache') as CourseListCache;
            const teacherCourses = courseListCache?.teacher || [];

            // Show the list of courses to help the user identify course IDs
            if (teacherCourses.length > 0) {
                // Create a formatted list of courses to show in the message
                const courseListFormatted = teacherCourses.map(course =>
                    `ID: ${course.id} | ${course.name}`
                ).join('\n');

                // Show the course list in an information message
                await vscode.window.showInformationMessage(
                    `Your courses:\n${courseListFormatted}`,
                    { modal: true }
                );
            } else {
                vscode.window.showInformationMessage(
                    'You have no courses to delete. Use the "List Courses" command to refresh.'
                );
                return;
            }

            // Prompt for course ID
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

            const courseId = parseInt(courseIdInput, 10);

            // Try to find the course in the cache to show its name
            const courseToDelete = teacherCourses.find(course => course.id === courseId);
            const courseName = courseToDelete ? courseToDelete.name : `Course ID: ${courseId}`;

            // Confirm deletion
            const confirmation = await vscode.window.showWarningMessage(
                `Are you sure you want to delete "${courseName}"? This action cannot be undone.`,
                'Yes',
                'No'
            );

            if (confirmation !== 'Yes') {
                return; // User cancelled
            }

            // Delete course
            await courseService.deleteCourse(token, courseId);
            vscode.window.showInformationMessage(`Course "${courseName}" deleted successfully.`);

            // Update course list cache if the course was in our cache
            if (courseToDelete && courseListCache) {
                courseListCache.teacher = courseListCache.teacher.filter(
                    course => course.id !== courseId
                );
                courseListCache.lastUpdated = new Date().toISOString();
                await context.globalState.update('courseListCache', courseListCache);
            }
        } catch (error: any) {
            vscode.window.showErrorMessage(`Error deleting course: ${error.message}`);
        }
    });

    context.subscriptions.push(disposable);
}

/**
 * Helper to prompt for role selection
 */
async function promptForRole(): Promise<string | undefined> {
    return vscode.window.showQuickPick(
        ['student', 'teacher'],
        {
            placeHolder: 'Select your role',
            title: 'Select Role'
        }
    );
}