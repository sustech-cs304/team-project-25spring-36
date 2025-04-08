import axios from 'axios';
import * as vscode from 'vscode';
import * as path from 'path';
import { API_CONFIG } from '../resources/configs/config';
import { parseResponse } from '../utils/parseResponse';
import { ICourse, ICourseDirectory, ICourseDirectoryEntry, DirectoryPermissionType } from '../models/CourseModels';

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
 * Get directories for a courses
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
   * Create a new course (teacher only
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
  },


  /**
   * Delete a directory
   */
  async deleteDirectory(token: string, directoryId: number): Promise<string> {
    try {
      const response = await axios.delete(`${API_CONFIG.BASE_URL}${API_CONFIG.COURSE.DIRECTORY}`, {
        params: { course_directory_id: directoryId },
        headers: {
          'Access-Token': token
        }
      });
      return parseResponse<string>(response);
    } catch (error: any) {
      console.error('Error deleting directory:', error);
      throw new Error(error.response?.data?.message || error.message);
    }
  },

  /**
   * Create a new directory in a course
   */
  async postDirectory(
    token: string,
    courseId: number,
    name: string,
    permission?: Record<string, DirectoryPermissionType[]>
  ): Promise<number> {
    try {
      // Create request body with required fields
      const requestBody: any = {
        course_id: courseId,
        name
      };

      // Only include permission field if provided and not empty
      if (permission && Object.keys(permission).length > 0) {
        requestBody.permission = permission;
      }

      const response = await axios.post(
        `${API_CONFIG.BASE_URL}${API_CONFIG.COURSE.DIRECTORY}`,
        requestBody,
        {
          headers: {
            'Access-Token': token
          }
        }
      );

      // Extract course_directory_id from the response data
      const result = parseResponse<{ course_directory_id: number }>(response);
      return result.course_directory_id;
    } catch (error: any) {
      console.error('Error creating directory:', error);
      throw new Error(error.response?.data?.message || error.message);
    }
  },

  /**
   * Delete a directory entry (file or folder)
   */
  async deleteEntry(token: string, entryId: number): Promise<string> {
    try {
      const response = await axios.delete(
        `${API_CONFIG.BASE_URL}${API_CONFIG.COURSE.DIRECTORY_ENTRY}`,
        {
          params: { course_directory_entry_id: entryId },
          headers: {
            'Access-Token': token
          }
        }
      );
      return parseResponse<string>(response);
    } catch (error: any) {
      console.error('Error deleting entry:', error);
      throw new Error(error.response?.data?.message || error.message);
    }
  },

  /**
   * Upload a file to create a new entry
   * @param token Authentication token
   * @param directoryId Directory ID to upload to
   * @param entryPath Path within the directory
   * @param fileUri VS Code URI to the fil
   * @returns ID of the created entry
   */
  async uploadFile(
    token: string,
    directoryId: number,
    entryPath: string,
    fileUri: vscode.Uri
  ): Promise<number> {
    try {
      // Read file content as binary data
      const fileContent = await vscode.workspace.fs.readFile(fileUri);

      // Get filename from path
      const fileName = path.basename(fileUri.fsPath);

      // Create FormData (requires npm install form-data)
      const FormData = require('form-data');
      const form = new FormData();

      // Add directory ID and path to form
      form.append('course_directory_id', directoryId.toString());
      form.append('path', entryPath);

      // Convert Uint8Array to Buffer and add as file
      form.append('file', Buffer.from(fileContent), {
        filename: fileName,
        contentType: 'application/octet-stream'
      });

      const response = await axios.post(
        `${API_CONFIG.BASE_URL}${API_CONFIG.COURSE.DIRECTORY_ENTRY}`,
        form,
        {
          headers: {
            'Access-Token': token,
            ...form.getHeaders()
          },
          // For large files
          maxBodyLength: Infinity,
          maxContentLength: Infinity
        }
      );

      // Extract entry ID from response
      const result = parseResponse<{ course_directory_entry_id: number }>(response);
      return result.course_directory_entry_id;
    } catch (error: any) {
      console.error('Error uploading file:', error);
      throw new Error(error.response?.data?.message || error.message);
    }
  },

  /**
   * Download a file entry
   * @param token Authentication token
   * @param entryId ID of the entry to download
   * @returns Binary content of the file
   */
  async downloadEntry(token: string, entryId: number): Promise<Uint8Array> {
    try {
      const response = await axios.get(
        `${API_CONFIG.BASE_URL}${API_CONFIG.COURSE.DIRECTORY_ENTRY}/download`,
        {
          params: { course_directory_entry_id: entryId },
          headers: {
            'Access-Token': token
          },
          responseType: 'arraybuffer' // Important for binary data
        }
      );

      // For binary data, we can't use parseResponse helper
      if (response.status !== 200) {
        throw new Error(`Failed to download file: ${response.statusText}`);
      }

      // Return the binary data as Uint8Array
      return new Uint8Array(response.data);
    } catch (error: any) {
      console.error('Error downloading entry:', error);
      throw new Error(error.response?.data?.message || error.message);
    }
  },

  /**
   * Move an entry to a different path
   * @param token Authentication token
   * @param entryId ID of the entry to move
   * @param destinationPath Destination path for the entry
   * @returns Success message
   */
  async moveEntry(
    token: string,
    entryId: number,
    destinationPath: string
  ): Promise<string> {
    try {
      const response = await axios.put(
        `${API_CONFIG.BASE_URL}${API_CONFIG.COURSE.DIRECTORY_ENTRY}/move`,
        {
          course_directory_entry_id: entryId,
          dst_path: destinationPath
        },
        {
          headers: {
            'Access-Token': token
          }
        }
      );

      return parseResponse<string>(response);
    } catch (error: any) {
      console.error('Error moving entry:', error);
      throw new Error(error.response?.data?.message || error.message);
    }
  },
};