import * as vscode from 'vscode';
import { courseService } from '../services/CourseService';
import { refreshViews, ViewType, refreshAllViews } from '../views/viewManager';
import { LoginInfo } from '../models/LoginInfo';
import { CourseTreeDataProvider, CourseTreeItem } from '../views/CourseView';
import { DirectoryPermissionType } from '../models/CourseModels';
import * as path from 'path';
import * as os from 'os';
import * as fs from 'fs';
import { getAuthDetails } from '../utils/authUtils';


export function registerCourseCommands(context: vscode.ExtensionContext, treeDataProvider?: CourseTreeDataProvider): void {
    registerCreateCourseCommand(context);
    registerDeleteCourseCommand(context);
    registerOpenFileCommand(context);
    registerDeleteDirectoryCommand(context);
    registerPostDirectoryCommand(context);
    registerUploadFileCommand(context);
    registerDeleteEntryCommand(context);
    registerMoveEntryCommand(context);
    registerJoinCourseCommand(context);
    registerDeleteStudentCommand(context);

    registerGetCollaborativeEntryHistoryCommand(context);
    registerDeleteCollaborativeEntryCommand(context);
    registerGetCollaborativeEntriesCommand(context);
    registerDownloadCollaborativeEntryCommand(context);
    registerUploadCollaborativeFileCommand(context);
    registerJoinCollaborativeSessionCommand(context);
    registerOpenCollaborativeFileCommand(context);
    registerCourseChatCommand(context);
}

/**
 * AI-generated-content
 * tool: GitHub Copilot
 * version: Claude 3.7 Sonnet Thinking
 * usage: I asked Copilot to implement command registration for course creation.
 * Then I use this as a template for command registration for the resting commands.
 */
function registerCreateCourseCommand(context: vscode.ExtensionContext): void {
    const disposable = vscode.commands.registerCommand('intelligent-ide.course.post', async () => {
        try {

            const authDetails = await getAuthDetails(context);
            if (!authDetails) {
                return []; // Auth failed, return empty
            }
            const { token, loginInfo } = authDetails;

            // Check if user has teacher role
            if (loginInfo.role !== 'teacher') {
                const switchToTeacher = await vscode.window.showWarningMessage(
                    'You must be a teacher to create courses. Switch to teacher role?',
                    'Yes',
                    'No'
                );

                if (switchToTeacher === 'Yes') {
                    // Update role to teacher
                    await context.workspaceState.update('loginInfo', {
                        ...loginInfo,
                        role: 'teacher'
                    });
                    refreshAllViews();
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

            refreshViews([ViewType.COURSE]);
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
                const authDetails = await getAuthDetails(context);
                if (!authDetails) {
                    return []; // Auth failed, return empty
                }
                const { token, loginInfo } = authDetails;


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
                        return; // User cancelle
                    }

                    courseId = parseInt(courseIdInput, 10);
                }

                // Proceed with deletion using courseId
                await courseService.deleteCourse(token, courseId);
                vscode.window.showInformationMessage(`Course deleted successfully.`);

                refreshViews([ViewType.COURSE]);

            } catch (error: any) {
                vscode.window.showErrorMessage(`Error deleting course: ${error.message}`);
            }
        }
    );

    context.subscriptions.push(disposable);
}


/**
 * Register command to open a course file with smart temporary file caching
 */
function registerOpenFileCommand(context: vscode.ExtensionContext): void {
    const disposable = vscode.commands.registerCommand('intelligent-ide.course.openFile', async (item: CourseTreeItem) => {
        if (!item.entry || item.isDirectory) {
            return;
        }

        try {
            const authDetails = await getAuthDetails(context);
            if (!authDetails) {
                return []; // Auth failed, return empty
            }
            const { token, loginInfo } = authDetails;
            // Show progress while downloading
            await vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: `Opening ${item.label}...`,
                cancellable: false
            }, async (progress) => {
                try {
                    // Create a stable identifier for this file
                    const fileName = path.basename(item.path || 'file');
                    const entryId = item.entry!.id;
                    const createdAt = item.entry!.created_at;

                    // Create a stable file identifier that doesn't change with each download
                    const fileId = `${entryId}-${createdAt.replace(/[^0-9]/g, '')}`;

                    // Use system temp directory with our extension prefix
                    const tempDir = path.join(os.tmpdir(), 'intelligent-ide');
                    if (!fs.existsSync(tempDir)) {
                        fs.mkdirSync(tempDir, { recursive: true });
                    }

                    // Use a consistent filename based on stable ID
                    const tempFilePath = path.join(tempDir, `${fileId}-${fileName}`);

                    // Check if the file already exists and is recent
                    let shouldDownload = true;
                    if (fs.existsSync(tempFilePath)) {
                        // File exists, show notification that we're using cached version
                        progress.report({ message: 'Using cached version...' });
                        shouldDownload = false;
                    }

                    // Download only if necessary
                    if (shouldDownload) {
                        progress.report({ message: 'Downloading fresh content...' });
                        const fileContent = await courseService.downloadEntry(token, entryId);
                        await vscode.workspace.fs.writeFile(vscode.Uri.file(tempFilePath), fileContent);
                    }

                    // Open the file using vscode.open for all file types
                    const fileUri = vscode.Uri.file(tempFilePath);
                    await vscode.commands.executeCommand('vscode.open', fileUri);

                    // Only show "temporary file" warning first time
                    if (shouldDownload) {
                        const saveAction = await vscode.window.showInformationMessage(
                            'This is a cached file from your course. Save a permanent copy?',
                            'Save As', 'No Thanks'
                        );

                        if (saveAction === 'Save As') {
                            await vscode.commands.executeCommand('workbench.action.files.saveAs');
                        }
                    }

                } catch (error: any) {
                    vscode.window.showErrorMessage(`Error opening file: ${error.message}`);
                }
            });
        } catch (error: any) {
            vscode.window.showErrorMessage(`Error opening file: ${error.message}`);
        }
    });

    context.subscriptions.push(disposable);
}

