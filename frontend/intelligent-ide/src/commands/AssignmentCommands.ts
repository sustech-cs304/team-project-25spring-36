import * as vscode from 'vscode';
import { assignmentService } from '../services/AssignmentService';
import { courseService } from '../services/CourseService';
import { getAuthDetails } from '../utils/authUtils';
import { CourseTreeItem } from '../views/CourseView';
import { refreshAllViews, ViewType, refreshViews, getCourseTreeProvider } from '../views/viewManager';
import {
    ICourseHomeworkAssignmentCreateRequest,
    ICourseHomeworkAssignmentUpdateRequest,
    ICourseHomeworkSubmissionCreateRequest,
    ICourseHomeworkSubmissionGradeRequest,
    ICourseHomeworkAssignment,
    ICourseHomeworkSubmission,
    ICourseHomeworkAssignmentStatus
} from '../models/AssignmentModels';
import { ICourse, ICourseDirectoryEntry } from '../models/CourseModels';

// --- Main Registration Function ---
export function registerAssignmentCommands(context: vscode.ExtensionContext): void {
    registerCreateAssignmentCommand(context);
    registerUpdateAssignmentCommand(context);
    registerDeleteAssignmentCommand(context);
    registerViewSubmissionsCommand(context);
    registerSubmitToAssignmentCommand(context);
    registerViewAssignmentStatusCommand(context);
    registerGradeSubmissionCommand(context);
    registerDeleteSubmissionCommand(context);
    registerViewAttachmentsCommand(context);
}
// --- Command Implementations ---

function registerCreateAssignmentCommand(context: vscode.ExtensionContext): void {
    context.subscriptions.push(vscode.commands.registerCommand('intelligent-ide.course.assignment.create', async (item?: CourseTreeItem) => {
        const auth = await getAuthDetails(context);
        if (!auth || auth.loginInfo.role !== 'teacher') {
            vscode.window.showErrorMessage("Only teachers can create assignments.");
            return;
        }
        const courseId = await getCourseId(auth.token, auth.loginInfo.role, item);
        if (!courseId) {
            vscode.window.showInformationMessage("Assignment creation cancelled: No course selected.");
            return;
        }

        const title = await vscode.window.showInputBox({ prompt: "Assignment Title", validateInput: text => text ? null : "Title cannot be empty" });
        if (title === undefined) { return; }

        const description = await vscode.window.showInputBox({ prompt: "Assignment Description (optional)" });
        if (description === undefined) { return; }

        const deadline = await selectDeadline();
        if (deadline === undefined) {
            vscode.window.showInformationMessage("Assignment creation cancelled: No deadline provided.");
            return;
        }

        const selectedFileIds = await selectCourseFiles(auth.token, courseId);
        if (selectedFileIds === undefined) {
            vscode.window.showInformationMessage("Assignment creation cancelled: File selection failed or was cancelled.");
            return;
        }

        const assignmentData: ICourseHomeworkAssignmentCreateRequest = {
            course_id: courseId, title, description: description || null, deadline, course_directory_entry_ids: selectedFileIds
        };

        try {
            await vscode.window.withProgress({ location: vscode.ProgressLocation.Notification, title: "Creating Assignment..." }, async () => {
                await assignmentService.createAssignment(auth.token, assignmentData);
            });
            vscode.window.showInformationMessage(`Assignment "${title}" created successfully.`);
            refreshAllViews();
        } catch (error: any) {
            vscode.window.showErrorMessage(`Failed to create assignment: ${error.message}`);
        }
    }));
}

