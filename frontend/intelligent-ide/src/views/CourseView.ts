import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import { courseService } from '../services/CourseService';
import { ICourseDirectoryEntry } from '../models/CourseModels';
import { MyNotebookController } from '../notebook/NotebookController';
import { MyNotebookSerializer } from '../notebook/NotebookSerializer';
import { getAuthDetails } from '../utils/authUtils';
import { ICourseHomeworkAssignment, ICourseHomeworkSubmission } from '../models/AssignmentModels';
import { assignmentService } from '../services/AssignmentService';
import PDFDocument from 'pdfkit';

/**
 * AI-generated-content
 * tool: GitHub Copilot
 * version: Claude 3.7 Sonnet Thinking
 * usage: I asked Copilot to implement a tree view for course content with proper 
 * hierarchical structure, file icons, and handling of virtual directories.
 * The code was adapted to cohere with backend design.
 */

// Define tree item types
type TreeItemType = 'course' | 'directory' | 'entry' | 'virtual-directory' | 'student' | 'notebook' |
    'assignment' | 'submission' | 'assignment-folder' | 'submission-folder';

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
        public readonly created_at?: string,
        public readonly assignment?: ICourseHomeworkAssignment,
        public readonly submission?: ICourseHomeworkSubmission
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
            case 'assignment-folder':
                this.iconPath = new vscode.ThemeIcon('folder');
                this.contextValue = 'assignmentFolder';
                break;
            case 'assignment':
                // Use different icons based on deadline status
                if (assignment?.deadline) {
                    const now = new Date();
                    const deadline = new Date(assignment.deadline);
                    const daysUntilDeadline = Math.ceil((deadline.getTime() - now.getTime()) / (1000 * 3600 * 24));

                    if (daysUntilDeadline < 0) {
                        // Overdue
                        this.iconPath = new vscode.ThemeIcon('warning', new vscode.ThemeColor('errorForeground'));
                    } else if (daysUntilDeadline <= 2) {
                        // Due soon
                        this.iconPath = new vscode.ThemeIcon('clock', new vscode.ThemeColor('editorWarning.foreground'));
                    } else {
                        // Plenty of time
                        this.iconPath = new vscode.ThemeIcon('notebook');
                    }
                } else {
                    this.iconPath = new vscode.ThemeIcon('notebook');
                }
                this.contextValue = 'assignmentItem';

                // Add deadline in the description if available
                if (assignment?.deadline) {
                    const deadline = new Date(assignment.deadline);
                    this.description = `Due: ${deadline.toLocaleDateString()}`;
                    this.tooltip = new vscode.MarkdownString(`**${this.label}**\n\nDue: ${deadline.toLocaleString()}`);
                }

                if (assignment && assignment.course_directory_entry_ids) {
                    let entryIds: number[] = [];
                    if (typeof assignment.course_directory_entry_ids === 'string') {
                        entryIds = JSON.parse(assignment.course_directory_entry_ids);
                    }
                    const attachmentCount = entryIds.length;
                    if (attachmentCount > 0) {
                        if (this.description) {
                            this.description += ` | ${attachmentCount} attachment${attachmentCount !== 1 ? 's' : ''}`;
                        } else {
                            this.description = `${attachmentCount} attachment${attachmentCount !== 1 ? 's' : ''}`;
                        }
                    }
                }
                break;
            case 'submission-folder':
                this.iconPath = new vscode.ThemeIcon('repo-push');
                this.contextValue = 'submissionFolder';
                break;
            case 'submission':
                // Use different icons based on grade status
                if (submission?.grade !== undefined) {
                    this.iconPath = new vscode.ThemeIcon('check', new vscode.ThemeColor('editor.foreground'));
                    this.description = `Grade: ${submission.grade}`;
                } else {
                    this.iconPath = new vscode.ThemeIcon('circle-outline');
                    this.description = 'Not graded';
                }
                this.contextValue = 'submissionItem';

                // Add submission date in tooltip
                if (submission?.submission_date) {
                    const submissionDate = new Date(submission.submission_date);
                    this.tooltip = new vscode.MarkdownString(`**${this.label}**\n\nSubmitted: ${submissionDate.toLocaleString()}`);
                }

                if (submission && submission.course_directory_entry_ids) {
                    let entryIds: number[] = [];
                    if (typeof submission.course_directory_entry_ids === 'string') {
                        entryIds = JSON.parse(submission.course_directory_entry_ids);
                    }
                    const attachmentCount = entryIds.length;
                    if (attachmentCount > 0) {
                        if (this.description) {
                            this.description += ` | ${attachmentCount} attachment${attachmentCount !== 1 ? 's' : ''}`;
                        } else {
                            this.description = `${attachmentCount} attachment${attachmentCount !== 1 ? 's' : ''}`;
                        }
                    }
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

    private readonly notebookFiles: vscode.Uri[] = [];
    private readonly defaultNotebookPath = "C:\\Users\\Lenovo\\Desktop";

    // Add a cache for entries
    private entryCache: Map<number, ICourseDirectoryEntry> = new Map();

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
        // For operations requiring auth, call the utility first
        const authDetails = await getAuthDetails(this.context);
        if (!authDetails) {
            return [];
        }
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
            // For a course, show both directories and an assignments folder
            const directoryItems = await this.getCourseDirectories(element.itemId as number);

            // Add assignments folder
            const assignmentsFolder = new CourseTreeItem(
                'Assignments',
                vscode.TreeItemCollapsibleState.Collapsed,
                'assignment-folder',
                `assignments-${element.itemId}`,
                element.itemId as number
            );

            return [assignmentsFolder, ...directoryItems];
        }

        if (element.type === 'assignment-folder' && authDetails) {
            // Show assignments for this course
            const courseId = element.parentId as number;
            return await this.getAssignments(courseId, authDetails.token);
        }

        if (element.type === 'assignment' && authDetails) {
            const assignmentId = element.itemId as number;

            // For teachers: show submissions folder
            // For students: show their submissions (or option to submit)
            if (authDetails.loginInfo.role === 'teacher') {
                return [
                    new CourseTreeItem(
                        'Submissions',
                        vscode.TreeItemCollapsibleState.Collapsed,
                        'submission-folder',
                        `submissions-${assignmentId}`,
                        assignmentId
                    )
                ];
            } else {
                // For students - get their submissions or show "Submit" option
                return await this.getStudentSubmissions(assignmentId, authDetails.token);
            }
        }

        if (element.type === 'submission-folder' && authDetails) {
            // Show all submissions for this assignment (teacher view)
            const assignmentId = element.parentId as number;
            return await this.getAllSubmissions(assignmentId, authDetails.token);
        }

        // Keep the rest of the existing structure
        try {
            if (element.type === 'directory') {
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
                const entries = await courseService.getEntries(authDetails.token, directoryId, "/", true);

                // If no entries, just return empty array without error message
                if (entries.length === 0) {
                    return [];
                }

                // When processing entries from the API response:
                entries.forEach(entry => {
                    this.addEntryToCache(entry); // Add this line
                });

                return this.organizeEntriesByPath(entries, directoryId);
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

    // Expose methods to access and manage the entry cache
    public findEntryById(entryId: number): ICourseDirectoryEntry | undefined {
        return this.entryCache.get(entryId);
    }

    public addEntryToCache(entry: ICourseDirectoryEntry): void {
        if (entry && entry.id) {
            this.entryCache.set(Number(entry.id), entry);
        }
    }

    private async getCourses(): Promise<CourseTreeItem[]> {
        // For operations requiring auth, call the utility first
        const authDetails = await getAuthDetails(this.context);
        if (!authDetails) {
            return []; // Auth failed, return empty
        }
        const { token, loginInfo } = authDetails;

        const courses = await courseService.getCourses(token, loginInfo.role);

        // Start preloading all entries for each course in the background
        for (const course of courses) {
            this.preloadAllCourseEntries(token, course.id).catch(err => {
                console.error(`Error preloading entries for course ${course.id}:`, err);
            });
        }

        return courses.map(course => new CourseTreeItem(
            course.name,
            vscode.TreeItemCollapsibleState.Collapsed,
            'course',
            course.id
        ));
    }

    private async getCourseDirectories(courseId: number): Promise<CourseTreeItem[]> {
        const authDetails = await getAuthDetails(this.context);
        if (!authDetails) {
            return []; // Auth failed, return empty
        }
        const { token, loginInfo } = authDetails;


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

        vscode.commands.registerCommand('intelligent-ide.notebook.exportToPdf', async (item: CourseTreeItem) => {
            const uri = vscode.Uri.file(item.path || '');
            if (!uri || !uri.fsPath) {
                vscode.window.showErrorMessage('Invalid notebook file.');
                return;
            }

            // Read and parse the notebook content
            const rawContent = fs.readFileSync(uri.fsPath, 'utf8');

            let parsedContent;
            try {
                parsedContent = JSON.parse(rawContent); // Parse the JSON content
            } catch (error) {
                vscode.window.showErrorMessage('Failed to parse notebook content.');
                return;
            }

            // Extract and format the content from cells
            const cells = parsedContent.cells || [];
            const formattedContent = cells
                .map((cell: any) => cell.value || '') // Extract the "value" field from each cell
                .join('\n\n'); // Separate cells with double newlines

            // Prompt user to select the export path
            const saveUri = await vscode.window.showSaveDialog({
                filters: { 'PDF Files': ['pdf'] },
                saveLabel: 'Export as PDF',
                defaultUri: vscode.Uri.file(uri.fsPath.replace(/\.ipynb$/, '.pdf'))
            });

            if (!saveUri) {
                vscode.window.showInformationMessage('Export cancelled.');
                return;
            }

            const pdfPath = saveUri.fsPath;

            // Check if the file already exists
            if (fs.existsSync(pdfPath)) {
                const overwrite = await vscode.window.showWarningMessage(
                    `The file ${pdfPath} already exists. Do you want to overwrite it?`,
                    { modal: true },
                    'Yes',
                    'No'
                );

                if (overwrite !== 'Yes') {
                    vscode.window.showInformationMessage('Export cancelled.');
                    return;
                }
            }

            try {
                const doc = new PDFDocument();
                const writeStream = fs.createWriteStream(pdfPath);

                doc.pipe(writeStream);

                doc.font('Times-Roman'); // Use built-in font
                doc.text(formattedContent, { align: 'left' }); // Write formatted content to PDF

                doc.end();

                writeStream.on('finish', () => {
                    vscode.window.showInformationMessage(`Notebook exported successfully to: ${pdfPath}`);
                });

                writeStream.on('error', (error) => {
                    vscode.window.showErrorMessage(`Failed to write PDF: ${error.message}`);
                });
            } catch (error) {
                vscode.window.showErrorMessage(`Failed to export notebook as PDF: ${(error as Error).message}`);
            }
        });
    }

    private async getAssignments(courseId: number, token: string): Promise<CourseTreeItem[]> {
        try {
            const assignments = await assignmentService.getAssignments(token, courseId);

            return assignments.map(assignment => new CourseTreeItem(
                assignment.title || `Assignment ${assignment.id}`,
                vscode.TreeItemCollapsibleState.Collapsed,
                'assignment',
                assignment.id,
                courseId,
                undefined,
                undefined,
                undefined,
                assignment.created_at,
                assignment
            ));
        } catch (error: any) {
            vscode.window.showErrorMessage(`Error loading assignments: ${error.message}`);
            return [];
        }
    }

    private async getAllSubmissions(assignmentId: number, token: string): Promise<CourseTreeItem[]> {
        try {
            const submissions = await assignmentService.getSubmissions(token, { assignment_id: assignmentId });

            return submissions.map(submission => new CourseTreeItem(
                submission.title || `Submission by Student ${submission.student_id}`,
                vscode.TreeItemCollapsibleState.None,
                'submission',
                submission.id,
                assignmentId,
                undefined,
                undefined,
                undefined,
                submission.created_at,
                undefined,
                submission
            ));
        } catch (error: any) {
            vscode.window.showErrorMessage(`Error loading submissions: ${error.message}`);
            return [];
        }
    }

    private async getStudentSubmissions(assignmentId: number, token: string): Promise<CourseTreeItem[]> {
        try {
            const authDetails = await getAuthDetails(this.context);
            if (!authDetails) {
                return [];
            }

            // For student role, we only fetch their own submissions
            const submissions = await assignmentService.getSubmissions(token, {
                assignment_id: assignmentId,
            });

            return submissions.map(submission => new CourseTreeItem(
                submission.title || `Your submission (${new Date(submission.submission_date).toLocaleDateString()})`,
                vscode.TreeItemCollapsibleState.None,
                'submission',
                submission.id,
                assignmentId,
                undefined,
                undefined,
                undefined,
                submission.created_at,
                undefined,
                submission
            ));
        } catch (error: any) {
            vscode.window.showErrorMessage(`Error loading your submissions: ${error.message}`);
            return [];
        }
    }

    /**
     * Preload all entries from all directories for a course
     * to ensure attachments are available in the cache
     */
    private async preloadAllCourseEntries(token: string, courseId: number): Promise<void> {
        console.log(`Preloading entries for course ${courseId}`);

        try {
            // First get all directories for this course
            const directories = await courseService.getDirectories(token, courseId);

            // For each directory, load all its entries
            for (const directory of directories) {
                try {
                    const entries = await courseService.getEntries(token, directory.id, "/", true);

                    // Add all entries to the cache
                    entries.forEach(entry => {
                        this.addEntryToCache(entry);
                    });

                    console.log(`Loaded ${entries.length} entries from directory ${directory.name}`);
                } catch (error) {
                    console.error(`Failed to load entries for directory ${directory.id}:`, error);
                }
            }
        } catch (error) {
            console.error(`Failed to preload entries for course ${courseId}:`, error);
        }
    }
}
export function createCourseTreeDataProvider(context: vscode.ExtensionContext): CourseTreeDataProvider {
    return new CourseTreeDataProvider(context);
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