/**
 * egister command to delete a directory
 */
function registerDeleteDirectoryCommand(context: vscode.ExtensionContext): void {
    const disposable = vscode.commands.registerCommand(
        'intelligent-ide.directory.delete',
        async (directoryItem?: CourseTreeItem) => {
            try {
                const authDetails = await getAuthDetails(context);
                if (!authDetails) {
                    return []; // Auth failed, return empty
                }
                const { token, loginInfo } = authDetails;


                // Use the passed parameter if available, otherwise prompt
                let directoryId: number;

                if (directoryItem && directoryItem.itemId) {
                    // Use the ID from the passed parameter
                    directoryId = typeof directoryItem.itemId === 'number'
                        ? directoryItem.itemId
                        : parseInt(directoryItem.itemId.toString(), 10);

                    // Confirm deletion with directory name if available
                    if (directoryItem.label) {
                        const confirmation = await vscode.window.showWarningMessage(
                            `Are you sure you want to delete the directory "${directoryItem.label}"?`,
                            'Yes', 'No'
                        );

                        if (confirmation !== 'Yes') {
                            return; // User cancelled
                        }
                    }
                } else {
                    // Prompt for directory ID if not provided
                    const directoryIdInput = await vscode.window.showInputBox({
                        prompt: 'Enter the Directory ID to delete',
                        placeHolder: 'e.g., 123',
                        validateInput: (text) => {
                            if (!text) {
                                return 'Directory ID is required';
                            }
                            if (!/^\d+$/.test(text)) {
                                return 'Directory ID must be a number';
                            }
                            return null; // No validation error
                        }
                    });

                    if (!directoryIdInput) {
                        return; // User cancelled
                    }

                    directoryId = parseInt(directoryIdInput, 10);
                }

                // Proceed with deletion
                await courseService.deleteDirectory(token, directoryId);
                vscode.window.showInformationMessage(`Directory deleted successfully.`);

                refreshViews([ViewType.COURSE]);

            } catch (error: any) {
                vscode.window.showErrorMessage(`Error deleting directory: ${error.message}`);
            }
        }
    );

    context.subscriptions.push(disposable);
}

/**
 * Register command to create a new directory
 */
function registerPostDirectoryCommand(context: vscode.ExtensionContext): void {
    const disposable = vscode.commands.registerCommand(
        'intelligent-ide.directory.post',
        async (courseArg?: number | CourseTreeItem) => { // Modified argument
            try {
                const authDetails = await getAuthDetails(context);
                if (!authDetails) {
                    return;
                }
                const { token } = authDetails;

                let courseId: number;

                if (typeof courseArg === 'number') {
                    courseId = courseArg;
                } else if (courseArg && courseArg.itemId && courseArg.type === 'course') {
                    courseId = typeof courseArg.itemId === 'number'
                        ? courseArg.itemId
                        : parseInt(courseArg.itemId.toString(), 10);
                } else {
                    const courseIdInput = await vscode.window.showInputBox({
                        prompt: 'Enter the Course ID for the new directory',
                        placeHolder: 'e.g., 123',
                        validateInput: (text) => {
                            if (!text) { return 'Course ID is required'; }
                            if (!/^\d+$/.test(text)) { return 'Course ID must be a number'; }
                            return null;
                        }
                    });
                    if (!courseIdInput) { return; } // User cancelled
                    courseId = parseInt(courseIdInput, 10);
                }

                if (isNaN(courseId)) {
                    vscode.window.showErrorMessage('Invalid Course ID provided.');
                    return;
                }

                const name = await vscode.window.showInputBox({
                    prompt: 'Enter directory name',
                    placeHolder: 'e.g., Assignments'
                });
                if (!name) { return; } // User cancelled

                // Permissions handling remains commented out as per your existing code
                // ...

                const directoryId = await courseService.postDirectory(token, courseId, name, undefined);
                vscode.window.showInformationMessage(`Directory "${name}" created with ID: ${directoryId}`);
                refreshViews([ViewType.COURSE]);

            } catch (error: any) {
                vscode.window.showErrorMessage(`Error creating directory: ${error.message}`);
            }
        }
    );
    context.subscriptions.push(disposable);
}