function registerUpdateAssignmentCommand(context: vscode.ExtensionContext): void {
    context.subscriptions.push(vscode.commands.registerCommand('intelligent-ide.course.assignment.update', async (item?: CourseTreeItem) => {
        const auth = await getAuthDetails(context);
        if (!auth || auth.loginInfo.role !== 'teacher') {
            vscode.window.showErrorMessage("Only teachers can update assignments.");
            return;
        }

        const courseId = await getCourseId(auth.token, auth.loginInfo.role, item);
        if (!courseId) { return; }

        const assignmentId = await getAssignmentId(auth.token, courseId, item);
        if (!assignmentId) { return; }

        let existingAssignment: ICourseHomeworkAssignment | undefined;
        try {
            const assignments = await assignmentService.getAssignments(auth.token, courseId);
            existingAssignment = assignments.find(a => Number(a.id) === Number(assignmentId));
            if (!existingAssignment) {
                vscode.window.showErrorMessage(`Assignment with ID ${assignmentId} not found.`);
                return;
            }
        } catch (e: any) {
            vscode.window.showErrorMessage(`Failed to fetch existing assignment details: ${e.message}`);
            return;
        }

        const newTitle = await vscode.window.showInputBox({ prompt: "New Assignment Title", value: existingAssignment.title || "", placeHolder: "Leave blank to keep current" });
        if (newTitle === undefined) { return; }

        const newDescription = await vscode.window.showInputBox({ prompt: "New Assignment Description", value: existingAssignment.description || "", placeHolder: "Leave blank to keep current" });
        if (newDescription === undefined) { return; }

        const newDeadline = await selectDeadline(existingAssignment.deadline || undefined);
        if (newDeadline === undefined && existingAssignment.deadline) {
            vscode.window.showInformationMessage("Assignment update cancelled: Deadline selection was cancelled.");
            return;
        }


        const newSelectedFileIds = await selectCourseFiles(auth.token, courseId, existingAssignment.course_directory_entry_ids);


        const updateData: ICourseHomeworkAssignmentUpdateRequest = { assignment_id: assignmentId };
        let changesMade = false;

        if (newTitle !== existingAssignment.title && newTitle.trim() !== "") {
            updateData.title = newTitle;
            changesMade = true;
        }
        if (newDescription !== existingAssignment.description && newDescription.trim() !== "") {
            updateData.description = newDescription;
            changesMade = true;
        }

        // Only update deadline if newDeadline is not undefined (meaning it was either selected, or "Keep Current" was chosen, or it's a new assignment)
        // AND it's different from the existing one.
        if (newDeadline !== undefined && newDeadline !== existingAssignment.deadline) {
            updateData.deadline = newDeadline;
            changesMade = true;
        }


        if (newSelectedFileIds !== undefined) {

            // Convert the string representation to an array
            let existingEntryIds: number[] = [];
            if (typeof existingAssignment.course_directory_entry_ids === 'string') {
                existingEntryIds = JSON.parse(existingAssignment.course_directory_entry_ids);
            }
            const existingIdsStr = [...existingEntryIds].sort().join(',');
            const newIdsStr = [...newSelectedFileIds].sort().join(',');

            if (existingIdsStr !== newIdsStr) {
                updateData.course_directory_entry_ids = newSelectedFileIds;
                changesMade = true;
            }
        }

        if (!changesMade) {
            vscode.window.showInformationMessage("No changes detected to update.");
            return;
        }

        try {
            await vscode.window.withProgress({ location: vscode.ProgressLocation.Notification, title: "Updating Assignment..." }, async () => {
                await assignmentService.updateAssignment(auth.token, updateData);
            });
            vscode.window.showInformationMessage(`Assignment ID ${assignmentId} updated successfully.`);
            refreshAllViews();
        } catch (error: any) {
            vscode.window.showErrorMessage(`Failed to update assignment: ${error.message}`);
        }
    }));
}

function registerDeleteAssignmentCommand(context: vscode.ExtensionContext): void {
    context.subscriptions.push(vscode.commands.registerCommand('intelligent-ide.course.assignment.delete', async (item?: CourseTreeItem) => {
        const auth = await getAuthDetails(context);
        if (!auth || auth.loginInfo.role !== 'teacher') {
            vscode.window.showErrorMessage("Only teachers can delete assignments.");
            return;
        }
        const courseId = await getCourseId(auth.token, auth.loginInfo.role, item);
        if (!courseId) { return; }

        const assignmentId = await getAssignmentId(auth.token, courseId, item);
        if (!assignmentId) { return; }

        const assignmentLabel = item?.label || `ID ${assignmentId}`;
        const confirmation = await vscode.window.showWarningMessage(`Are you sure you want to delete assignment "${assignmentLabel}"?`, { modal: true }, "Yes");
        if (confirmation !== "Yes") { return; }

        try {
            await assignmentService.deleteAssignment(auth.token, assignmentId);
            vscode.window.showInformationMessage(`Assignment "${assignmentLabel}" deleted successfully.`);
            refreshAllViews();
        } catch (error: any) {
            vscode.window.showErrorMessage(`Failed to delete assignment: ${error.message}`);
        }
    }));
}

