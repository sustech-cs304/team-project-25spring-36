import * as assert from 'assert';
import * as sinon from 'sinon';
import * as vscode from 'vscode';
import { assignmentService } from '../../services/AssignmentService';
import { courseService } from '../../services/CourseService';
import * as authUtils from '../../utils/authUtils';
import * as viewManager from '../../views/viewManager';
import { registerAssignmentCommands } from '../../commands/AssignmentCommands';
import { CourseTreeItem } from '../../views/CourseView';
import { ICourseHomeworkAssignment, ICourseHomeworkAssignmentStatus, ICourseHomeworkSubmission } from '../../models/AssignmentModels';
import { ICourse, ICourseDirectory, ICourseDirectoryEntry } from '../../models/CourseModels';

suite('Assignment Commands Test Suite', () => {
    let mockContext: vscode.ExtensionContext;
    let mockGlobalState: Map<string, any>;
    let mockSecrets: {
        store: sinon.SinonStub;
        get: sinon.SinonStub;
        delete: sinon.SinonStub;
    };
    let mockCommands: Record<string, (...args: any[]) => any>;
    
    // VS Code API stubs
    let showInputBoxStub: sinon.SinonStub;
    let showQuickPickStub: sinon.SinonStub;
    let showInfoMessageStub: sinon.SinonStub;
    let showErrorMessageStub: sinon.SinonStub;
    let showWarningMessageStub: sinon.SinonStub;
    let withProgressStub: sinon.SinonStub;
    
    // View manager stubs
    let refreshAllViewsStub: sinon.SinonStub;
    let refreshViewsStub: sinon.SinonStub;
    let getCourseTreeProviderStub: sinon.SinonStub;
    
    // Auth utils stub
    let getAuthDetailsStub: sinon.SinonStub;
    
    // Service stubs
    let createAssignmentStub: sinon.SinonStub;
    let updateAssignmentStub: sinon.SinonStub;
    let deleteAssignmentStub: sinon.SinonStub;
    let getAssignmentsStub: sinon.SinonStub;
    let getSubmissionsStub: sinon.SinonStub;
    let createSubmissionStub: sinon.SinonStub;
    let deleteSubmissionStub: sinon.SinonStub;
    let gradeSubmissionStub: sinon.SinonStub;
    let getAssignmentStatusesStub: sinon.SinonStub;
    
    // Course service stubs
    let getCoursesStub: sinon.SinonStub;
    let getDirectoriesStub: sinon.SinonStub;
    let getEntriesStub: sinon.SinonStub;
    
    const mockToken = 'mock-token-123';
    const mockTeacher = {
        id: 1,
        email: 'teacher@example.com',
        username: 'teacher',
        role: 'teacher' as 'teacher',
        token: mockToken
    };
    const mockStudent = {
        id: 2,
        email: 'student@example.com',
        username: 'student',
        role: 'student' as 'student',
        token: mockToken
    };
    //TODO
    const mockCourses: ICourse[] = [
        { 
            id: 1, 
            name: 'Course 1', 
            description: 'Test Course 1',
            teacher_id: 1,
            teacher_name: 'Teacher',
            created_at: '2025-05-01T10:00:00'
        },
        { 
            id: 2, 
            name: 'Course 2', 
            description: 'Test Course 2',
            teacher_id: 1,
            teacher_name: 'Teacher',
            created_at: '2025-05-02T10:00:00'
        }
    ];
    
    // Fix assignments to match ICourseHomeworkAssignment interface
    const mockAssignments: ICourseHomeworkAssignment[] = [
        { 
            id: 1, 
            course_id: 1, 
            title: 'Assignment 1', 
            description: 'Test Assignment 1', 
            deadline: '2025-05-25T23:59:59',
            course_directory_entry_ids: [1, 2],
            created_at: '2025-05-15T10:00:00',
            updated_at: '2025-05-15T10:00:00'
        },
        { 
            id: 2, 
            course_id: 1, 
            title: 'Assignment 2', 
            description: 'Test Assignment 2', 
            deadline: '2025-05-30T23:59:59', 
            course_directory_entry_ids: [2, 3],
            created_at: '2025-05-16T10:00:00',
            updated_at: '2025-05-17T10:00:00'
        }
    ];
    
    // Fix submissions to match ICourseHomeworkSubmission interface
    const mockSubmissions: ICourseHomeworkSubmission[] = [
        { 
            id: 1, 
            assignment_id: 1, 
            student_id: 2, 
            title: 'Submission 1', 
            description: 'My first submission',
            course_directory_entry_ids: [4, 5], 
            grade: null, 
            feedback: null,
            submission_date: '2025-05-20T10:00:00',
            created_at: '2025-05-20T10:00:00',
            updated_at: '2025-05-20T10:00:00'
        },
        { 
            id: 2, 
            assignment_id: 1, 
            student_id: 3, 
            title: 'Submission 2',
            description: 'My second submission',
            course_directory_entry_ids: [6],
            grade: 85, 
            feedback: 'Good job',
            submission_date: '2025-05-19T14:30:00',
            created_at: '2025-05-19T14:30:00',
            updated_at: '2025-05-19T14:35:00'
        }
    ];

const mockDirectories: ICourseDirectory[] = [
    { 
        id: 1, 
        course_id: 1, 
        name: 'Lectures',
        permission: null,
        created_at: '2025-05-01T10:00:00'
    },
    { 
        id: 2, 
        course_id: 1, 
        name: 'Assignments',
        permission: null,
        created_at: '2025-05-01T10:00:00'
    }
];

const mockEntries: ICourseDirectoryEntry[] = [
    { 
        id: 1, 
        course_directory_id: 1,
        path: '/Lectures/lecture1.pdf', 
        type: 'file',
        created_at: '2025-05-01T10:00:00',
        storage_name: 'lecture1_123456.pdf'
    },
    { 
        id: 2, 
        course_directory_id: 1,
        path: '/Lectures/lecture2.pdf', 
        type: 'file',
        created_at: '2025-05-01T10:30:00',
        storage_name: 'lecture2_123456.pdf'
    },
    { 
        id: 3, 
        course_directory_id: 2,
        path: '/Assignments/hw1.pdf', 
        type: 'file',
        created_at: '2025-05-02T10:00:00',
        storage_name: 'hw1_123456.pdf'
    },
    { 
        id: 4, 
        course_directory_id: 2,
        path: '/Assignments/submission1.pdf', 
        type: 'file',
        created_at: '2025-05-10T10:00:00',
        storage_name: 'submission1_123456.pdf'
    },
    { 
        id: 5, 
        course_directory_id: 2,
        path: '/Assignments/submission2.pdf', 
        type: 'file',
        created_at: '2025-05-10T10:30:00',
        storage_name: 'submission2_123456.pdf'
    }
];
    const mockStatuses: ICourseHomeworkAssignmentStatus[] = [
        { 
            id: 1, 
            course_id: 1, 
            title: 'Assignment 1', 
            description: 'Test Assignment 1', 
            deadline: '2025-05-25T23:59:59',
            course_directory_entry_ids: [1, 2],
            created_at: '2025-05-15T10:00:00',
            updated_at: '2025-05-15T10:00:00',
            is_overdue: false,
            is_completed: true,
            submission_count: 1,
            latest_submission_id: {
                id: 1,
                assignment_id: 1,
                student_id: 2,
                title: 'Submission 1',
                description: 'My submission',
                course_directory_entry_ids: [4, 5],
                grade: 90,
                feedback: 'Well done',
                submission_date: '2025-05-20T10:00:00',
                created_at: '2025-05-20T10:00:00',
                updated_at: '2025-05-20T10:00:00'
            }
        },
        { 
            id: 2, 
            course_id: 1, 
            title: 'Assignment 2', 
            description: 'Test Assignment 2', 
            deadline: '2025-05-30T23:59:59',
            course_directory_entry_ids: [2, 3],
            created_at: '2025-05-16T10:00:00',
            updated_at: '2025-05-17T10:00:00',
            is_overdue: false,
            is_completed: false,
            submission_count: 0,
            latest_submission_id: null
        }
    ];

    // Mock course tree provider and findEntryById method
    let mockTreeProvider: any;
    
    setup(() => {
        sinon.restore();
        mockGlobalState = new Map<string, any>();
        mockSecrets = {
            store: sinon.stub().resolves(),
            get: sinon.stub().resolves(mockToken),
            delete: sinon.stub().resolves()
        };
        mockCommands = {};
        
        // Set up mock context
        mockContext = {
            subscriptions: [],
            globalState: {
                get: (key: string) => mockGlobalState.get(key),
                update: (key: string, value: any) => {
                    mockGlobalState.set(key, value);
                    return Promise.resolve();
                }
            } as any,
            secrets: mockSecrets
        } as unknown as vscode.ExtensionContext;
        
        // Set up command registration and execution
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
        withProgressStub = sinon.stub(vscode.window, 'withProgress').callsFake((options, task) => {
            return task({ report: () => {} }, { isCancellationRequested: false, onCancellationRequested: () => ({ dispose: () => {} }) });
        });
        
        // View manager stubs
        refreshAllViewsStub = sinon.stub(viewManager, 'refreshAllViews');
        refreshViewsStub = sinon.stub(viewManager, 'refreshViews');
        
        // Mock tree provider with findEntryById method
        mockTreeProvider = {
            findEntryById: sinon.stub()
        };
        getCourseTreeProviderStub = sinon.stub(viewManager, 'getCourseTreeProvider').returns(mockTreeProvider);
        
        // Auth utils stub - default to teacher
        getAuthDetailsStub = sinon.stub(authUtils, 'getAuthDetails').resolves({ token: mockToken, loginInfo: mockTeacher });
        
        // Assignment service stubs
        createAssignmentStub = sinon.stub(assignmentService, 'createAssignment').resolves();
        updateAssignmentStub = sinon.stub(assignmentService, 'updateAssignment').resolves();
        deleteAssignmentStub = sinon.stub(assignmentService, 'deleteAssignment').resolves();
        getAssignmentsStub = sinon.stub(assignmentService, 'getAssignments').resolves(mockAssignments);
        getSubmissionsStub = sinon.stub(assignmentService, 'getSubmissions').resolves(mockSubmissions);
        createSubmissionStub = sinon.stub(assignmentService, 'createSubmission').resolves();
        deleteSubmissionStub = sinon.stub(assignmentService, 'deleteSubmission').resolves();
        gradeSubmissionStub = sinon.stub(assignmentService, 'gradeSubmission').resolves();
        getAssignmentStatusesStub = sinon.stub(assignmentService, 'getAssignmentStatuses').resolves(mockStatuses);
        
        // Course service stubs
        getCoursesStub = sinon.stub(courseService, 'getCourses').resolves(mockCourses);
        getDirectoriesStub = sinon.stub(courseService, 'getDirectories').resolves(mockDirectories);
        getEntriesStub = sinon.stub(courseService, 'getEntries').resolves(mockEntries);
        
        // Register assignment commands
        registerAssignmentCommands(mockContext);
    });
    
    teardown(() => {
        sinon.restore();
    });

    // Tests for createAssignmentCommand
    test('Create assignment - successful as teacher', async () => {
        const courseItem = {
            type: 'course',
            itemId: 1,
            label: 'Course 1'
        };
        
        showInputBoxStub.onFirstCall().resolves('New Assignment'); // Title
        showInputBoxStub.onSecondCall().resolves('Assignment Description'); // Description
        
        // Mock deadline selection
        showQuickPickStub.onFirstCall().resolves({
            label: '$(calendar) Tomorrow at 9:00 AM',
            value: () => '2025-05-21T09:00:00'
        });
        
        // Mock file selection
        showQuickPickStub.onSecondCall().resolves({ label: '$(files) Select Files' });
        showQuickPickStub.onThirdCall().resolves([
            { id: 1, label: '$(file) lecture1.pdf' },
            { id: 2, label: '$(file) lecture2.pdf' }
        ]);
        
        await vscode.commands.executeCommand('intelligent-ide.course.assignment.create', courseItem);
        
        assert.ok(createAssignmentStub.calledOnce, "Assignment creation service should be called");
        assert.ok(createAssignmentStub.firstCall.args[0] === mockToken, "Should pass token");
        assert.ok(showInfoMessageStub.calledWithMatch(/created successfully/), "Success message should be shown");
        assert.ok(refreshAllViewsStub.calledOnce, "Views should be refreshed");
    });
    
    test('Create assignment - not authorized as student', async () => {
        // Override auth to return student role
        getAuthDetailsStub.resolves({ token: mockToken, loginInfo: mockStudent });
        
        await vscode.commands.executeCommand('intelligent-ide.course.assignment.create');
        
        assert.ok(!createAssignmentStub.called, "Assignment creation should not be called");
        assert.ok(showErrorMessageStub.calledWith("Only teachers can create assignments."), 
            "Error message about teacher role should be shown");
    });

    // Tests for updateAssignmentCommand
    test('Update assignment - successful', async () => {
        const assignmentItem = {
            type: 'assignment',
            itemId: 1,
            parentId: 1,
            label: 'Assignment 1'
        };
        
        // Mock input for updates
        showInputBoxStub.onFirstCall().resolves('Updated Assignment'); // New title
        showInputBoxStub.onSecondCall().resolves('Updated Description'); // New description
        
        // Mock deadline selection - keep current
        showQuickPickStub.onFirstCall().resolves({
            label: '$(debug-step-back) Keep Current Deadline',
            value: () => '2025-05-25T23:59:59'
        });
        
        // Mock file selection
        showQuickPickStub.onSecondCall().resolves({ label: '$(files) Select Files' });
        showQuickPickStub.onThirdCall().resolves([
            { id: 2, label: '$(file) lecture2.pdf' },
            { id: 3, label: '$(file) hw1.pdf' }
        ]);
        
        await vscode.commands.executeCommand('intelligent-ide.course.assignment.update', assignmentItem);
        
        assert.ok(updateAssignmentStub.calledOnce, "Assignment update service should be called");
        assert.ok(showInfoMessageStub.calledWithMatch(/updated successfully/), "Success message should be shown");
    });
    
    // Tests for deleteAssignmentCommand
    test('Delete assignment - confirm deletion', async () => {
        const assignmentItem = {
            type: 'assignment',
            itemId: 1,
            parentId: 1,
            label: 'Assignment 1'
        };
        
        // Mock confirmation dialog
        showWarningMessageStub.resolves('Yes');
        
        await vscode.commands.executeCommand('intelligent-ide.course.assignment.delete', assignmentItem);
        
        assert.ok(deleteAssignmentStub.calledOnce, "Assignment deletion service should be called");
        assert.ok(showInfoMessageStub.calledWithMatch(/deleted successfully/), "Success message should be shown");
    });
    
    test('Delete assignment - cancel deletion', async () => {
        const assignmentItem = {
            type: 'assignment',
            itemId: 1,
            parentId: 1,
            label: 'Assignment 1'
        };
        
        // Mock cancellation of confirmation dialog
        showWarningMessageStub.resolves(undefined);
        
        await vscode.commands.executeCommand('intelligent-ide.course.assignment.delete', assignmentItem);
        
        assert.ok(!deleteAssignmentStub.called, "Assignment deletion service should not be called");
    });
    
    // Tests for viewSubmissionsCommand
    test('View submissions - show list and select one', async () => {
        const assignmentItem = {
            type: 'assignment',
            itemId: 1,
            parentId: 1,
            label: 'Assignment 1'
        };
        
        // Mock submission selection
        showQuickPickStub.resolves({
            id: 1,
            label: 'Submission 1',
            description: sinon.match(/Submitted:/)
        });
        
        await vscode.commands.executeCommand('intelligent-ide.course.assignment.viewSubmissions', assignmentItem);
        
        assert.ok(getSubmissionsStub.calledOnce, "Get submissions service should be called");
        assert.deepStrictEqual(
            getSubmissionsStub.firstCall.args[1],
            { assignment_id: 1 },
            "Should request submissions for correct assignment"
        );
    });
    
    // Tests for submitToAssignmentCommand
    test('Submit to assignment - successful as student', async () => {
        // Override auth to return student role
        getAuthDetailsStub.resolves({ token: mockToken, loginInfo: mockStudent });
        
        const assignmentItem = {
            type: 'assignment',
            itemId: 1,
            parentId: 1,
            label: 'Assignment 1'
        };
        
        // Mock inputs
        showInputBoxStub.onFirstCall().resolves('My Submission'); // Title
        showInputBoxStub.onSecondCall().resolves('This is my homework submission'); // Description
        
        // Mock file selection
        showQuickPickStub.onFirstCall().resolves({ label: '$(files) Select Files' });
        showQuickPickStub.onSecondCall().resolves([{ id: 4, label: '$(file) submission1.pdf' }]);
        
        await vscode.commands.executeCommand('intelligent-ide.course.assignment.submit', assignmentItem);
        
        assert.ok(createSubmissionStub.calledOnce, "Create submission service should be called");
        assert.ok(showInfoMessageStub.calledWithMatch(/successful/), "Success message should be shown");
    });
    
    // Tests for viewAssignmentStatusCommand
    test('View assignment status - show status details', async () => {
        const assignmentItem = {
            type: 'assignment',
            itemId: 1,
            parentId: 1,
            label: 'Assignment 1'
        };
        
        await vscode.commands.executeCommand('intelligent-ide.course.assignment.viewStatus', assignmentItem);
        
        assert.ok(getAssignmentStatusesStub.calledOnce, "Get assignment statuses service should be called");
        assert.strictEqual(getAssignmentStatusesStub.firstCall.args[1], 1, "Should get statuses for correct course");
    });
    
    // Tests for gradeSubmissionCommand
    test('Grade submission - successful as teacher', async () => {
        const submissionItem = {
            type: 'submission',
            itemId: 1,
            parentId: 1, // assignment ID
            label: 'Submission 1'
        };
        
        // Mock inputs
        showInputBoxStub.onFirstCall().resolves('90'); // Grade
        showInputBoxStub.onSecondCall().resolves('Good job on the assignment!'); // Feedback
        
        await vscode.commands.executeCommand('intelligent-ide.course.submission.grade', submissionItem);
        
        assert.ok(gradeSubmissionStub.calledOnce, "Grade submission service should be called");
        assert.ok(showInfoMessageStub.calledWithMatch(/graded successfully/), "Success message should be shown");
    });
    
    // Tests for deleteSubmissionCommand
    test('Delete submission - confirm deletion', async () => {
        const submissionItem = {
            type: 'submission',
            itemId: 1,
            parentId: 1,
            label: 'Submission 1'
        };
        
        // Mock confirmation dialog
        showWarningMessageStub.resolves('Yes');
        
        await vscode.commands.executeCommand('intelligent-ide.course.submission.delete', submissionItem);
        
        assert.ok(deleteSubmissionStub.calledOnce, "Submission deletion service should be called");
        assert.ok(showInfoMessageStub.calledWithMatch(/deleted successfully/), "Success message should be shown");
    });
    
    // Tests for viewAttachmentsCommand
    test('View attachments - assignment attachments', async () => {
        const assignmentItem = {
            type: 'assignment',
            itemId: 1,
            parentId: 1,
            label: 'Assignment 1',
            assignment: {
                id: 1,
                course_id: 1,
                title: 'Assignment 1',
                description: 'Test Assignment 1',
                deadline: '2025-05-25T23:59:59',
                course_directory_entry_ids: [1, 2],
                created_at: '2025-05-15T10:00:00',
                updated_at: '2025-05-15T10:00:00'
            }
        };
        
        // Mock tree provider to return entries
        mockTreeProvider.findEntryById.callsFake((id: number) => {
            return mockEntries.find(e => e.id === id);
        });
        
        // Mock attachment selection
        showQuickPickStub.resolves({
            label: 'lecture1.pdf',
            description: 'Type: file',
            detail: '/Lectures/lecture1.pdf',
            entry: mockEntries[0]
        });
        
        await vscode.commands.executeCommand('intelligent-ide.course.viewAttachments', assignmentItem);
        
    });
    
    test('View attachments - no attachments available', async () => {
        const assignmentItem = {
            type: 'assignment',
            itemId: 1,
            parentId: 1,
            label: 'Assignment 1',
            assignment: {
                id: 1,
                course_id: 1,
                title: 'Assignment 1',
                description: 'Test Assignment 1',
                deadline: '2025-05-25T23:59:59',
                course_directory_entry_ids: [], // Changed from string to empty array
                created_at: '2025-05-15T10:00:00',
                updated_at: '2025-05-15T10:00:00'
            }
        };
        
        await vscode.commands.executeCommand('intelligent-ide.course.viewAttachments', assignmentItem);
        
        assert.ok(showInfoMessageStub.calledWith('No attachments available.'), "Should show no attachments message");
    });
    
    // Error handling tests
    test('Create assignment - error handling', async () => {
        const courseItem = { type: 'course', itemId: 1 };
        
        showInputBoxStub.onFirstCall().resolves('New Assignment'); // Title
        showInputBoxStub.onSecondCall().resolves('Assignment Description'); // Description
        
        // Mock deadline selection
        showQuickPickStub.onFirstCall().resolves({
            label: '$(calendar) Tomorrow at 9:00 AM',
            value: () => '2025-05-21T09:00:00'
        });
        
        // Mock file selection
        showQuickPickStub.onSecondCall().resolves({ label: '$(files) Select Files' });
        showQuickPickStub.onThirdCall().resolves([{ id: 1, label: '$(file) lecture1.pdf' }]);
        
        // Simulate an error
        createAssignmentStub.rejects(new Error('API Error'));
        
        await vscode.commands.executeCommand('intelligent-ide.course.assignment.create', courseItem);
        
        assert.ok(showErrorMessageStub.calledWithMatch(/Failed to create assignment/), 
            "Should display error message");
    });
});
// Fix directory interfaces to match actual models