/**
 * Register command to delete a directory entry
 */
function registerDeleteEntryCommand(context: vscode.ExtensionContext): void {
    const disposable = vscode.commands.registerCommand(
        'intelligent-ide.entry.delete',
        async (entryItem?: CourseTreeItem) => {
            try {
                const authDetails = await getAuthDetails(context);
                if (!authDetails) {
                    return []; // Auth failed, return empty
                }
                const { token, loginInfo } = authDetails;

                if (!entryItem || !entryItem.entry) {
                    vscode.window.showErrorMessage('No entry selected for deletion');
                    return;
                }

                // Confirm deletion
                const confirmation = await vscode.window.showWarningMessage(
                    `Are you sure you want to delete "${entryItem.label}"?`,
                    'Yes', 'No'
                );

                if (confirmation !== 'Yes') {
                    return;
                }

                // Delete the entry
                await courseService.deleteEntry(token, entryItem.entry.id);
                vscode.window.showInformationMessage(`Entry deleted successfully.`);
                refreshViews([ViewType.COURSE]);

            } catch (error: any) {
                vscode.window.showErrorMessage(`Error deleting entry: ${error.message}`);
            }
        }
    );

    context.subscriptions.push(disposable);
}

/**
 * Register command to upload a file
 */
function registerUploadFileCommand(context: vscode.ExtensionContext): void {
    const disposable = vscode.commands.registerCommand(
        'intelligent-ide.entry.upload',
        async (arg?: CourseTreeItem | { directoryId: number, initialPath?: string }) => { // Modified argument
            try {
                const authDetails = await getAuthDetails(context);
                if (!authDetails) {
                    return;
                }
                const { token } = authDetails;

                let directoryId: number;

                if (arg) {
                    if ((arg as CourseTreeItem).type === 'directory' || (arg as CourseTreeItem).type === 'virtual-directory') {
                        const treeItem = arg as CourseTreeItem;
                        directoryId = typeof treeItem.itemId === 'number'
                            ? treeItem.itemId
                            : parseInt(treeItem.itemId.toString(), 10);
                    } else if ((arg as { directoryId: number }).directoryId !== undefined) {
                        const customArg = arg as { directoryId: number, initialPath?: string };
                        directoryId = customArg.directoryId;
                    } else {
                        // Argument provided but not in expected format, fall through to prompt
                        const directoryIdInput = await vscode.window.showInputBox({
                            prompt: 'Enter directory ID to upload to',
                            placeHolder: 'e.g., 123',
                            validateInput: (text) => /^\d+$/.test(text) ? null : 'Directory ID must be a number'
                        });
                        if (!directoryIdInput) { return; }
                        directoryId = parseInt(directoryIdInput, 10);
                    }
                } else {
                    // No argument, prompt for directory ID
                    const directoryIdInput = await vscode.window.showInputBox({
                        prompt: 'Enter directory ID to upload to',
                        placeHolder: 'e.g., 123',
                        validateInput: (text) => /^\d+$/.test(text) ? null : 'Directory ID must be a number'
                    });
                    if (!directoryIdInput) { return; }
                    directoryId = parseInt(directoryIdInput, 10);
                }

                if (isNaN(directoryId)) {
                    vscode.window.showErrorMessage('Invalid Directory ID provided.');
                    return;
                }

                const fileUris = await vscode.window.showOpenDialog({
                    canSelectFiles: true,
                    canSelectFolders: false,
                    canSelectMany: false,
                    openLabel: 'Select File to Upload'
                });
                if (!fileUris || fileUris.length === 0) { return; }

                const selectedFilename = path.basename(fileUris[0].fsPath);

                let uploadDirectoryPath = await vscode.window.showInputBox({
                    prompt: 'Enter directory path',
                    placeHolder: 'e.g., /folder/ or /',
                    value: '/',
                    validateInput: (input) => {
                        if (!input.startsWith('/')) { return 'Path must start with /'; }
                        return null;
                    }
                });
                if (uploadDirectoryPath === undefined) { return; } // User cancelled

                // Ensure path ends with a slash if it's not just "/"
                if (uploadDirectoryPath !== '/' && !uploadDirectoryPath.endsWith('/')) {
                    uploadDirectoryPath += '/';
                }
                // Append filename
                const finalPathInDirectory = uploadDirectoryPath === '/' ? `/${selectedFilename}` : `${uploadDirectoryPath}${selectedFilename}`;


                await vscode.window.withProgress({
                    location: vscode.ProgressLocation.Notification,
                    title: 'Uploading file...',
                    cancellable: false
                }, async () => {
                    const entryId = await courseService.uploadFile(
                        token,
                        directoryId,
                        finalPathInDirectory,
                        fileUris[0]
                    );
                    vscode.window.showInformationMessage(`File uploaded successfully with ID: ${entryId}. Path: ${finalPathInDirectory}`);
                    refreshViews([ViewType.COURSE]);
                });

            } catch (error: any) {
                vscode.window.showErrorMessage(`Error uploading file: ${error.message}`);
            }
        }
    );
    context.subscriptions.push(disposable);
}