function registerViewSubmissionsCommand(context: vscode.ExtensionContext): void {
    context.subscriptions.push(vscode.commands.registerCommand('intelligent-ide.course.assignment.viewSubmissions', async (item?: CourseTreeItem) => {
        const auth = await getAuthDetails(context);
        if (!auth || auth.loginInfo.role !== 'teacher') {
            vscode.window.showErrorMessage("Only teachers can view all submissions for an assignment.");
            return;
        }
        const courseId = await getCourseId(auth.token, auth.loginInfo.role, item);
        if (!courseId) { return; }

        const assignmentId = await getAssignmentId(auth.token, courseId, item);
        if (!assignmentId) { return; }

        try {
            const submissions = await assignmentService.getSubmissions(auth.token, { assignment_id: assignmentId });
            if (!submissions || submissions.length === 0) {
                vscode.window.showInformationMessage("No submissions found for this assignment.");
                return;
            }
            const submissionPicks = submissions.map(sub => ({
                label: sub.title || `Submission by Student ID ${sub.student_id}`,
                description: `Submitted: ${new Date(sub.created_at).toLocaleString()}, Grade: ${sub.grade ?? 'Not Graded'}`,
                id: sub.id,
                studentId: sub.student_id
            }));
            const selected = await vscode.window.showQuickPick(submissionPicks, { placeHolder: "Select a submission to view details or grade" });
            if (selected) {
                vscode.commands.executeCommand('intelligent-ide.course.submission.grade', { itemId: selected.id, parentId: assignmentId, contextValue: 'submissionItem', label: selected.label });
            }
        } catch (error: any) {
            vscode.window.showErrorMessage(`Failed to fetch submissions: ${error.message}`);
        }
    }));
}

function registerSubmitToAssignmentCommand(context: vscode.ExtensionContext): void {
    context.subscriptions.push(vscode.commands.registerCommand('intelligent-ide.course.assignment.submit', async (item?: CourseTreeItem) => {
        const auth = await getAuthDetails(context);
        if (!auth || auth.loginInfo.role !== 'student') {
            vscode.window.showErrorMessage("Only students can submit to assignments.");
            return;
        }
        const courseId = await getCourseId(auth.token, auth.loginInfo.role, item);
        if (!courseId) { return; }

        const assignmentId = await getAssignmentId(auth.token, courseId, item);
        if (!assignmentId) { return; }

        const title = await vscode.window.showInputBox({ prompt: "Submission Title (optional)" });
        if (title === undefined) { return; }

        const description = await vscode.window.showInputBox({ prompt: "Submission Description/Comment (optional)" });
        if (description === undefined) { return; }

        const selectedFileIds = await selectCourseFiles(auth.token, courseId);
        if (selectedFileIds === undefined || selectedFileIds.length === 0) {
            vscode.window.showInformationMessage("Submission cancelled: No files selected or file selection failed.");
            return;
        }

        const submissionData: ICourseHomeworkSubmissionCreateRequest = {
            assignment_id: assignmentId,
            title: title || null,
            description: description || null,
            course_directory_entry_ids: selectedFileIds
        };

        try {
            await vscode.window.withProgress({ location: vscode.ProgressLocation.Notification, title: "Submitting Assignment..." }, async () => {
                await assignmentService.createSubmission(auth.token, submissionData);
            });
            vscode.window.showInformationMessage(`Submission for assignment ID ${assignmentId} successful.`);
            refreshAllViews();
        } catch (error: any) {
            vscode.window.showErrorMessage(`Failed to submit assignment: ${error.message}`);
        }
    }));
}

