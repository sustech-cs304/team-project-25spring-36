import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import { courseService } from '../services/CourseService';
import { ICourseDirectoryEntry } from '../models/CourseModels';
import { LoginInfo } from '../models/LoginInfo';
import { MyNotebookController } from '../notebook/NotebookController';
import { MyNotebookSerializer } from '../notebook/NotebookSerializer';
import { registerCourseCommands } from '../commands/CourseCommands';

/**
 * AI-generated-content
 * tool: GitHub Copilot
 * version: Claude 3.7 Sonnet Thinking
 * usage: I asked Copilot to implement a tree view for course content with proper 
 * hierarchical structure, file icons, and handling of virtual directories.
 * The code was adapted to cohere with backend design.
 */

// Define tree item types
type TreeItemType = 'course' | 'directory' | 'entry' | 'virtual-directory' | 'student' | 'notebook';

// Define a class for tree items
export class CourseTreeItem extends vscode.TreeItem {
    public readonly children?: CourseTreeItem[];

    constructor(
        public readonly label: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly type: TreeItemType,
        public readonly itemId: number | string,
        public readonly parentId?: number | string,
        public readonly path?: string,
        public readonly isDirectory?: boolean,
        public readonly entry?: ICourseDirectoryEntry,
        public readonly created_at?: string  // Add created_at paramete
    ) {
        super(label, collapsibleState);

        // Set appropriate icons and context values
        switch (type) {
            case 'course':
                this.iconPath = new vscode.ThemeIcon('book');
                this.contextValue = 'course';
                this.tooltip = `Course: ${label} (ID: ${itemId})`;
                break;
            case 'directory':
                this.iconPath = new vscode.ThemeIcon('folder');
                this.contextValue = 'directory';
                this.tooltip = `Directory: ${label} (ID: ${itemId})`;
                break;
            case 'virtual-directory':
                this.iconPath = new vscode.ThemeIcon('folder');
                this.contextValue = 'virtual-directory';
                this.tooltip = `Directory: ${label} (ID: ${itemId})`;
                break;
            case 'entry':
                if (entry && entry.type === 'directory') {
                    this.iconPath = new vscode.ThemeIcon('folder');
                    this.contextValue = 'entry-directory';
                    this.tooltip = `Directory: ${path} (ID: ${entry.id})`;
                } else {
                    this.iconPath = getFileIcon(path || '');
                    this.contextValue = 'entry-file';
                    this.tooltip = `File: ${path} (ID: ${itemId})`;
                }
                break;
            case 'student':
                this.iconPath = new vscode.ThemeIcon('person');
                this.contextValue = 'student';
                this.tooltip = `Student: ${label} (ID: ${itemId})`;
                break;
            case 'notebook':
                this.iconPath = new vscode.ThemeIcon('notebook');
                this.contextValue = 'notebookItem';
                this.command = {
                    command: 'vscode.openWith',
                    title: 'Open Notebook',
                    arguments: [vscode.Uri.file(path || ''), 'my-notebook']
                };
                break;
        }

        const timestamp = created_at
            ? new Date(created_at).getTime().toString()
            : entry?.created_at
                ? new Date(entry.created_at).getTime().toString()
                : Date.now().toString();

        this.id = `${type}-${itemId}-${timestamp}${path ? `-${path.replace(/[\/\\]/g, '_')}` : ''}`;

        if ((type === 'entry' && !isDirectory) && path) {
            this.command = {
                command: 'intelligent-ide.course.openFile',
                title: 'Open File',
                arguments: [this]
            };
        }
    }
}