/**
 * Register command to move an entry to a different location
 */
function registerMoveEntryCommand(context: vscode.ExtensionContext): void {
    const disposable = vscode.commands.registerCommand(
        'intelligent-ide.entry.move',
        async (entryItem?: CourseTreeItem) => {
            try {
                const authDetails = await getAuthDetails(context);
                if (!authDetails) {
                    return []; // Auth failed, return empty
                }
                const { token, loginInfo } = authDetails;

                // Determine entry ID from selection or prompt
                let entryId: number;
                let currentPath: string | undefined;

                if (entryItem && entryItem.entry) {
                    entryId = entryItem.entry.id;
                    currentPath = entryItem.path;
                } else {
                    // Prompt for entry ID if not provided
                    const entryIdInput = await vscode.window.showInputBox({
                        prompt: 'Enter the Entry ID to move',
                        placeHolder: 'e.g., 123',
                        validateInput: (text) => {
                            if (!text) {
                                return 'Entry ID is required';
                            }
                            if (!/^\d+$/.test(text)) {
                                return 'Entry ID must be a number';
                            }
                            return null; // No validation error
                        }
                    });

                    if (!entryIdInput) {
                        return; // User cancelled
                    }

                    entryId = parseInt(entryIdInput, 10);
                }

                // Get the filename from the current path if available
                const fileName = currentPath ? path.basename(currentPath) : 'file';

                // Prompt for destination path
                const destinationPath = await vscode.window.showInputBox({
                    prompt: 'Enter destination path (including filename)',
                    placeHolder: 'e.g., /folder/file.txt',
                    value: currentPath || `/${fileName}`,
                    validateInput: (text) => {
                        if (!text) {
                            return 'Destination path is required';
                        }
                        if (!text.startsWith('/')) {
                            return 'Path must start with /';
                        }
                        return null; // No validation error
                    }
                });

                if (!destinationPath) {
                    return; // User cancelled
                }

                // Show progress notification
                await vscode.window.withProgress({
                    location: vscode.ProgressLocation.Notification,
                    title: 'Moving file...',
                    cancellable: false
                }, async (progress) => {
                    // Move the entry
                    await courseService.moveEntry(token, entryId, destinationPath);

                    vscode.window.showInformationMessage(
                        `Entry successfully moved to ${destinationPath}`
                    );
                    refreshViews([ViewType.COURSE]);
                });
            } catch (error: any) {
                vscode.window.showErrorMessage(`Error moving entry: ${error.message}`);
            }
        }
    );

    context.subscriptions.push(disposable);
}


function registerJoinCourseCommand(context: vscode.ExtensionContext): void {
    const disposable = vscode.commands.registerCommand(
        'intelligent-ide.course.join',
        async () => {
            try {
                const authDetails = await getAuthDetails(context);
                if (!authDetails) {
                    return []; // Auth failed, return empty
                }
                const { token, loginInfo } = authDetails;


                const courseIdInput = await vscode.window.showInputBox({
                    prompt: 'Enter the Course ID you want to join',
                    placeHolder: 'e.g., 101',
                    validateInput: (text) => {
                        if (!text) {
                            return 'Course ID is required';
                        }
                        if (!/^\d+$/.test(text)) {
                            return 'Course ID must be a number';
                        }
                        return null;
                    }
                });

                if (!courseIdInput) {
                    return;
                }

                const courseId = parseInt(courseIdInput, 10);

                const student_id = await courseService.joinCourse(token, courseId);
                vscode.window.showInformationMessage(`You successfully joined the course with student ID: ${student_id}.`);

                refreshViews([ViewType.COURSE]);
            } catch (error: any) {
                vscode.window.showErrorMessage(`Failed to join course: ${error.message}`);
            }
        }
    );

    context.subscriptions.push(disposable);
}