function registerViewAssignmentStatusCommand(context: vscode.ExtensionContext): void {
    context.subscriptions.push(vscode.commands.registerCommand('intelligent-ide.course.assignment.viewStatus', async (item?: CourseTreeItem) => {
        const auth = await getAuthDetails(context);
        if (!auth) { return; }

        // Get the course ID for fetching statuses
        const courseId = await getCourseId(auth.token, auth.loginInfo.role, item);
        if (!courseId) { return; }

        try {
            const statuses = await assignmentService.getAssignmentStatuses(auth.token, courseId);
            if (!statuses || statuses.length === 0) {
                vscode.window.showInformationMessage(`No assignments found or no status available for course ${courseId}.`);
                return;
            }

            // If the command was triggered directly from an assignment item, use that assignment's ID
            let selectedAssignmentId: number | undefined;
            if (item && (item.type === 'assignment' || item.contextValue === 'assignmentItem')) {
                if (typeof item.itemId === 'number') {
                    selectedAssignmentId = item.itemId;
                } else if (typeof item.itemId === 'string' && !isNaN(Number(item.itemId))) {
                    selectedAssignmentId = Number(item.itemId);
                }
            }

            let fullStatus: ICourseHomeworkAssignmentStatus | undefined;

            // If we have an assignment ID from the context, find its status directly
            if (selectedAssignmentId) {
                fullStatus = statuses.find(s => Number(s.id) === Number(selectedAssignmentId));
                if (!fullStatus) {
                    vscode.window.showWarningMessage(`Could not find status for assignment ID ${selectedAssignmentId}`);
                    return;
                }
            } else {
                // Otherwise, show the QuickPick for the user to select an assignment
                const statusPicks = statuses.map(status => ({
                    label: `${status.title || "Untitled Assignment"}`,
                    description: `Status: ${status.is_completed ? 'Completed' : (status.is_overdue ? 'Overdue' : 'Pending')} (${status.submission_count} submissions)`,
                    detail: `Deadline: ${status.deadline ? new Date(status.deadline).toLocaleString() : 'N/A'}. ${status.latest_submission_id?.grade ? 'Latest Grade: ' + status.latest_submission_id.grade : ''}`,
                    id: status.id
                }));

                const selectedStatus = await vscode.window.showQuickPick(statusPicks, {
                    placeHolder: "Select an assignment to view its status details"
                });

                if (!selectedStatus) {
                    return; // User cancelled
                }

                fullStatus = statuses.find(s => Number(s.id) === Number(selectedStatus.id));
            }

            if (fullStatus) {
                let detailMessage = `Assignment: ${fullStatus.title}\n`;
                detailMessage += `Description: ${fullStatus.description || 'N/A'}\n`;
                detailMessage += `Deadline: ${fullStatus.deadline ? new Date(fullStatus.deadline).toLocaleString() : 'N/A'}\n`;
                detailMessage += `Overdue: ${fullStatus.is_overdue ? 'Yes' : 'No'}\n`;
                detailMessage += `Completed: ${fullStatus.is_completed ? 'Yes' : 'No'}\n`;
                detailMessage += `Submissions: ${fullStatus.submission_count}\n`;

                if (fullStatus.latest_submission_id) {
                    detailMessage += `Latest Submission: ${new Date(fullStatus.latest_submission_id.created_at).toLocaleString()}\n`;
                    detailMessage += `  Grade: ${fullStatus.latest_submission_id.grade ?? 'Not Graded'}\n`;
                    detailMessage += `  Feedback: ${fullStatus.latest_submission_id.feedback || 'No Feedback'}\n`;
                }

                vscode.window.showInformationMessage(detailMessage, { modal: true });
            }
        } catch (error: any) {
            vscode.window.showErrorMessage(`Failed to get assignment statuses: ${error.message}`);
        }
    }));
}

function registerGradeSubmissionCommand(context: vscode.ExtensionContext): void {
    context.subscriptions.push(vscode.commands.registerCommand('intelligent-ide.course.submission.grade', async (item?: CourseTreeItem) => {
        const auth = await getAuthDetails(context);
        if (!auth || auth.loginInfo.role !== 'teacher') {
            vscode.window.showErrorMessage("Only teachers can grade submissions.");
            return;
        }

        // We need assignmentId to list submissions if submissionId is not directly provided by item
        // This part might need refinement based on how 'item' is structured when this command is called
        let assignmentId = item?.parentId as number | undefined; // Assuming parentId of submissionItem is assignmentId
        let submissionId = item?.itemId as number | undefined;

        if (!submissionId) {
            const courseIdForContext = await getCourseId(auth.token, auth.loginInfo.role); // Get any course to start
            if (!courseIdForContext) { return; }
            const tempAssignmentId = await getAssignmentId(auth.token, courseIdForContext);
            if (!tempAssignmentId) { return; }
            assignmentId = tempAssignmentId;
            submissionId = await getSubmissionId(auth.token, assignmentId, item);
        }
        if (!submissionId) { return; }
        // TODO
        // teacher should be able to review the attachments of the submission

        const gradeStr = await vscode.window.showInputBox({
            prompt: "Enter Grade (numeric)",
            validateInput: text => !text ? "Grade cannot be empty." : (isNaN(parseFloat(text)) ? "Grade must be a number." : null)
        });
        if (gradeStr === undefined) { return; }
        const grade = parseFloat(gradeStr);

        const feedback = await vscode.window.showInputBox({ prompt: "Enter Feedback (optional)" });
        if (feedback === undefined) { return; }

        const gradeData: ICourseHomeworkSubmissionGradeRequest = {
            submission_id: submissionId,
            grade: grade,
            feedback: feedback || null
        };

        try {
            await assignmentService.gradeSubmission(auth.token, gradeData);
            vscode.window.showInformationMessage(`Submission ID ${submissionId} graded successfully.`);
            refreshAllViews();
        } catch (error: any) {
            vscode.window.showErrorMessage(`Failed to grade submission: ${error.message}`);
        }
    }));
}

