export interface ICourse {
    id: number;
    name: string;
    description: string;
    teacher_id: number;
    teacher_name: string;
    created_at: string;
}

export interface ICourseDirectory {
    id: number;
    course_id: number;
    name: string;
    permission: Record<string, string[]> | null;
    created_at: string;
}

export interface ICourseDirectoryEntry {
    id: number;
    course_directory_id: number;
    path: string;
    type: string;
    created_at: string;
    storage_name: string
}

export interface ICourseStudent {
    id: number;
    course_id: number;
    user_id: number;
    user_name: string;
    created_at: string;
}

export interface ICollaborativeEntry {
    id: number;
    course_id: number;
    file_name: string;
    created_at: string;
    created_by: number;
    created_by_name: string;
}

export interface CourseListCache {
    teacher: ICourse[];
    student: ICourse[];
    lastUpdated: string;
}