function registerDeleteStudentCommand(context: vscode.ExtensionContext): void {
    const disposable = vscode.commands.registerCommand(
        'intelligent-ide.student.delete',
        async (studentItem?: CourseTreeItem) => {
            try {
                const authDetails = await getAuthDetails(context);
                if (!authDetails) {
                    return []; // Auth failed, return empty
                }
                const { token, loginInfo } = authDetails;

                // Check if user has teacher role
                if (loginInfo.role !== 'teacher') {
                    vscode.window.showErrorMessage('Only teachers can remove students.');
                    return;
                }

                let studentId: number;
                let courseId: number;

                // If student item was clicked in the tree view
                if (studentItem && studentItem.type === 'student') {
                    studentId = typeof studentItem.itemId === 'number'
                        ? studentItem.itemId
                        : parseInt(studentItem.itemId.toString(), 10);

                    courseId = typeof studentItem.parentId === 'number'
                        ? studentItem.parentId
                        : parseInt(studentItem.parentId!.toString(), 10);

                    // Confirm deletion
                    const confirmation = await vscode.window.showWarningMessage(
                        `Are you sure you want to remove student "${studentItem.label}" from the course?`,
                        'Yes', 'No'
                    );

                    if (confirmation !== 'Yes') {
                        return;
                    }
                } else {
                    // If command was invoked without a student selected, prompt for course ID
                    const courseIdInput = await vscode.window.showInputBox({
                        prompt: 'Enter the Course ID to manage students',
                        placeHolder: 'e.g., 101',
                        validateInput: (text) => {
                            if (!text) { return 'Course ID is required'; }
                            if (!/^\d+$/.test(text)) { return 'Course ID must be a number'; }
                            return null;
                        }
                    });

                    if (!courseIdInput) { return; }
                    courseId = parseInt(courseIdInput, 10);

                    // Get student list and show picker
                    try {
                        const students = await courseService.getStudents(token, courseId);

                        if (!students || students.length === 0) {
                            vscode.window.showInformationMessage('No students enrolled in this course.');
                            return;
                        }

                        const studentOption = await vscode.window.showQuickPick(
                            students.map(student => ({
                                label: `${student.username} (${student.email})`,
                                id: student.id
                            })),
                            { placeHolder: 'Select student to remove' }
                        );

                        if (!studentOption) { return; }
                        studentId = parseInt(studentOption.id, 10);

                    } catch (error) {
                        // Fallback to manual ID entry
                        const studentIdInput = await vscode.window.showInputBox({
                            prompt: 'Enter the student ID you want to remove',
                            placeHolder: 'e.g., 101',
                            validateInput: (text) => {
                                if (!text) { return 'Student ID is required'; }
                                if (!/^\d+$/.test(text)) { return 'Student ID must be a number'; }
                                return null;
                            }
                        });

                        if (!studentIdInput) { return; }
                        studentId = parseInt(studentIdInput, 10);
                    }
                }

                // Delete the student
                await courseService.deleteStudent(token, courseId, studentId);
                vscode.window.showInformationMessage(`Student removed from the course successfully`);

                // Refresh the tree view
                refreshViews([ViewType.COURSE]);

            } catch (error: any) {
                vscode.window.showErrorMessage(`Failed to remove student: ${error.message}`);
            }
        }
    );

    context.subscriptions.push(disposable);
}


function registerGetCollaborativeEntryHistoryCommand(context: vscode.ExtensionContext): void {
    const disposable = vscode.commands.registerCommand(
        'intelligent-ide.collaborative.history',
        async (entryItem?: CourseTreeItem) => {
            try {
                const authDetails = await getAuthDetails(context);
                if (!authDetails) {
                    return []; // Auth failed, return empty
                }
                const { token, loginInfo } = authDetails;

                if (!entryItem || !entryItem.collaborativeEntry) {
                    vscode.window.showErrorMessage('No entry selected for deletion');
                    return;
                }

                const history = await courseService.CollaborativeHistory(
                    token,
                    entryItem.collaborativeEntry.course_id, entryItem.collaborativeEntry.id
                );

                vscode.window.showInformationMessage(`Edit history: ${JSON.stringify(history)}`);
            } catch (error: any) {
                vscode.window.showErrorMessage(`Error fetching edit history: ${error.message}`);
            }
        }
    );

    context.subscriptions.push(disposable);
}


function registerDeleteCollaborativeEntryCommand(context: vscode.ExtensionContext): void {
    const disposable = vscode.commands.registerCommand(
        'intelligent-ide.collaborative.delete',
        async (entryItem?: CourseTreeItem) => {
   
                try {
                    const authDetails = await getAuthDetails(context);
                    if (!authDetails) {
                        return []; // Auth failed, return empty
                    }
                    const { token, loginInfo } = authDetails;
    
                    if (!entryItem || !entryItem.collaborativeEntry) {
                        vscode.window.showErrorMessage('No entry selected for deletion');
                        return;
                    }
    
                    // Confirm deletion
                    const confirmation = await vscode.window.showWarningMessage(
                        `Are you sure you want to delete "${entryItem.label}"?`,
                        'Yes', 'No'
                    );
    
                    if (confirmation !== 'Yes') {
                        return;
                    }
    
                    // Delete the entry
                    await courseService.deleteCollaborativeEntry(token, entryItem.collaborativeEntry.course_id, entryItem.collaborativeEntry.id);
                    vscode.window.showInformationMessage(`Entry deleted successfully.`);
                    refreshViews([ViewType.COURSE]);
    
                } catch (error: any) {
                    vscode.window.showErrorMessage(`Error deleting entry: ${error.message}`);
                }
        }
    );

    context.subscriptions.push(disposable);
}



