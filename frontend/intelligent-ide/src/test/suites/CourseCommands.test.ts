import * as assert from 'assert';
import * as sinon from 'sinon';
import * as vscode from 'vscode';
import { courseService } from '../../services/CourseService';
import * as viewManager from '../../views/viewManager';
import * as authUtils from '../../utils/authUtils';
import { registerCourseCommands } from '../../commands/CourseCommands';

suite('Course Commands Test Suite', () => {
    let mockContext: vscode.ExtensionContext;
    let mockGlobalState: Map<string, any>;
    let mockWorkspaceState: Map<string, any>;
    let mockSecrets: {
        store: sinon.SinonStub<[string, string], Promise<void>>;
        get: sinon.SinonStub<[string], Promise<string | undefined>>;
        delete: sinon.SinonStub<[string], Promise<void>>;
    };
    let mockCommands: Record<string, (...args: any[]) => any>;
    let globalStateUpdateStub: sinon.SinonStub<[string, any], Promise<void>>;
    let workspaceStateUpdateStub: sinon.SinonStub<[string, any], Promise<void>>;

    // VS Code API stubs
    let showInputBoxStub: sinon.SinonStub;
    let showQuickPickStub: sinon.SinonStub;
    let showInfoMessageStub: sinon.SinonStub;
    let showErrorMessageStub: sinon.SinonStub;
    let showWarningMessageStub: sinon.SinonStub;
    let showOpenDialogStub: sinon.SinonStub;
    let showSaveDialogStub: sinon.SinonStub;
    let withProgressStub: sinon.SinonStub;

    // View manager stubs
    let refreshAllViewsStub: sinon.SinonStub;
    let refreshViewsStub: sinon.SinonStub;

    // Auth utils stub
    let getAuthDetailsStub: sinon.SinonStub;

    // Service stubs
    let createCourseStub: sinon.SinonStub;
    let deleteCourseStub: sinon.SinonStub;
    let postDirectoryStub: sinon.SinonStub;
    let deleteDirectoryStub: sinon.SinonStub;
    let uploadFileStub: sinon.SinonStub;
    let deleteEntryStub: sinon.SinonStub;
    let moveEntryStub: sinon.SinonStub;
    let joinCourseStub: sinon.SinonStub;
    let deleteStudentStub: sinon.SinonStub;
    let getStudentsStub: sinon.SinonStub;
    let downloadEntryStub: sinon.SinonStub;

    // Filesystem stubs
    let fsExistsStub: sinon.SinonStub;
    let fsMkdirStub: sinon.SinonStub;
    let workspaceWriteFileStub: sinon.SinonStub;

    const mockToken = 'mock-token-123';
    const mockLoginInfo = {
        id: 1,
        email: 'test@example.com',
        username: 'testuser',
        role: 'teacher' as const,
        token: mockToken
    };

    setup(() => {
        sinon.restore();
        mockGlobalState = new Map<string, any>();
        mockWorkspaceState = new Map<string, any>();
        
        mockSecrets = {
            store: sinon.stub<[string, string], Promise<void>>().resolves(),
            get: sinon.stub<[string], Promise<string | undefined>>().resolves(mockToken),
            delete: sinon.stub<[string], Promise<void>>().resolves()
        };
        mockCommands = {};

        globalStateUpdateStub = sinon.stub<[string, any], Promise<void>>().callsFake(async (key: string, value: any) => {
            mockGlobalState.set(key, value);
            return Promise.resolve();
        });

        workspaceStateUpdateStub = sinon.stub<[string, any], Promise<void>>().callsFake(async (key: string, value: any) => {
            mockWorkspaceState.set(key, value);
            return Promise.resolve();
        });

        mockContext = {
            subscriptions: [],
            globalState: {
                get: (key: string) => mockGlobalState.get(key),
                update: globalStateUpdateStub
            } as any,
            workspaceState: {
                get: (key: string) => mockWorkspaceState.get(key),
                update: workspaceStateUpdateStub
            } as any,
            secrets: mockSecrets
        } as unknown as vscode.ExtensionContext;

        sinon.stub(vscode.commands, 'registerCommand').callsFake((commandId, handler) => {
            mockCommands[commandId] = handler;
            return { dispose: () => { } };
        });
        sinon.stub(vscode.commands, 'executeCommand').callsFake((commandId, ...args) => {
            if (mockCommands[commandId]) {
                return Promise.resolve(mockCommands[commandId](...args));
            }
            return Promise.resolve(undefined);
        });

        // VS Code window stubs
        showInputBoxStub = sinon.stub(vscode.window, 'showInputBox');
        showQuickPickStub = sinon.stub(vscode.window, 'showQuickPick');
        showInfoMessageStub = sinon.stub(vscode.window, 'showInformationMessage').resolves(undefined);
        showErrorMessageStub = sinon.stub(vscode.window, 'showErrorMessage').resolves(undefined);
        showWarningMessageStub = sinon.stub(vscode.window, 'showWarningMessage').resolves(undefined);
        
        // Fix showOpenDialog to return a valid URI array immediately
        showOpenDialogStub = sinon.stub(vscode.window, 'showOpenDialog').resolves([vscode.Uri.file('/fake/path/test.txt')]);
        showSaveDialogStub = sinon.stub(vscode.window, 'showSaveDialog').resolves(vscode.Uri.file('/fake/path/saved.txt'));
    
        withProgressStub = sinon.stub(vscode.window, 'withProgress').callsFake((opts, cb) => {
            return cb(
                { report: () => { } }, 
                { isCancellationRequested: false, onCancellationRequested: () => ({ dispose: () => {} }) }
            );
        });

        // View manager stubs
        refreshAllViewsStub = sinon.stub(viewManager, 'refreshAllViews');
        refreshViewsStub = sinon.stub(viewManager, 'refreshViews');

        // Auth utils
        getAuthDetailsStub = sinon.stub(authUtils, 'getAuthDetails').resolves({ token: mockToken, loginInfo: mockLoginInfo });

        // Course service stubs
        createCourseStub = sinon.stub(courseService, 'createCourse').resolves();
        deleteCourseStub = sinon.stub(courseService, 'deleteCourse').resolves();
        postDirectoryStub = sinon.stub(courseService, 'postDirectory').resolves(1);
        deleteDirectoryStub = sinon.stub(courseService, 'deleteDirectory').resolves();
        uploadFileStub = sinon.stub(courseService, 'uploadFile').resolves(1);
        deleteEntryStub = sinon.stub(courseService, 'deleteEntry').resolves();
        moveEntryStub = sinon.stub(courseService, 'moveEntry').resolves();
        joinCourseStub = sinon.stub(courseService, 'joinCourse').resolves(1);
        deleteStudentStub = sinon.stub(courseService, 'deleteStudent').resolves();
        getStudentsStub = sinon.stub(courseService, 'getStudents').resolves([{ id: '2', username: 'student1', email: 's1@example.com',created_at: '2023-01-01' , uid: '1' }]);
        downloadEntryStub = sinon.stub(courseService, 'downloadEntry').resolves(Buffer.from('test content'));

        registerCourseCommands(mockContext);
    });

    teardown(() => {
        sinon.restore();
 
    });

    test('Create course command - successful', async () => {
        showInputBoxStub.onFirstCall().resolves('Course Name');
        showInputBoxStub.onSecondCall().resolves('Course Description');
        await vscode.commands.executeCommand('intelligent-ide.course.post');
        assert.ok(createCourseStub.calledWith(mockToken, 'Course Name', 'Course Description'));
        assert.ok(showInfoMessageStub.calledWithMatch(/created successfully/));
        assert.ok(refreshViewsStub.called);
    });

    test('Create course command - role switch', async () => {
        const studentInfo = { ...mockLoginInfo, role: 'student' as 'student' };
        getAuthDetailsStub.resolves({ token: mockToken, loginInfo: studentInfo });
        
        showWarningMessageStub.resolves('Yes');
        showInputBoxStub.onFirstCall().resolves('Course Name');
        showInputBoxStub.onSecondCall().resolves('Course Description');
        
        await vscode.commands.executeCommand('intelligent-ide.course.post');
        
        // Should update role to teacher in workspace state
        assert.ok(workspaceStateUpdateStub.calledWith('loginInfo', { ...studentInfo, role: 'teacher' }));
        assert.ok(refreshAllViewsStub.called);
        assert.ok(createCourseStub.calledWith(mockToken, 'Course Name', 'Course Description'));
    });

    test('Create course command - cancelled inputs', async () => {
        showInputBoxStub.onFirstCall().resolves(undefined); // Cancel on course name
        await vscode.commands.executeCommand('intelligent-ide.course.post');
        assert.ok(!createCourseStub.called);
    });

    test('Delete course command - successful', async () => {
        showWarningMessageStub.resolves('Yes');
        await vscode.commands.executeCommand('intelligent-ide.course.delete', { itemId: 1, label: 'Course 1' });
        assert.ok(deleteCourseStub.calledWith(mockToken, 1));
        assert.ok(showInfoMessageStub.calledWithMatch(/deleted successfully/));
        assert.ok(refreshViewsStub.called);
    });

    test('Delete course command - manual input', async () => {
        showInputBoxStub.resolves('42');
        await vscode.commands.executeCommand('intelligent-ide.course.delete');
        assert.ok(deleteCourseStub.calledWith(mockToken, 42));
        assert.ok(showInfoMessageStub.calledWithMatch(/deleted successfully/));
    });

    test('Delete course command - cancelled confirmation', async () => {
        showWarningMessageStub.resolves('No');
        await vscode.commands.executeCommand('intelligent-ide.course.delete', { itemId: 1, label: 'Course 1' });
        assert.ok(!deleteCourseStub.called);
    });

    test('Delete course command - no teacher role', async () => {
        const studentInfo = { ...mockLoginInfo, role: 'student' as 'student' };
        getAuthDetailsStub.resolves({ token: mockToken, loginInfo: studentInfo });
        
        await vscode.commands.executeCommand('intelligent-ide.course.delete', { itemId: 1 });
        assert.ok(!deleteCourseStub.called);
        assert.ok(showErrorMessageStub.calledWith('Only teachers can delete courses.'));
    });


    test('Open file command - using cached version', async () => {
        
        const mockItem = {
            entry: { id: 42, created_at: '2023-05-15T12:00:00Z' },
            path: '/folder/test.txt',
            label: 'test.txt',
            isDirectory: false
        };

        await vscode.commands.executeCommand('intelligent-ide.course.openFile', mockItem);
        
        assert.ok(withProgressStub.called);
        assert.ok(!downloadEntryStub.called);
    });

    test('Delete directory command - successful with tree item', async () => {
        showWarningMessageStub.resolves('Yes');
        
        const directoryItem = {
            itemId: 3,
            label: 'Lectures',
            type: 'directory'
        };
        
        await vscode.commands.executeCommand('intelligent-ide.directory.delete', directoryItem);
        assert.ok(deleteDirectoryStub.calledWith(mockToken, 3));
        assert.ok(showInfoMessageStub.calledWithMatch(/deleted successfully/));
        assert.ok(refreshViewsStub.called);
    });

    test('Delete directory command - successful with manual input', async () => {
        showInputBoxStub.resolves('5');
        
        await vscode.commands.executeCommand('intelligent-ide.directory.delete');
        assert.ok(deleteDirectoryStub.calledWith(mockToken, 5));
        assert.ok(showInfoMessageStub.calledWithMatch(/deleted successfully/));
    });

    test('Delete directory command - cancelled confirmation', async () => {
        showWarningMessageStub.resolves('No');
        
        const directoryItem = {
            itemId: 3,
            label: 'Lectures'
        };
        
        await vscode.commands.executeCommand('intelligent-ide.directory.delete', directoryItem);
        assert.ok(!deleteDirectoryStub.called);
    });

    test('Post directory command - successful with course tree item', async () => {
        showInputBoxStub.resolves('NewDirectory');
        
        const courseItem = {
            itemId: 2,
            type: 'course'
        };
        
        await vscode.commands.executeCommand('intelligent-ide.directory.post', courseItem);
        assert.ok(postDirectoryStub.calledWith(mockToken, 2, 'NewDirectory', undefined));
        assert.ok(showInfoMessageStub.calledWithMatch(/created with ID: 1/));
        assert.ok(refreshViewsStub.called);
    });

    test('Post directory command - successful with course ID', async () => {
        showInputBoxStub.resolves('NewDirectory');
        
        await vscode.commands.executeCommand('intelligent-ide.directory.post', 3);
        assert.ok(postDirectoryStub.calledWith(mockToken, 3, 'NewDirectory', undefined));
        assert.ok(showInfoMessageStub.calledWithMatch(/created with ID: 1/));
    });

    test('Post directory command - manual course ID input', async () => {
        showInputBoxStub.onFirstCall().resolves('4'); // Course ID
        showInputBoxStub.onSecondCall().resolves('Assignments'); // Directory name
        
        await vscode.commands.executeCommand('intelligent-ide.directory.post');
        assert.ok(postDirectoryStub.calledWith(mockToken, 4, 'Assignments', undefined));
    });

    test('Delete entry command - successful', async () => {
        showWarningMessageStub.resolves('Yes');
        
        const entryItem = {
            entry: { id: 7 },
            label: 'report.pdf'
        };
        
        await vscode.commands.executeCommand('intelligent-ide.entry.delete', entryItem);
        assert.ok(deleteEntryStub.calledWith(mockToken, 7));
        assert.ok(showInfoMessageStub.calledWithMatch(/deleted successfully/));
        assert.ok(refreshViewsStub.called);
    });

    test('Delete entry command - cancelled confirmation', async () => {
        showWarningMessageStub.resolves('No');
        
        const entryItem = {
            entry: { id: 7 },
            label: 'report.pdf'
        };
        
        await vscode.commands.executeCommand('intelligent-ide.entry.delete', entryItem);
        assert.ok(!deleteEntryStub.called);
    });

    test('Delete entry command - no entry provided', async () => {
        await vscode.commands.executeCommand('intelligent-ide.entry.delete');
        assert.ok(!deleteEntryStub.called);
        assert.ok(showErrorMessageStub.calledWith('No entry selected for deletion'));
    });

    test('Upload file command - successful with directory item', async function() {
        // Increase timeout for this test
        this.timeout(5000);
        
        // Ensure showOpenDialog resolves immediately
        showOpenDialogStub.resolves([vscode.Uri.file('/tmp/test.txt')]);
        showInputBoxStub.resolves('/');
        
        const directoryItem = {
            type: 'directory',
            itemId: 5
        };
        
        // Use await to ensure promise completes
        await vscode.commands.executeCommand('intelligent-ide.entry.upload', directoryItem);
        
        // Verify the service was called with correct parameters
        assert.ok(uploadFileStub.called, "uploadFile should be called");
        assert.ok(showInfoMessageStub.called, "Info message should be shown");
        assert.ok(refreshViewsStub.called, "Views should be refreshed");
    });

    test('Upload file command - successful with directoryId param', async function() {
        this.timeout(5000);
        
        showOpenDialogStub.resolves([vscode.Uri.file('/tmp/test2.txt')]);
        showInputBoxStub.resolves('/subfolder/');
        
        await vscode.commands.executeCommand('intelligent-ide.entry.upload', { directoryId: 6 });
        
        assert.ok(uploadFileStub.called, "uploadFile should be called");
        assert.ok(showInfoMessageStub.calledWithMatch(/uploaded successfully/), "Success message should be shown");
    });

    test('Upload file command - manual directory ID input', async function() {
        this.timeout(5000);
        
        showOpenDialogStub.resolves([vscode.Uri.file('/tmp/test3.txt')]);
        showInputBoxStub.onFirstCall().resolves('8'); // Directory ID
        showInputBoxStub.onSecondCall().resolves('/docs/'); // Path
        
        await vscode.commands.executeCommand('intelligent-ide.entry.upload');
        
        assert.ok(uploadFileStub.called, "uploadFile should be called");
        assert.ok(withProgressStub.called, "withProgress should be called");
    });

    test('Error handling in upload file', async function() {
        this.timeout(5000);
        
        showOpenDialogStub.resolves([vscode.Uri.file('/tmp/error.txt')]);
        uploadFileStub.rejects(new Error('Upload failed'));
        showInputBoxStub.onFirstCall().resolves('5'); // Directory ID
        showInputBoxStub.onSecondCall().resolves('/'); // Path
        
        await vscode.commands.executeCommand('intelligent-ide.entry.upload');
        
        assert.ok(showErrorMessageStub.called, "Error message should be shown");
        assert.ok(showErrorMessageStub.calledWithMatch(/Upload failed/), "Error message should mention upload failure");
    });

});