// Define the tree data provider
export class CourseTreeDataProvider implements vscode.TreeDataProvider<CourseTreeItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<CourseTreeItem | undefined | null | void> =
        new vscode.EventEmitter<CourseTreeItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<CourseTreeItem | undefined | null | void> =
        this._onDidChangeTreeData.event;

    private readonly notebookFiles: vscode.Uri[] = [];
    private readonly defaultNotebookPath = "C:\\Users\\Lenovo\\Desktop";

    constructor(private context: vscode.ExtensionContext) {
        this.registerNotebookSerializer();
        this.registerNotebookController();
        this.loadNotebooksFromDefaultPath();
        this.registerNotebookCommands();
    }

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: CourseTreeItem): vscode.TreeItem {
        return element;
    }

    async getChildren(element?: CourseTreeItem): Promise<CourseTreeItem[]> {
        if (!element) {
            // Root level: Show notebooks and courses
            const notebooks = this.notebookFiles.map(uri => new CourseTreeItem(
                path.basename(uri.fsPath),
                vscode.TreeItemCollapsibleState.None,
                'notebook',
                uri.fsPath,
                undefined,
                uri.fsPath
            ));

            const courses = await this.getCourses();
            return [...notebooks, ...courses];
        }

        if (element.type === 'course') {
            return this.getCourseDirectories(element.itemId as number);
        }

        const loginInfo = this.context.globalState.get('loginInfo') as LoginInfo | undefined;
        if (!loginInfo) {
            vscode.window.showWarningMessage('Please log in to view courses.');
            return [];
        }

        const token = await this.context.secrets.get('authToken');
        if (!token) {
            vscode.window.showWarningMessage('Authentication token not found. Please log in again.');
            return [];
        }

        try {
            if (!element) {
                // Root level: Fetch courses
                const courses = await courseService.getCourses(token, loginInfo.role);
                if (courses.length === 0) {
                    vscode.window.showInformationMessage(`No courses found for ${loginInfo.role} role.`);
                    return [];
                }

                return courses.map(course => new CourseTreeItem(
                    course.name,
                    vscode.TreeItemCollapsibleState.Collapsed,
                    'course',
                    course.id,
                    undefined,
                    undefined,
                    undefined,
                    undefined,
                    course.created_at
                ));
            } else if ((element.type as TreeItemType) === 'course') {
                // Second level: Fetch directories for the selected course
                const courseId = typeof element.itemId === 'number' ? element.itemId : parseInt(element.itemId.toString());

                // Get directories
                const directories = await courseService.getDirectories(token, courseId);
                const directoryItems = directories.map(directory => new CourseTreeItem(
                    directory.name,
                    vscode.TreeItemCollapsibleState.Collapsed,
                    'directory',
                    directory.id,
                    courseId,
                    undefined,
                    true,
                    undefined,
                    directory.created_at
                ));

                // Only show students folder for teacher role
                if (loginInfo.role === 'teacher') {
                    // Create a students folder
                    const studentsFolder = new CourseTreeItem(
                        'students',
                        vscode.TreeItemCollapsibleState.Collapsed,
                        'virtual-directory',
                        `students-${courseId}`,
                        courseId,
                        undefined,
                        true
                    );

                    // Get students
                    try {
                        const students = await courseService.getStudents(token, courseId);
                        if (students && students.length > 0) {
                            // Create student items
                            (studentsFolder as any).children = students.map(student => new CourseTreeItem(
                                `${student.username} (${student.email})`,
                                vscode.TreeItemCollapsibleState.None,
                                'student',
                                student.id,
                                courseId,
                                undefined,
                                false
                            ));
                        }
                        // Return both directories and students folder
                        return [...directoryItems, studentsFolder];
                    } catch (error) {
                        console.error('Error fetching students:', error);
                        // Still return directories and students folder even if students fail to load
                        (studentsFolder as any).children = [
                            new CourseTreeItem(
                                'Error loading students',
                                vscode.TreeItemCollapsibleState.None,
                                'virtual-directory',
                                'error-students',
                                courseId,
                                undefined,
                                false
                            )
                        ];
                        return [...directoryItems, studentsFolder];
                    }
                } else {
                    // For students, only return the directories
                    return directoryItems;
                }
            } else if (element.type === 'directory') {
                try {
                    // Convert itemId to number if it's a string
                    const directoryId = typeof element.itemId === 'number'
                        ? element.itemId
                        : parseInt(element.itemId.toString(), 10);

                    // Check if conversion was successful
                    if (isNaN(directoryId)) {
                        vscode.window.showErrorMessage('Invalid directory ID');
                        return [];
                    }

                    // Use the root path "/" and fuzzy=true to get all entries in this directory
                    const entries = await courseService.getEntries(token, directoryId, "/", true);

                    // If no entries, just return empty array without error message
                    if (entries.length === 0) {
                        return [];
                    }

                    return this.organizeEntriesByPath(entries, directoryId);
                } catch (error: any) {
                    // If this is a "no entries" error, return empty array silently
                    if (error.message?.includes('No entries found')) {
                        return [];
                    }
                    vscode.window.showErrorMessage(`Error getting entries: ${error.message}`);
                    return [];
                }
            } else if (element.type === 'virtual-directory') {
                // Return the children of this virtual directory
                if ((element as any).children && Array.isArray((element as any).children)) {
                    return (element as any).children;
                }
                return [];
            }
        } catch (error: any) {
            vscode.window.showErrorMessage(`Error: ${error.message}`);
            return [];
        }

        return [];
    }

    private async getCourses(): Promise<CourseTreeItem[]> {
        const loginInfo = this.context.globalState.get('loginInfo') as LoginInfo | undefined;
        if (!loginInfo) {
            vscode.window.showWarningMessage('Please log in to view courses.');
            return [];
        }

        const token = await this.context.secrets.get('authToken');
        if (!token) {
            vscode.window.showWarningMessage('Authentication token not found. Please log in again.');
            return [];
        }

        const courses = await courseService.getCourses(token, loginInfo.role);
        return courses.map(course => new CourseTreeItem(
            course.name,
            vscode.TreeItemCollapsibleState.Collapsed,
            'course',
            course.id
        ));
    }

    private async getCourseDirectories(courseId: number): Promise<CourseTreeItem[]> {
        const token = await this.context.secrets.get('authToken');
        if (!token) {
            vscode.window.showWarningMessage('Authentication token not found. Please log in again.');
            return [];
        }

        const directories = await courseService.getDirectories(token, courseId);
        return directories.map(directory => new CourseTreeItem(
            directory.name,
            vscode.TreeItemCollapsibleState.Collapsed,
            'directory',
            directory.id,
            courseId
        ));
    }

    /**
     * Organize entries by their path structure to create a virtual file system
     * This approach ignores directory-type entries and builds the structure from file paths
     */
    private organizeEntriesByPath(entries: ICourseDirectoryEntry[], parentDirectoryId: number): CourseTreeItem[] {
        // Map to track all created virtual directories by path
        const directoryMap = new Map<string, CourseTreeItem>();
        const rootItems: CourseTreeItem[] = [];

        // First pass: only process file entries and build directory structure
        for (const entry of entries) {
            // Skip entries that are explicitly directories
            if (entry.type === "directory") {
                continue;
            }

            // Normalize path (remove leading slash)
            const normalizedPath = entry.path.replace(/^\/+/, '');
            const pathParts = normalizedPath.split('/');

            if (pathParts.length === 1) {
                // This is a root-level file
                rootItems.push(new CourseTreeItem(
                    normalizedPath,
                    vscode.TreeItemCollapsibleState.None,
                    'entry',
                    entry.id,
                    parentDirectoryId,
                    normalizedPath,
                    false,
                    entry,
                    entry.created_at
                ));
            } else {
                // This is a nested file - we need to ensure all parent directories exist
                let currentPath = "";
                const filename = pathParts.pop() || ""; // Get the last part (always the filename)

                // Create directory structure as needed
                for (const part of pathParts) {
                    const parentPath = currentPath;
                    currentPath = currentPath ? `${currentPath}/${part}` : part;

                    // Create this directory if it doesn't exist yet
                    if (!directoryMap.has(currentPath)) {
                        const virtualDirId = `virtual-${currentPath}-${Math.random().toString(36).substring(2, 9)}`;
                        const virtualDir = new CourseTreeItem(
                            part,
                            vscode.TreeItemCollapsibleState.Collapsed,
                            'virtual-directory',
                            virtualDirId,
                            parentDirectoryId,
                            currentPath,
                            true
                        );

                        // Add children array to track nested items
                        (virtualDir as any).children = [];

                        // Add to directory map
                        directoryMap.set(currentPath, virtualDir);

                        // Add to parent directory or root
                        if (parentPath) {
                            const parentDir = directoryMap.get(parentPath);
                            if (parentDir && (parentDir as any).children) {
                                (parentDir as any).children.push(virtualDir);
                            }
                        } else {
                            rootItems.push(virtualDir);
                        }
                    }
                }

                // Now add the file to its parent directory
                const fileItem = new CourseTreeItem(
                    filename,
                    vscode.TreeItemCollapsibleState.None,
                    'entry',
                    entry.id,
                    parentDirectoryId,
                    normalizedPath,
                    false,
                    entry,
                    entry.created_at // Pass created_at directly
                );

                const parentDir = directoryMap.get(currentPath);
                if (parentDir && (parentDir as any).children) {
                    (parentDir as any).children.push(fileItem);
                }
            }
        }

        // Apply some additional improvements
        return this.sortTreeItems(rootItems);
    }

    /**
     * Sort tree items - directories first, then alphabetically
     */
    private sortTreeItems(items: CourseTreeItem[]): CourseTreeItem[] {
        items.sort((a, b) => {
            // Directories before files
            const aIsDir = a.type === 'virtual-directory' || (a.type === 'entry' && a.isDirectory);
            const bIsDir = b.type === 'virtual-directory' || (b.type === 'entry' && b.isDirectory);

            if (aIsDir && !bIsDir) { return -1; }
            if (!aIsDir && bIsDir) { return 1; }

            // Alphabetical order
            return a.label.localeCompare(b.label);
        });

        // Recursively sort children
        for (const item of items) {
            if ((item as any).children) {
                (item as any).children = this.sortTreeItems((item as any).children);
            }
        }

        return items;
    }

    private registerNotebookSerializer() {
        vscode.workspace.registerNotebookSerializer(
            'my-notebook',
            new MyNotebookSerializer()
        );
    }

    private registerNotebookController() {
        new MyNotebookController();
    }

    private loadNotebooksFromDefaultPath() {
        if (!fs.existsSync(this.defaultNotebookPath)) {
            console.error(`Default notebook path does not exist: ${this.defaultNotebookPath}`);
            return;
        }

        const files = fs.readdirSync(this.defaultNotebookPath);
        files.forEach(file => {
            if (file.endsWith('.ipynb')) {
                const filePath = path.join(this.defaultNotebookPath, file);
                this.notebookFiles.push(vscode.Uri.file(filePath));
            }
        });

        this.refresh();
    }

    private registerNotebookCommands() {
        vscode.commands.registerCommand('intelligent-ide.notebook.new', async () => {
            const uri = await vscode.window.showSaveDialog({
                filters: { 'My Notebook': ['ipynb'] },
                saveLabel: 'Create Notebook',
                defaultUri: vscode.Uri.file(path.join(this.defaultNotebookPath, 'Untitled.ipynb'))
            });

            if (!uri) {
                vscode.window.showInformationMessage('Notebook creation cancelled.');
                return;
            }

            const initialContent = JSON.stringify({ cells: [] }, null, 2);
            await vscode.workspace.fs.writeFile(uri, Buffer.from(initialContent, 'utf8'));

            this.notebookFiles.push(uri);
            this.refresh();

            vscode.window.showInformationMessage(`Notebook created: ${uri.fsPath}`);
        });

        vscode.commands.registerCommand('intelligent-ide.notebook.delete', async (item: CourseTreeItem) => {
            const uri = vscode.Uri.file(item.path || '');
            if (!uri || !uri.fsPath) {
                vscode.window.showErrorMessage('Invalid notebook file.');
                return;
            }

            const confirmed = await vscode.window.showWarningMessage(
                `Are you sure you want to delete ${path.basename(uri.fsPath)}?`,
                { modal: true },
                'Yes'
            );

            if (confirmed === 'Yes') {
                try {
                    fs.unlinkSync(uri.fsPath);
                    const index = this.notebookFiles.findIndex(file => file.fsPath === uri.fsPath);
                    if (index !== -1) {
                        this.notebookFiles.splice(index, 1);
                        this.refresh();
                    }
                    vscode.window.showInformationMessage(`Notebook deleted: ${uri.fsPath}`);
                } catch (error) {
                    vscode.window.showErrorMessage(`Failed to delete notebook: ${(error as Error).message}`);
                }
            }
        });

        vscode.commands.registerCommand('intelligent-ide.notebook.refresh', () => {
            this.notebookFiles.length = 0;
            this.loadNotebooksFromDefaultPath();
            this.refresh();
            vscode.window.showInformationMessage('Notebook Explorer refreshed.');
        });
    }
}