function registerGetCollaborativeEntriesCommand(context: vscode.ExtensionContext): void {
    const disposable = vscode.commands.registerCommand(
        'intelligent-ide.collaborative.list',
        async (entryItem?: CourseTreeItem) => {
            try {
                const authDetails = await getAuthDetails(context);
                if (!authDetails) {
                    return []; // Auth failed, return empty
                }
                const { token, loginInfo } = authDetails;

                // if (!entryItem || !entryItem.itemId) {
                //     vscode.window.showErrorMessage('No directory selected for listing entries.');
                //     return;
                // }


                let courseId: number;

                if (entryItem && entryItem.itemId && entryItem.type === 'course') {
                    courseId = typeof entryItem.itemId === 'number'
                        ? entryItem.itemId
                        : parseInt(entryItem.itemId.toString(), 10);
                } else {
                    // Prompt for course ID
                    const courseIdInput = await vscode.window.showInputBox({
                        prompt: 'Enter the Course ID for the new directory',
                        placeHolder: 'e.g., 123',
                        validateInput: (text) => {
                            if (!text) {
                                return 'Course ID is required';
                            }
                            if (!/^\d+$/.test(text)) {
                                return 'Course ID must be a number';
                            }
                            return null;
                        }
                    });

                    if (!courseIdInput) {
                        return; // User cancelled
                    }

                    courseId = parseInt(courseIdInput, 10);
                }

                
                const entries = await courseService.getCollaborativeDirectories(
                    token,
                    courseId
                );

                vscode.window.showInformationMessage(`Collaborative entries: ${JSON.stringify(entries)}`);
            } catch (error: any) {
                vscode.window.showErrorMessage(`Error fetching collaborative entries: ${error.message}`);
            }
        }
    );

    context.subscriptions.push(disposable);
}



function registerDownloadCollaborativeEntryCommand(context: vscode.ExtensionContext): void {
    const disposable = vscode.commands.registerCommand(
        'intelligent-ide.collaborative.download',
        async (entryItem?: CourseTreeItem) => {
            try {
                const authDetails = await getAuthDetails(context);
                if (!authDetails) {
                    return []; // Auth failed, return empty
                }
                const { token, loginInfo } = authDetails;

                if (!entryItem || !entryItem.collaborativeEntry) {
                    vscode.window.showErrorMessage('No entry selected for download.');
                    return;
                }


                let courseId: number;

                if (entryItem && entryItem.itemId && entryItem.type === 'course') {
                    courseId = typeof entryItem.itemId === 'number'
                        ? entryItem.itemId
                        : parseInt(entryItem.itemId.toString(), 10);
                } else {
                    // Prompt for course ID

                }



                const fileData = await courseService.downloadCollaborativeEntry(
                    token,
                    entryItem.collaborativeEntry.course_id, entryItem.collaborativeEntry.id
                );
                console.log(entryItem.collaborativeEntry.course_id, entryItem.collaborativeEntry.id);
                const saveUri = await vscode.window.showSaveDialog({
                    saveLabel: 'Save File',
                    title: 'Save Downloaded File',
                    defaultUri: vscode.Uri.file(entryItem.label)
                });

                if (!saveUri) {
                    return;
                }

                await vscode.workspace.fs.writeFile(saveUri, fileData);
                vscode.window.showInformationMessage('File downloaded successfully!');
            } catch (error: any) {
                vscode.window.showErrorMessage(`Error downloading entry: ${error.message}`);
            }
        }
    );

    context.subscriptions.push(disposable);
}

function registerUploadCollaborativeFileCommand(context: vscode.ExtensionContext): void {
    const disposable = vscode.commands.registerCommand(
        'intelligent-ide.collaborative.upload',
        async (directoryItem?: CourseTreeItem) => {
            try {
                const authDetails = await getAuthDetails(context);
                if (!authDetails) {
                    return []; // Auth failed, return empty
                }
                const { token, loginInfo } = authDetails;
                if (!loginInfo) {
                    vscode.window.showErrorMessage('You must log in to create a course.');
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
                        refreshViews([ViewType.COURSE]);
                    } else {
                        return; // User cancelled
                    }
                }
                

                
                // Get directory ID from selected item or prompt
                let directoryId: number;
                console.log(directoryItem?.parentId);
                if (directoryItem && directoryItem.parentId &&
                    (directoryItem.type === 'collaborative-folder' || directoryItem.type === 'virtual-directory')) {
                    directoryId = typeof directoryItem.parentId === 'number'
                        ? directoryItem.parentId
                        : parseInt(directoryItem.parentId.toString(), 10);
                } else {
                    // Prompt for directory ID
                    const directoryIdInput = await vscode.window.showInputBox({
                        prompt: 'Enter collaborative course ID to upload to',
                        placeHolder: 'e.g., 123',
                        validateInput: (text) => {
                            return /^\d+$/.test(text) ? null : 'Course ID must be a number';
                        }
                    });

                    if (!directoryIdInput) {
                        return;
                    }

                    directoryId = parseInt(directoryIdInput, 10);
                }

                // Open file picker dialog
                const fileUris = await vscode.window.showOpenDialog({
                    canSelectFiles: true,
                    canSelectFolders: false,
                    canSelectMany: false,
                    openLabel: 'Select File to Upload'
                });

                if (!fileUris || fileUris.length === 0) {
                    return;
                }

                // Show progress notification
                vscode.window.withProgress({
                    location: vscode.ProgressLocation.Notification,
                    title: 'Uploading collaborative file...',
                    cancellable: false
                }, async (progress) => {
                    // Upload the selected file using the modified directoryPath
                    const entryId = await courseService.uploadCollaborativeFile(
                        token,
                        directoryId, // Using the directoryPath directly
                        fileUris[0]
                    );

                    vscode.window.showInformationMessage(`Collaborative file uploaded successfully with ID: ${entryId}`);
                    // Refresh the tree view
                    refreshViews([ViewType.COURSE]);
                });

            } catch (error: any) {
                vscode.window.showErrorMessage(`Error uploading collaborative file: ${error.message}`);
            }
        }
    );

    context.subscriptions.push(disposable);
}

