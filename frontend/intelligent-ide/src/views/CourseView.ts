import * as vscode from 'vscode';
import { courseService } from '../services/CourseService';
import { ICourseDirectoryEntry } from '../models/CourseModels';
import { LoginInfo } from '../models/LoginInfo';
import * as path from 'path';
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
type TreeItemType = 'course' | 'directory' | 'entry' | 'virtual-directory';

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
        public readonly created_at?: string  // Add created_at parameter
    ) {
        super(label, collapsibleState);

        // Set appropriate icons and context values
        switch (type) {
            case 'course':
                this.iconPath = new vscode.ThemeIcon('book');
                this.contextValue = 'course';
                this.tooltip = `Course: ${label}`;
                break;
            case 'directory':
                this.iconPath = new vscode.ThemeIcon('folder');
                this.contextValue = 'directory';
                this.tooltip = `Directory: ${label}`;
                break;
            case 'virtual-directory':
                this.iconPath = new vscode.ThemeIcon('folder');
                this.contextValue = 'virtual-directory';
                this.tooltip = `Directory: ${label}`;
                break;
            case 'entry':
                if (entry && entry.type === 'directory') {
                    this.iconPath = new vscode.ThemeIcon('folder');
                    this.contextValue = 'entry-directory';
                    this.tooltip = `Directory: ${path}`;
                } else {
                    this.iconPath = getFileIcon(path || '');
                    this.contextValue = 'entry-file';
                    this.tooltip = `File: ${path}`;
                }
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

    constructor(private context: vscode.ExtensionContext) { }

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: CourseTreeItem): vscode.TreeItem {
        return element;
    }

    async getChildren(element?: CourseTreeItem): Promise<CourseTreeItem[]> {
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
            } else if (element.type === 'course') {
                // Second level: Fetch directories for the selected course
                const courseId = typeof element.itemId === 'number' ? element.itemId : parseInt(element.itemId.toString());
                const directories = await courseService.getDirectories(token, courseId);

                if (directories.length === 0) {
                    vscode.window.showInformationMessage('No directories found in this course.');
                    return [];
                }

                return directories.map(directory => new CourseTreeItem(
                    directory.name,
                    vscode.TreeItemCollapsibleState.Collapsed,
                    'directory',
                    directory.id,
                    courseId,
                    undefined, // path
                    true, // isDirectory
                    undefined, // entry
                    directory.created_at // Pass created_at directly
                ));
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

/**
 * Register the TreeView
 */
export function registerCourseView(context: vscode.ExtensionContext): vscode.Disposable {
    const treeDataProvider = new CourseTreeDataProvider(context);
    const treeView = vscode.window.createTreeView('courses', {
        treeDataProvider,
        showCollapseAll: true
    });

    // Pass treeDataProvider to command registration
    registerCourseCommands(context, treeDataProvider);

    context.subscriptions.push(treeView);
    return treeView;
}