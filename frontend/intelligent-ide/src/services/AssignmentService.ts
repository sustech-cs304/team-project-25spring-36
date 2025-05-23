import axios from 'axios';
import { API_CONFIG } from '../resources/configs/config';
import { parseResponse } from '../utils/parseResponse';
import {
    ICourseHomeworkAssignmentCreateRequest,
    ICourseHomeworkAssignmentUpdateRequest,
    ICourseHomeworkSubmissionCreateRequest,
    ICourseHomeworkSubmissionGradeRequest,
    ICourseHomeworkAssignment,
    ICourseHomeworkSubmission,
    ICourseHomeworkAssignmentStatus
} from '../models/AssignmentModels';

export const assignmentService = {
    /**
     * Create a new homework assignment (teacher only).
     */
    async createAssignment(
        token: string,
        assignmentData: ICourseHomeworkAssignmentCreateRequest
    ): Promise<ICourseHomeworkAssignment> { // Assuming the response is the created assignment object
        try {
            const response = await axios.post(
                `${API_CONFIG.BASE_URL}${API_CONFIG.HOMEWORK.ASSIGNMENT}`,
                assignmentData,
                {
                    headers: { 'Access-Token': token }
                }
            );
            return parseResponse<ICourseHomeworkAssignment>(response);
        } catch (error: any) {
            console.error('Error creating assignment:', error);
            throw new Error(error.response?.data?.detail || error.response?.data?.message || error.message);
        }
    },

    /**
     * Get all assignments for a course.
     */
    async getAssignments(
        token: string,
        courseId: number
    ): Promise<ICourseHomeworkAssignment[]> {
        try {
            const response = await axios.get(
                `${API_CONFIG.BASE_URL}${API_CONFIG.HOMEWORK.ASSIGNMENT}`,
                {
                    params: { course_id: courseId },
                    headers: { 'Access-Token': token }
                }
            );
            return parseResponse<ICourseHomeworkAssignment[]>(response);
        } catch (error: any) {
            console.error('Error getting assignments:', error);
            throw new Error(error.response?.data?.detail || error.response?.data?.message || error.message);
        }
    },

    /**
     * Delete an assignment (teacher only).
     */
    async deleteAssignment(
        token: string,
        assignmentId: number
    ): Promise<any> { // API doc shows empty JSON {} for success
        try {
            const response = await axios.delete(
                `${API_CONFIG.BASE_URL}${API_CONFIG.HOMEWORK.ASSIGNMENT}`,
                {
                    params: { assignment_id: assignmentId },
                    headers: { 'Access-Token': token }
                }
            );
            return parseResponse<any>(response);
        } catch (error: any) {
            console.error('Error deleting assignment:', error);
            throw new Error(error.response?.data?.detail || error.response?.data?.message || error.message);
        }
    },

    /**
     * Update an assignment (teacher only).
     */
    async updateAssignment(
        token: string,
        assignmentData: ICourseHomeworkAssignmentUpdateRequest
    ): Promise<ICourseHomeworkAssignment> { // Assuming the response is the updated assignment
        try {
            const response = await axios.put(
                `${API_CONFIG.BASE_URL}${API_CONFIG.HOMEWORK.ASSIGNMENT}`,
                assignmentData,
                {
                    headers: { 'Access-Token': token }
                }
            );
            return parseResponse<ICourseHomeworkAssignment>(response);
        } catch (error: any) {
            console.error('Error updating assignment:', error);
            throw new Error(error.response?.data?.detail || error.response?.data?.message || error.message);
        }
    },

    /**
     * Create a homework submission (student only).
     */
    async createSubmission(
        token: string,
        submissionData: ICourseHomeworkSubmissionCreateRequest
    ): Promise<ICourseHomeworkSubmission> { // Assuming response is the created submission
        try {
            const response = await axios.post(
                `${API_CONFIG.BASE_URL}${API_CONFIG.HOMEWORK.SUBMISSION}`,
                submissionData,
                {
                    headers: { 'Access-Token': token }
                }
            );
            return parseResponse<ICourseHomeworkSubmission>(response);
        } catch (error: any) {
            console.error('Error creating submission:', error);
            throw new Error(error.response?.data?.detail || error.response?.data?.message || error.message);
        }
    },

    /**
     * Get homework submissions.
     */
    async getSubmissions(
        token: string,
        params: {
            submission_id?: number;
            assignment_id?: number;
            student_id?: number;
        }
    ): Promise<ICourseHomeworkSubmission[]> {
        try {
            const response = await axios.get(
                `${API_CONFIG.BASE_URL}${API_CONFIG.HOMEWORK.SUBMISSION}`,
                {
                    params,
                    headers: { 'Access-Token': token }
                }
            );
            return parseResponse<ICourseHomeworkSubmission[]>(response);
        } catch (error: any) {
            console.error('Error getting submissions:', error);
            throw new Error(error.response?.data?.detail || error.response?.data?.message || error.message);
        }
    },

    /**
     * Delete a submission (teacher only).
     */
    async deleteSubmission(
        token: string,
        submissionId: number
    ): Promise<any> { // API doc shows empty JSON {} for success
        try {
            const response = await axios.delete(
                `${API_CONFIG.BASE_URL}${API_CONFIG.HOMEWORK.SUBMISSION}`,
                {
                    params: { submission_id: submissionId },
                    headers: { 'Access-Token': token }
                }
            );
            return parseResponse<any>(response);
        } catch (error: any) {
            console.error('Error deleting submission:', error);
            throw new Error(error.response?.data?.detail || error.response?.data?.message || error.message);
        }
    },

    /**
     * Grade a submission (teacher only).
     */
    async gradeSubmission(
        token: string,
        gradeData: ICourseHomeworkSubmissionGradeRequest
    ): Promise<ICourseHomeworkSubmission> { // API doc shows empty JSON {} for success, might return updated submission
        try {
            const response = await axios.put(
                `${API_CONFIG.BASE_URL}${API_CONFIG.HOMEWORK.SUBMISSION_GRADE}`,
                gradeData,
                {
                    headers: { 'Access-Token': token }
                }
            );
            return parseResponse<ICourseHomeworkSubmission>(response);
        } catch (error: any) {
            console.error('Error grading submission:', error);
            throw new Error(error.response?.data?.detail || error.response?.data?.message || error.message);
        }
    },

    /**
     * Get assignment status for a student in a course.
     */
    async getAssignmentStatuses(
        token: string,
        courseId: number
    ): Promise<ICourseHomeworkAssignmentStatus[]> {
        try {
            const response = await axios.get(
                `${API_CONFIG.BASE_URL}${API_CONFIG.HOMEWORK.ASSIGNMENT_STATUS}`,
                {
                    params: { course_id: courseId },
                    headers: { 'Access-Token': token }
                }
            );
            return parseResponse<ICourseHomeworkAssignmentStatus[]>(response);
        } catch (error: any) {
            console.error('Error getting assignment statuses:', error);
            throw new Error(error.response?.data?.detail || error.response?.data?.message || error.message);
        }
    }
};