function registerOpenCollaborativeFileCommand(context: vscode.ExtensionContext): void {
    const disposable = vscode.commands.registerCommand(
        'intelligent-ide.collaborative.openFile',
        async (entryItem?: CourseTreeItem) => {
            if (!entryItem || !entryItem.collaborativeEntry) {
                vscode.window.showErrorMessage('No collaborative file selected for opening.');
                return;
            }

            try {
                const authDetails = await getAuthDetails(context);
                if (!authDetails) {
                    vscode.window.showErrorMessage('Authentication failed. Please log in again.');
                    return;
                }
                const { token } = authDetails;

                const courseId = entryItem.parentId as number;
                const entryId = entryItem.collaborativeEntry.id;

                // Show progress while downloading
                await vscode.window.withProgress({
                    location: vscode.ProgressLocation.Notification,
                    title: `Opening ${entryItem.label}...`,
                    cancellable: false
                }, async (progress) => {
                    try {
                        // Download the file content
                        const fileData = await courseService.downloadCollaborativeEntry(token, courseId, entryId);

                        // Create a temporary file path
                        const tempDir = path.join(os.tmpdir(), 'intelligent-ide');
                        if (!fs.existsSync(tempDir)) {
                            fs.mkdirSync(tempDir, { recursive: true });
                        }
                        const tempFilePath = path.join(tempDir, entryItem.collaborativeEntry?.file_name || 'collaborative_'+courseId+'_'+entryId);

                        // Write the file content to the temporary file
                        await vscode.workspace.fs.writeFile(vscode.Uri.file(tempFilePath), fileData);

                        // Open the file in VS Code
                        const fileUri = vscode.Uri.file(tempFilePath);
                        await vscode.commands.executeCommand('vscode.open', fileUri);
                    } catch (error: any) {
                        vscode.window.showErrorMessage(`Error opening file: ${error.message}`);
                    }
                });
            } catch (error: any) {
                vscode.window.showErrorMessage(`Error opening collaborative file: ${error.message}`);
            }
        }
    );

    context.subscriptions.push(disposable);
}

function registerJoinCollaborativeSessionCommand(context: vscode.ExtensionContext): void {
    const disposable = vscode.commands.registerCommand(
        'intelligent-ide.collaborative.join',
        async (entryItem?: CourseTreeItem) => {
            try {
                const authDetails = await getAuthDetails(context);
                if (!authDetails) {
                    vscode.window.showErrorMessage('Authentication failed. Please log in again.');
                    return;
                }
                const { token } = authDetails;

                // // Prompt for course ID
                // const courseIdInput = await vscode.window.showInputBox({
                //     prompt: 'Enter the Course ID for the collaborative session',
                //     placeHolder: 'e.g., 101',
                //     validateInput: (text) => {
                //         if (!text) {
                //             return 'Course ID is required';
                //         }
                //         if (!/^\d+$/.test(text)) {
                //             return 'Course ID must be a number';
                //         }
                //         return null;
                //     }
                // });

                // if (!courseIdInput) {
                //     return; // User cancelled
                // }

                // const courseId = parseInt(courseIdInput, 10);

                // // Prompt for collaborative entry ID
                // const entryIdInput = await vscode.window.showInputBox({
                //     prompt: 'Enter the Collaborative Entry ID',
                //     placeHolder: 'e.g., 202',
                //     validateInput: (text) => {
                //         if (!text) {
                //             return 'Collaborative Entry ID is required';
                //         }
                //         if (!/^\d+$/.test(text)) {
                //             return 'Collaborative Entry ID must be a number';
                //         }
                //         return null;
                //     }
                // });

                // if (!entryIdInput) {
                //     return; // User cancelled
                // }

                // const entryId = parseInt(entryIdInput, 10);

                // Join the collaborative session
                if (!entryItem || !entryItem.collaborativeEntry) {
                    vscode.window.showErrorMessage('Invalid collaborative entry. Please select a valid entry.');
                    return;
                }
                const sessionDetails = await courseService.joinCollaborativeSession(token, entryItem.collaborativeEntry.course_id, entryItem.collaborativeEntry.id);

                // if (sessionDetails) {
                //     vscode.window.showInformationMessage(
                //         `Successfully joined collaborative session for entry ID: ${entryItem.collaborativeEntry.course_id} in course ID: ${entryItem.collaborativeEntry.id}.`
                //     );
                // } else {
                //     vscode.window.showErrorMessage('Failed to join collaborative session.');
                // }

                // Optionally refresh views or perform additional actions
                refreshViews([ViewType.COURSE]);
            } catch (error: any) {
                vscode.window.showErrorMessage(`Error joining collaborative session: ${error.message}`);
            }
        }
    );

    context.subscriptions.push(disposable);
}