function registerDeleteSubmissionCommand(context: vscode.ExtensionContext): void {
    context.subscriptions.push(vscode.commands.registerCommand('intelligent-ide.course.submission.delete', async (item?: CourseTreeItem) => {
        const auth = await getAuthDetails(context);
        if (!auth || auth.loginInfo.role !== 'teacher') {
            vscode.window.showErrorMessage("Only teachers can delete submissions.");
            return;
        }

        let assignmentId = item?.parentId as number | undefined;
        let submissionId = item?.itemId as number | undefined;

        if (!submissionId) {
            const courseIdForContext = await getCourseId(auth.token, auth.loginInfo.role);
            if (!courseIdForContext) { return; }
            const tempAssignmentId = await getAssignmentId(auth.token, courseIdForContext);
            if (!tempAssignmentId) { return; }
            assignmentId = tempAssignmentId;
            submissionId = await getSubmissionId(auth.token, assignmentId, item);
        }
        if (!submissionId) { return; }

        const submissionLabel = item?.label || `ID ${submissionId}`;
        const confirmation = await vscode.window.showWarningMessage(`Are you sure you want to delete submission "${submissionLabel}"?`, { modal: true }, "Yes");
        if (confirmation !== "Yes") { return; }

        try {
            await assignmentService.deleteSubmission(auth.token, submissionId);
            vscode.window.showInformationMessage(`Submission "${submissionLabel}" deleted successfully.`);
            refreshAllViews();
        } catch (error: any) {
            vscode.window.showErrorMessage(`Failed to delete submission: ${error.message}`);
        }
    }));
}

function registerViewAttachmentsCommand(context: vscode.ExtensionContext): void {
    context.subscriptions.push(
        vscode.commands.registerCommand('intelligent-ide.course.viewAttachments', async (item: CourseTreeItem) => {
            const auth = await getAuthDetails(context);
            if (!auth) { return; }

            try {
                let entryIds: number[] = [];
                let title = '';

                // Extract entry IDs from assignment or submission
                if (item.type === 'assignment' && item.assignment?.course_directory_entry_ids) {
                    entryIds = item.assignment.course_directory_entry_ids;
                    title = `Attachments for Assignment: ${item.label}`;
                } else if (item.type === 'submission' && item.submission?.course_directory_entry_ids) {
                    entryIds = item.submission.course_directory_entry_ids;
                    title = `Attachments for Submission: ${item.label}`;
                }

                if (entryIds.length === 0) {
                    vscode.window.showInformationMessage('No attachments available.');
                    return;
                }

                // Try to find entries in the cache first
                const treeProvider = getCourseTreeProvider();
                const attachments: ICourseDirectoryEntry[] = [];

                for (const entryId of entryIds) {
                    // Try the cache first
                    let entry = treeProvider?.findEntryById(entryId);

                    if (entry) {
                        attachments.push(entry);
                    }
                }

                if (attachments.length === 0) {
                    return;
                }

                // Create QuickPick items from attachments
                const items = attachments.map(entry => ({
                    label: entry.path.split('/').pop() || entry.path,
                    description: `Type: ${entry.type}`,
                    detail: entry.path,
                    entry: entry
                }));

                // Show QuickPick with attachments
                const selectedItem = await vscode.window.showQuickPick(items, {
                    placeHolder: `Select an attachment to open (${attachments.length} available)`,
                    title
                });

                if (selectedItem) {
                    // Open the selected attachment using the existing file opening command
                    const treeItem = new CourseTreeItem(
                        selectedItem.label,
                        vscode.TreeItemCollapsibleState.None,
                        'entry',
                        selectedItem.entry.id,
                        undefined,
                        selectedItem.entry.path,
                        selectedItem.entry.type === 'directory',
                        selectedItem.entry
                    );

                    await vscode.commands.executeCommand('intelligent-ide.course.openFile', treeItem);
                }
            } catch (error: any) {
                vscode.window.showErrorMessage(`Error loading attachments: ${error.message}`);
            }
        })
    );
}
// --- Helper Functions ---

