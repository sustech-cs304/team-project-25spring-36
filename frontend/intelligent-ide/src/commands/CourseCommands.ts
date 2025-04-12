import * as vscode from 'vscode';
import { courseService } from '../services/CourseService';
import { refreshLoginView } from '../views/userView';
import { LoginInfo } from '../models/LoginInfo';
import { CourseTreeDataProvider, CourseTreeItem } from '../views/CourseView';
import { DirectoryPermissionType } from '../models/CourseModels';
import * as path from 'path';
import * as os from 'os';
import * as fs from 'fs';


export function registerCourseCommands(context: vscode.ExtensionContext, treeDataProvider?: CourseTreeDataProvider): void {
    registerCreateCourseCommand(context);
    registerDeleteCourseCommand(context);
    registerRefreshCommand(context, treeDataProvider);
    registerOpenFileCommand(context);
    registerDeleteDirectoryCommand(context);
    registerPostDirectoryCommand(context);
    registerUploadFileCommand(context);
    registerDeleteEntryCommand(context);
    registerMoveEntryCommand(context);
    registerJoinCourseCommand(context);
    registerDownloadEntryCommand(context);
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
                        return; // User cancelle
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

            // Show progress while downloadin
            await vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: `Downloading ${item.label}...`,
                cancellable: false
            }, async (progress) => {
                try {
                    // Create a unique identifier for this file
                    const fileId = `${item.entry!.id}-${Date.now()}`;
                    const fileName = path.basename(item.path || 'file');

                    // Use system temp directory with our extension prefix
                    const tempDir = path.join(os.tmpdir(), 'intelligent-ide');
                    if (!fs.existsSync(tempDir)) {
                        fs.mkdirSync(tempDir, { recursive: true });
                    }

                    // Use a unique filename to avoid collisions
                    const tempFilePath = path.join(tempDir, `${fileId}-${fileName}`);

                    // Always download fresh content
                    const fileContent = await courseService.downloadEntry(token, item.entry!.id);
                    await vscode.workspace.fs.writeFile(vscode.Uri.file(tempFilePath), fileContent);

                    // Open file with warning about being temporary
                    const document = await vscode.workspace.openTextDocument(tempFilePath);
                    await vscode.window.showTextDocument(document);

                    // Prompt to save permanently
                    const saveAction = await vscode.window.showInformationMessage(
                        'This is a temporary file that may be deleted. Save a permanent copy?',
                        'Save As', 'No Thanks'
                    );

                    if (saveAction === 'Save As') {
                        await vscode.commands.executeCommand('workbench.action.files.saveAs');
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
 * Register command to delete a directory
 */
function registerDeleteDirectoryCommand(context: vscode.ExtensionContext): void {
    const disposable = vscode.commands.registerCommand(
        'intelligent-ide.directory.delete',
        async (directoryItem?: CourseTreeItem) => {
            try {
                // Get login info and token
                const loginInfo: LoginInfo | undefined = context.globalState.get('loginInfo');
                if (!loginInfo) {
                    vscode.window.showErrorMessage('You must log in to delete a directory.');
                    return;
                }

                const token = await context.secrets.get('authToken');
                if (!token) {
                    vscode.window.showErrorMessage('Authentication token not found. Please log in again.');
                    return;
                }

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
                await vscode.commands.executeCommand('intelligent-ide.course.refresh');

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
        async (courseItem?: CourseTreeItem) => {
            try {
                // Get login info and token
                const loginInfo: LoginInfo | undefined = context.globalState.get('loginInfo');
                if (!loginInfo) {
                    vscode.window.showErrorMessage('You must log in to create a directory.');
                    return;
                }

                const token = await context.secrets.get('authToken');
                if (!token) {
                    vscode.window.showErrorMessage('Authentication token not found. Please log in again.');
                    return;
                }

                // Determine course ID
                let courseId: number;

                if (courseItem && courseItem.itemId && courseItem.type === 'course') {
                    courseId = typeof courseItem.itemId === 'number'
                        ? courseItem.itemId
                        : parseInt(courseItem.itemId.toString(), 10);
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

                // Prompt for directory name
                const name = await vscode.window.showInputBox({
                    prompt: 'Enter directory name',
                    placeHolder: 'e.g., Assignments'
                });

                if (!name) {
                    return; // User cancelled
                }

                // ============================================================
                // Permission handling is temporarily disabled until requirements are clearer
                // The following code is commented out:
                /*
                // Handle permissions - first ask if user wants to set permissions
                const setPermissions = await vscode.window.showQuickPick(
                    ['Yes', 'No'],
                    { placeHolder: 'Do you want to set permissions for this directory?' }
                );

                // Initialize permissions as undefined initially
                let permissions: Record<string, DirectoryPermissionType[]> | undefined = undefined;

                if (setPermissions === 'Yes') {
                    permissions = {};

                    // Ask for the path to set permissions for
                    const path = await vscode.window.showInputBox({
                        prompt: 'Enter path to set permissions for',
                        placeHolder: 'e.g., /path/to/directory'
                    });

                    if (path) {
                        // Show permission options with dependencies
                        const permissionOptions = [
                            { label: DirectoryPermissionType.READ, picked: false },
                            { label: DirectoryPermissionType.WRITE, picked: false },
                            { label: DirectoryPermissionType.UPLOAD, picked: false },
                            { label: DirectoryPermissionType.DELETE, picked: false }
                        ];

                        const selectedPermissions = await vscode.window.showQuickPick(
                            permissionOptions.map(p => p.label),
                            {
                                canPickMany: true,
                                placeHolder: 'Select permissions (READ is implied by WRITE and UPLOAD)'
                            }
                        );

                        if (selectedPermissions && selectedPermissions.length > 0) {
                            // Process permissions with dependencies
                            const finalPermissions: DirectoryPermissionType[] = [];

                            // Add base permissions
                            if (selectedPermissions.includes(DirectoryPermissionType.READ)) {
                                finalPermissions.push(DirectoryPermissionType.READ);
                            }

                            // WRITE implies READ
                            if (selectedPermissions.includes(DirectoryPermissionType.WRITE)) {
                                if (!finalPermissions.includes(DirectoryPermissionType.READ)) {
                                    finalPermissions.push(DirectoryPermissionType.READ);
                                }
                                finalPermissions.push(DirectoryPermissionType.WRITE);
                            }

                            // UPLOAD implies READ
                            if (selectedPermissions.includes(DirectoryPermissionType.UPLOAD)) {
                                if (!finalPermissions.includes(DirectoryPermissionType.READ)) {
                                    finalPermissions.push(DirectoryPermissionType.READ);
                                }
                                finalPermissions.push(DirectoryPermissionType.UPLOAD);
                            }

                            // DELETE highest permission
                            if (selectedPermissions.includes(DirectoryPermissionType.DELETE)) {
                                if (!finalPermissions.includes(DirectoryPermissionType.READ)) {
                                    finalPermissions.push(DirectoryPermissionType.READ);
                                }
                                finalPermissions.push(DirectoryPermissionType.DELETE);
                            }

                            // Assign permissions to path
                            permissions[path] = finalPermissions;
                        }
                    }
                }
                */
                // ============================================================

                // Create directory with undefined permissions (skipping permission handling for now)
                const directoryId = await courseService.postDirectory(token, courseId, name, undefined);
                vscode.window.showInformationMessage(`Directory "${name}" created with ID: ${directoryId}`);
                await vscode.commands.executeCommand('intelligent-ide.course.refresh');

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
                const token = await context.secrets.get('authToken');
                if (!token) {
                    vscode.window.showErrorMessage('Authentication token not found. Please log in again.');
                    return;
                }

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
                await vscode.commands.executeCommand('intelligent-ide.course.refresh');

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
        async (directoryItem?: CourseTreeItem) => {
            try {
                const token = await context.secrets.get('authToken');
                if (!token) {
                    vscode.window.showErrorMessage('Authentication token not found. Please log in again.');
                    return;
                }

                // Get directory ID from selected item or prompt
                let directoryId: number;

                if (directoryItem && directoryItem.itemId &&
                    (directoryItem.type === 'directory' || directoryItem.type === 'virtual-directory')) {
                    directoryId = typeof directoryItem.itemId === 'number'
                        ? directoryItem.itemId
                        : parseInt(directoryItem.itemId.toString(), 10);
                } else {
                    // Prompt for directory ID
                    const directoryIdInput = await vscode.window.showInputBox({
                        prompt: 'Enter directory ID to upload to',
                        placeHolder: 'e.g., 123',
                        validateInput: (text) => {
                            return /^\d+$/.test(text) ? null : 'Directory ID must be a number';
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
                // Get the selected filename
                const selectedFilename = path.basename(fileUris[0].fsPath);

                // Prompt for just the directory pat
                let directoryPath = await vscode.window.showInputBox({
                    prompt: 'Enter directory path to upload to (without filename)',
                    placeHolder: 'e.g., /folder/ or /',
                    value: directoryItem?.path || '/',
                    validateInput: (input) => {
                        // Ensure path starts with /
                        if (!input.startsWith('/')) {
                            return 'Path must start with /';
                        }
                        return null;
                    }
                });

                if (!directoryPath) {
                    return;
                }

                directoryPath = directoryPath === '/'
                    ? '/'
                    : directoryPath.endsWith('/') ? directoryPath : `${directoryPath}/`;

                // Then append the filename directly to directoryPath
                directoryPath = directoryPath === '/'
                    ? `/${selectedFilename}`
                    : `${directoryPath}${selectedFilename}`;

                // Show progress notification
                vscode.window.withProgress({
                    location: vscode.ProgressLocation.Notification,
                    title: 'Uploading file...',
                    cancellable: false
                }, async (progress) => {
                    // Upload the selected file using the modified directoryPath
                    const entryId = await courseService.uploadFile(
                        token,
                        directoryId,
                        directoryPath, // Using the directoryPath directly
                        fileUris[0]
                    );

                    vscode.window.showInformationMessage(`File uploaded successfully with ID: ${entryId}`);
                    await vscode.commands.executeCommand('intelligent-ide.course.refresh');
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
                const token = await context.secrets.get('authToken');
                if (!token) {
                    vscode.window.showErrorMessage('Authentication token not found. Please log in again.');
                    return;
                }

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
                    await vscode.commands.executeCommand('intelligent-ide.course.refresh');
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
                const token = await context.secrets.get('authToken');
                if (!token) {
                    vscode.window.showErrorMessage('Authentication token not found. Please log in again.');
                    return;
                }
                const loginInfo: LoginInfo | undefined = context.globalState.get('loginInfo');
                if (!loginInfo) {
                    vscode.window.showErrorMessage('You must log in first.');
                    return;
                }

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

                const joinRecordId = await courseService.joinCourse(token, courseId);
                vscode.window.showInformationMessage(`You successfully joined the course. Record ID: ${joinRecordId}`);

                await vscode.commands.executeCommand('intelligent-ide.course.refresh');
            } catch (error: any) {
                vscode.window.showErrorMessage(`Failed to join course: ${error.message}`);
            }
        }
    );

    context.subscriptions.push(disposable);
}

export function registerDownloadEntryCommand(context: vscode.ExtensionContext): void {
    const disposable = vscode.commands.registerCommand(
        'intelligent-ide.entry.download',
        async (treeItem: CourseTreeItem) => {
            try {
                // assuming courseService is already imported and available
                const token = await context.secrets.get('authToken');
                if (!token) {
                    vscode.window.showErrorMessage('Authentication token not found. Please log in again.');
                    console.error('Error: Authentication token not found.');
                    return;
                }
                console.log('Authentication token retrieved successfully.');

                // Check if the treeItem is valid and of type 'entry'
                if (!treeItem || treeItem.type !== 'entry' || treeItem.isDirectory) {
                    vscode.window.showErrorMessage('Invalid file entry selected for download.');
                    console.error('Error: Invalid file entry selected.');
                    return;
                }

                // Check if the entry ID is valid
                const entryId = typeof treeItem.itemId === 'number'
                    ? treeItem.itemId
                    : parseInt(treeItem.itemId.toString(), 10);

                if (isNaN(entryId)) {
                    vscode.window.showErrorMessage('Invalid entry ID.');
                    console.error('Error: Invalid entry ID:', treeItem.itemId);
                    return;
                }


                const fileData = await courseService.downloadEntry(token, entryId);

                const saveUri = await vscode.window.showSaveDialog({
                    saveLabel: 'Save File',
                    title: 'Save Downloaded File',
                    defaultUri: vscode.Uri.file(treeItem.label)
                });

                if (!saveUri) {
                    console.log('Save dialog cancelled by user.');
                    return;
                }
                await vscode.workspace.fs.writeFile(saveUri, fileData);
                vscode.window.showInformationMessage('File downloaded successfully!');


            } catch (error: any) {
                vscode.window.showErrorMessage(`Failed to download file: ${error.message}`);
                console.error('Error during file download:', error.message, error.stack);
            }
        }
    );

    context.subscriptions.push(disposable);
}