export function registerCourseChatCommand(context: vscode.ExtensionContext): void {
    const disposable = vscode.commands.registerCommand(
        'intelligent-ide.course.chat',
        async (courseArg?: number | CourseTreeItem) => {
            try {
                // 获取认证信息
                const authDetails = await getAuthDetails(context);
                if (!authDetails) {
                    return;
                }
                const { token } = authDetails;

                let courseId: number;

                if (typeof courseArg === 'number') {
                    courseId = courseArg;
                } else if (courseArg && courseArg.itemId && courseArg.type === 'course') {
                    courseId = typeof courseArg.itemId === 'number'
                        ? courseArg.itemId
                        : parseInt(courseArg.itemId.toString(), 10);
                } else {
                    const courseIdInput = await vscode.window.showInputBox({
                        prompt: 'Enter the Course ID for the new directory',
                        placeHolder: 'e.g., 123',
                        validateInput: (text) => {
                            if (!text) { return 'Course ID is required'; }
                            if (!/^\d+$/.test(text)) { return 'Course ID must be a number'; }
                            return null;
                        }
                    });
                    if (!courseIdInput) { return; } // User cancelled
                    courseId = parseInt(courseIdInput, 10);
                }

                if (isNaN(courseId)) {
                    vscode.window.showErrorMessage('Invalid Course ID provided.');
                    return;
                }


                // 打开聊天界面
                courseService.openCourseChatWebView(context, token, parseInt(courseId.toString(), 10));
            } catch (error: any) {
                vscode.window.showErrorMessage(`Failed to join course chat: ${error.message}`);
            }
        }
    );

    context.subscriptions.push(disposable);
}




// 🚫🚫🚫 WARNING 🚫🚫🚫
// +-----------------------------------------+
// | openfile command已经涵盖了这一部份，请不要重复实现 |
// +-----------------------------------------+
// 🚫🚫🚫 WARNING 🚫🚫🚫

// export function registerDownloadEntryCommand(context: vscode.ExtensionContext): void {
//     const disposable = vscode.commands.registerCommand(
//         'intelligent-ide.entry.download',
//         async (treeItem: CourseTreeItem) => {
//             try {
//                 // assuming courseService is already imported and available
//                 const token = await context.secrets.get('authToken');
//                 if (!token) {
//                     vscode.window.showErrorMessage('Authentication token not found. Please log in again.');
//                     console.error('Error: Authentication token not found.');
//                     return;
//                 }
//                 console.log('Authentication token retrieved successfully.');

//                 // Check if the treeItem is valid and of type 'entry'
//                 if (!treeItem || treeItem.type !== 'entry' || treeItem.isDirectory) {
//                     vscode.window.showErrorMessage('Invalid file entry selected for download.');
//                     console.error('Error: Invalid file entry selected.');
//                     return;
//                 }

//                 // Check if the entry ID is valid
//                 const entryId = typeof treeItem.itemId === 'number'
//                     ? treeItem.itemId
//                     : parseInt(treeItem.itemId.toString(), 10);

//                 if (isNaN(entryId)) {
//                     vscode.window.showErrorMessage('Invalid entry ID.');
//                     console.error('Error: Invalid entry ID:', treeItem.itemId);
//                     return;
//                 }


//                 const fileData = await courseService.downloadEntry(token, entryId);

//                 const saveUri = await vscode.window.showSaveDialog({
//                     saveLabel: 'Save File',
//                     title: 'Save Downloaded File',
//                     defaultUri: vscode.Uri.file(treeItem.label)
//                 });

//                 if (!saveUri) {
//                     console.log('Save dialog cancelled by user.');
//                     return;
//                 }
//                 await vscode.workspace.fs.writeFile(saveUri, fileData);
//                 vscode.window.showInformationMessage('File downloaded successfully!');


//             } catch (error: any) {
//                 vscode.window.showErrorMessage(`Failed to download file: ${error.message}`);
//                 console.error('Error during file download:', error.message, error.stack);
//             }
//         }
//     );

//     context.subscriptions.push(disposable);
// }