async function getCourseId(token: string, loginRole: string, item?: CourseTreeItem): Promise<number | undefined> {
    if (item) {

        // Direct course item
        if (item.type === 'course') {
            if (typeof item.itemId === 'number') {
                return item.itemId;
            } else if (typeof item.itemId === 'string' && !isNaN(Number(item.itemId))) {
                return Number(item.itemId);
            }
        }

        // Assignment item (where parentId is the course ID)
        if (item.type === 'assignment' || item.contextValue === 'assignmentItem') {
            if (typeof item.parentId === 'number') {
                return item.parentId;
            } else if (typeof item.parentId === 'string' && !isNaN(Number(item.parentId))) {
                return Number(item.parentId);
            }
        }

        // Assignment folder (where parentId is the course ID)
        if (item.type === 'assignment-folder' || item.contextValue === 'assignmentFolder') {
            if (typeof item.parentId === 'number') {
                return item.parentId;
            } else if (typeof item.parentId === 'string' && !isNaN(Number(item.parentId))) {
                return Number(item.parentId);
            }
        }

        // Submission (where parentId might lead to assignment, which leads to course)
        if (item.type === 'submission' || item.contextValue === 'submissionItem') {
            // Try to get assignment ID first (as parentId of submission)
            let assignmentId: number | undefined;

            if (typeof item.parentId === 'number') {
                assignmentId = item.parentId;
            } else if (typeof item.parentId === 'string' && !isNaN(Number(item.parentId))) {
                assignmentId = Number(item.parentId);
            }

            if (assignmentId) {
                try {
                    const assignments = await assignmentService.getAssignments(token, 0); // Getting all assignments
                    const assignment = assignments.find(a => Number(a.id) === Number(assignmentId));
                    if (assignment) {
                        return assignment.course_id;
                    }
                } catch (error) {
                    console.error("Error fetching assignment for course ID:", error);
                }
            }
        }
    }

    // Fallback to manual selection if we couldn't determine from context
    try {
        const courses = await courseService.getCourses(token, loginRole);
        if (!courses || courses.length === 0) {
            vscode.window.showInformationMessage("No courses available to select.");
            return undefined;
        }
        const coursePicks = courses.map(course => ({ label: course.name, description: `ID: ${course.id}`, id: course.id }));
        const selectedCourse = await vscode.window.showQuickPick(coursePicks, { placeHolder: "Select a course" });
        return selectedCourse?.id;
    } catch (error: any) {
        vscode.window.showErrorMessage(`Failed to fetch courses: ${error.message}`);
        const courseIdStr = await vscode.window.showInputBox({ prompt: "Enter Course ID manually" });
        return courseIdStr ? parseInt(courseIdStr) : undefined;
    }
}

async function getAssignmentId(token: string, courseId: number, item?: CourseTreeItem): Promise<number | undefined> {
    if (item) {

        // Direct assignment item check
        if (item.type === 'assignment' || item.contextValue === 'assignmentItem') {
            if (typeof item.itemId === 'number') {
                return item.itemId;
            } else if (typeof item.itemId === 'string' && !isNaN(Number(item.itemId))) {
                return Number(item.itemId);
            }
        }

        // Parent of submission item is assignment
        if ((item.type === 'submission' || item.contextValue === 'submissionItem') && item.parentId) {
            if (typeof item.parentId === 'number') {
                return item.parentId;
            } else if (typeof item.parentId === 'string' && !isNaN(Number(item.parentId))) {
                return Number(item.parentId);
            }
        }
    }

    // Fallback to selection
    try {
        const assignments = await assignmentService.getAssignments(token, courseId);
        if (!assignments || assignments.length === 0) {
            vscode.window.showInformationMessage(`No assignments found for course ID ${courseId}.`);
            return undefined;
        }
        const assignmentPicks = assignments.map(assignment => ({ label: assignment.title || "Untitled Assignment", description: `ID: ${assignment.id}`, id: assignment.id as number }));
        const selectedAssignment = await vscode.window.showQuickPick(assignmentPicks, { placeHolder: "Select an assignment" });
        return selectedAssignment?.id;
    } catch (error: any) {
        vscode.window.showErrorMessage(`Failed to fetch assignments: ${error.message}`);
        const assignmentIdStr = await vscode.window.showInputBox({ prompt: `Enter Assignment ID for course ${courseId} manually` });
        return assignmentIdStr ? parseInt(assignmentIdStr) : undefined;
    }
}

