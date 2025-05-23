/**
 *作业布置创建请求模型
 */
export interface ICourseHomeworkAssignmentCreateRequest {
    course_id: number;
    title: string | null;
    description: string | null;
    deadline: string | null; // ISO date-time string
    course_directory_entry_ids: number[];
}

/**
 * 作业布置更新请求模型
 */
export interface ICourseHomeworkAssignmentUpdateRequest {
    assignment_id: number;
    title?: string | null;
    description?: string | null;
    deadline?: string | null; // ISO date-time string
    course_directory_entry_ids?: number[];
}

/**
 * 作业提交创建请求模型
 */
export interface ICourseHomeworkSubmissionCreateRequest {
    assignment_id: number;
    title: string | null;
    description: string | null;
    course_directory_entry_ids: number[];
}

/**
 * 作业提交评分请求模型
 */
export interface ICourseHomeworkSubmissionGradeRequest {
    submission_id: number;
    grade: number;
    feedback: string | null;
}

export interface ICourseHomeworkAssignment {
    id: number;
    course_id: number;
    title: string | null;
    description: string | null;
    deadline: string | null;
    course_directory_entry_ids: number[];
    created_at: string;
    updated_at: string;
}

export interface ICourseHomeworkSubmission {
    id: number;
    assignment_id: number;
    student_id: number; // Assuming this is part of the submission details
    title: string | null;
    description: string | null;
    course_directory_entry_ids: number[];
    grade?: number | null;
    feedback?: string | null;
    submission_date: string; // ISO date-time string
    created_at: string;
    updated_at: string;
}
export interface ICourseHomeworkAssignmentStatus {
    id: number; // This is assignment.id
    course_id: number;
    title: string | null;
    description: string | null;
    deadline: string | null; // ISO date-time string
    course_directory_entry_ids: number[];
    created_at: string; // ISO date-time string
    updated_at: string; // ISO date-time string
    is_overdue: boolean;
    submission_count: number;
    is_completed: boolean;
    latest_submission_id: ICourseHomeworkSubmission | null;
}