/**
 * Get appropriate icon for file based on extension
 */
function getFileIcon(filePath: string): vscode.ThemeIcon {
    const ext = path.extname(filePath).toLowerCase();

    switch (ext) {
        case '.js':
        case '.ts':
        case '.jsx':
        case '.tsx':
            return new vscode.ThemeIcon('symbol-method');
        case '.html':
        case '.htm':
            return new vscode.ThemeIcon('symbol-property');
        case '.css':
        case '.scss':
        case '.less':
            return new vscode.ThemeIcon('symbol-color');
        case '.json':
            return new vscode.ThemeIcon('bracket');
        case '.md':
            return new vscode.ThemeIcon('markdown');
        case '.py':
            return new vscode.ThemeIcon('symbol-namespace');
        case '.c':
        case '.cpp':
        case '.h':
        case '.hpp':
            return new vscode.ThemeIcon('symbol-class');
        case '.java':
            return new vscode.ThemeIcon('symbol-package');
        case '.pdf':
            return new vscode.ThemeIcon('output');
        case '.jpg':
        case '.jpeg':
        case '.png':
        case '.gif':
        case '.bmp':
        case '.svg':
            return new vscode.ThemeIcon('symbol-enum');
        default:
            return new vscode.ThemeIcon('file');
    }
}