async function getSubmissionId(token: string, assignmentId: number, item?: CourseTreeItem, studentId?: number): Promise<number | undefined> {
    if (item) {

        // Direct submission item
        if (item.type === 'submission' || item.contextValue === 'submissionItem') {
            if (typeof item.itemId === 'number') {
                return item.itemId;
            } else if (typeof item.itemId === 'string' && !isNaN(Number(item.itemId))) {
                return Number(item.itemId);
            }
        }
    }

    // Fallback to selection
    try {
        const submissions = await assignmentService.getSubmissions(token, { assignment_id: assignmentId, student_id: studentId });
        if (!submissions || submissions.length === 0) {
            vscode.window.showInformationMessage(`No submissions found for assignment ID ${assignmentId}` + (studentId ? ` by student ID ${studentId}` : ''));
            return undefined;
        }
        const submissionPicks = submissions.map(sub => ({
            label: sub.title || `Submission ID: ${sub.id}`,
            description: `Student ID: ${sub.student_id}, Submitted: ${new Date(sub.created_at).toLocaleString()}`,
            id: sub.id
        }));
        const selectedSubmission = await vscode.window.showQuickPick(submissionPicks, { placeHolder: "Select a submission" });
        return selectedSubmission?.id;
    } catch (error: any) {
        vscode.window.showErrorMessage(`Failed to fetch submissions: ${error.message}`);
        const submissionIdStr = await vscode.window.showInputBox({ prompt: `Enter Submission ID for assignment ${assignmentId} manually` });
        return submissionIdStr ? parseInt(submissionIdStr) : undefined;
    }
}

async function selectCourseFiles(token: string, courseId: number, preselectedIds?: number[]): Promise<number[] | undefined> {
    try {
        // Fetch all directories first
        const directories = await courseService.getDirectories(token, courseId);

        if (!directories || directories.length === 0) {
            // If no directories, offer to create one with QuickPick instead of message
            const noDirsOptions = [
                { label: "$(plus) Create Directory", description: "Create a new directory for this course", action: "create" },
                { label: "$(x) Cancel", description: "Cancel file selection", action: "cancel" }
            ];

            const noDirsChoice = await vscode.window.showQuickPick(noDirsOptions, {
                placeHolder: "No directories found. What would you like to do?"
            });

            if (noDirsChoice?.action === "create") {
                await vscode.commands.executeCommand('intelligent-ide.directory.post', courseId);
                return selectCourseFiles(token, courseId, preselectedIds);
            }
            return undefined;
        }

        // Fetch all entries from all directories
        const allEntries: (ICourseDirectoryEntry & { directoryName: string })[] = [];
        for (const dir of directories) {
            try {
                const entries = await courseService.getEntries(token, dir.id, "/", true);
                entries.forEach(entry => {
                    if (entry.type !== 'directory') {
                        allEntries.push({ ...entry, directoryName: dir.name });
                    }
                });
            } catch (error: any) {
                if (error.message?.includes('No entries found')) {
                    continue;
                }
                throw error;
            }
        }

        // First, show a QuickPick for the action selection
        const actionItems: (vscode.QuickPickItem & { action?: string })[] = [
            { label: "$(files) Select Files", description: "Choose files to attach" },
            { label: "$(cloud-upload) Upload New File", description: "Upload a file to the course", action: "upload" },
            { label: "$(new-folder) Create Directory", description: "Create a new directory in the course", action: "create" }
        ];

        const actionSelection = await vscode.window.showQuickPick(actionItems, {
            placeHolder: "What would you like to do?",
            canPickMany: false  // Only one action can be selected
        });

        if (!actionSelection) {
            return undefined; // User cancelled
        }

        // Handle actions
        if (actionSelection.action === "upload") {
            // Handle directory selection for upload - no changes needed here
            const dirPicks = directories.map(d => ({
                label: d.name || "Root",
                description: `ID: ${d.id}`,
                id: d.id,
                path: d.name ? `/${d.name}/` : '/'
            }));

            const selectedDirPick = await vscode.window.showQuickPick(dirPicks, {
                placeHolder: "Select a directory to upload the file into"
            });

            if (selectedDirPick?.id !== undefined) {
                await vscode.commands.executeCommand('intelligent-ide.entry.upload', {
                    directoryId: selectedDirPick.id,
                    initialPath: selectedDirPick.path
                });
                return selectCourseFiles(token, courseId, preselectedIds);
            }
            return undefined;
        } else if (actionSelection.action === "create") {
            await vscode.commands.executeCommand('intelligent-ide.directory.post', courseId);
            return selectCourseFiles(token, courseId, preselectedIds);
        }

        if (allEntries.length === 0) {
            vscode.window.showInformationMessage("No files available. Please upload files first.");
            return undefined;
        }

        // Show file selection QuickPick
        const filePickItems = allEntries.map(entry => ({
            label: `$(file) ${entry.path.split('/').pop() || entry.path}`,
            description: `${entry.directoryName}`,
            detail: `ID: ${entry.id}`,
            id: entry.id,
            picked: preselectedIds?.includes(entry.id)
        }));

        const fileSelections = await vscode.window.showQuickPick(filePickItems, {
            placeHolder: "Select files to attach (you can select multiple)",
            canPickMany: true  // Multiple file selection is allowed
        });

        if (!fileSelections || fileSelections.length === 0) {
            return undefined;
        }

        return fileSelections.map(item => item.id!);
    } catch (error: any) {
        vscode.window.showErrorMessage(`Failed to process course files: ${error.message}`);
        return undefined;
    }
}

