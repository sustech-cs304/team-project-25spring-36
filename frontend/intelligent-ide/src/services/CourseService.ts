import axios from 'axios';
import { API_CONFIG } from '../resources/configs/config';
import { parseResponse } from '../utils/parseResponse';
import { ICourse, ICourseDirectory, ICourseDirectoryEntry } from '../models/CourseModels';

export const courseService = {
  /**
   * Get list of courses (based on user role)
   */
  async getCourses(token: string, role: string): Promise<ICourse[]> {
    try {
      const response = await axios.get(`${API_CONFIG.BASE_URL}${API_CONFIG.COURSE.BASE}`, {
        params: { role },
        headers: {
          'Access-Token': token
        }
      });
      return parseResponse<ICourse[]>(response);
    } catch (error: any) {
      console.error('Error getting courses:', error);
      throw new Error(error.response?.data?.message || error.message);
    }
  },
  /**
 * Get directories for a course
 */
  async getDirectories(token: string, courseId: number): Promise<ICourseDirectory[]> {
    try {
      const response = await axios.get(`${API_CONFIG.BASE_URL}${API_CONFIG.COURSE.DIRECTORY}`, {
        params: { course_id: courseId },
        headers: {
          'Access-Token': token
        }
      });
      return parseResponse<ICourseDirectory[]>(response);
    } catch (error: any) {
      console.error('Error getting directories:', error);
      throw new Error(error.response?.data?.message || error.message);
    }
  },

  /**
   * Get entries for a directory
   */
  async getEntries(
    token: string,
    directoryId: number,
    path: string = "/", // Default to root path
    fuzzy: boolean = true
  ): Promise<ICourseDirectoryEntry[]> {
    try {
      const response = await axios.get(`${API_CONFIG.BASE_URL}${API_CONFIG.COURSE.DIRECTORY_ENTRY}`, {
        params: {
          course_directory_id: directoryId,
          path: path,
          fuzzy: fuzzy
        },
        headers: {
          'Access-Token': token
        }
      });
      return parseResponse<ICourseDirectoryEntry[]>(response);
    } catch (error: any) {
      console.error('Error getting entries:', error);
      throw new Error(error.response?.data?.message || error.message);
    }
  },

  /**
   * Create a new course (teacher only)
   */
  async createCourse(token: string, name: string, description: string): Promise<number> {
    try {
      const response = await axios.post(
        `${API_CONFIG.BASE_URL}${API_CONFIG.COURSE.BASE}`,
        { name, description },
        {
          headers: {
            'Access-Token': token
          }
        }
      );
      return parseResponse<number>(response);
    } catch (error: any) {
      console.error('Error creating course:', error);
      throw new Error(error.response?.data?.message || error.message);
    }
  },

  /**
   * Delete a course (teacher only)
   */
  async deleteCourse(token: string, courseId: number): Promise<string> {
    try {
      const response = await axios.delete(`${API_CONFIG.BASE_URL}${API_CONFIG.COURSE.BASE}`, {
        params: { course_id: courseId },
        headers: {
          'Access-Token': token
        }
      });
      return parseResponse<string>(response); // Should return "success" status
    } catch (error: any) {
      console.error('Error deleting course:', error);
      throw new Error(error.response?.data?.message || error.message);
    }
  }
};