async function selectDeadline(currentDeadlineISO?: string): Promise<string | undefined> {
    const now = new Date(); // Represents current local time

    // Helper for padding numbers, local to this function
    const pad = (num: number) => num.toString().padStart(2, '0');

    // Helper to format a Date to naive local YYYY-MM-DDTHH:MM:SS, local to this function
    const toNaiveLocalISO = (date: Date): string => {
        return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
    };

    const quickPickItems: (vscode.QuickPickItem & { value?: () => string, isCustom?: boolean })[] = [
        {
            label: "$(calendar) Tomorrow at 9:00 AM",
            description: "Sets deadline to tomorrow morning",
            value: () => {
                const d = new Date(now);
                d.setDate(d.getDate() + 1);
                d.setHours(9, 0, 0, 0);
                return toNaiveLocalISO(d);
            }
        },
        {
            label: "$(clock) End of Today (23:59)",
            description: "Sets deadline to tonight",
            value: () => {
                const d = new Date(now);
                d.setHours(23, 59, 59, 999);
                return toNaiveLocalISO(d);
            }
        },
        {
            label: "$(milestone) In 3 Days",
            description: "Sets deadline three days from now",
            value: () => {
                const d = new Date(now);
                d.setDate(d.getDate() + 3);
                d.setHours(23, 59, 59, 999);
                return toNaiveLocalISO(d);
            }
        },
        {
            label: "$(arrow-right) In 1 Week",
            description: "Sets deadline one week from now",
            value: () => {
                const d = new Date(now);
                d.setDate(d.getDate() + 7);
                d.setHours(23, 59, 59, 999);
                return toNaiveLocalISO(d);
            }
        },
        {
            label: "$(pencil) Custom...",
            description: "Enter a specific date and time",
            isCustom: true
        }
    ];

    if (currentDeadlineISO) {
        const currentDateObj = new Date(currentDeadlineISO);
        quickPickItems.unshift({
            label: "$(debug-step-back) Keep Current Deadline",
            description: `Currently: ${currentDateObj.toLocaleString()}`,
            value: () => toNaiveLocalISO(currentDateObj)
        });
    }

    const selection = await vscode.window.showQuickPick(quickPickItems, {
        placeHolder: "Select or enter a deadline for the assignment"
    });

    if (!selection) {
        return undefined;
    }

    if (selection.isCustom) {
        let dateForDefaultInput: Date;
        if (currentDeadlineISO) {
            dateForDefaultInput = new Date(currentDeadlineISO);
        } else {
            dateForDefaultInput = new Date(now);
            dateForDefaultInput.setDate(dateForDefaultInput.getDate() + 1);
            dateForDefaultInput.setHours(17, 0, 0, 0);
        }

        const naiveDefaultValueForInputBox = `${dateForDefaultInput.getFullYear()}-${pad(dateForDefaultInput.getMonth() + 1)}-${pad(dateForDefaultInput.getDate())} ${pad(dateForDefaultInput.getHours())}:${pad(dateForDefaultInput.getMinutes())}:${pad(dateForDefaultInput.getSeconds())}`;

        const deadlineStr = await vscode.window.showInputBox({
            prompt: "Custom Deadline (YYYY-MM-DD HH:MM:SS local time)",
            placeHolder: "e.g., 2025-12-31 23:59:59",
            value: naiveDefaultValueForInputBox,
            validateInput: text => {
                if (!text) { return "Deadline cannot be empty."; }
                if (isNaN(new Date(text).getTime())) { return "Invalid date format. Use YYYY-MM-DD HH:MM:SS."; }
                return null;
            }
        });
        return deadlineStr ? toNaiveLocalISO(new Date(deadlineStr)) : undefined;
    } else if (selection.value) {
        return selection.value();
    }

    return undefined;
}