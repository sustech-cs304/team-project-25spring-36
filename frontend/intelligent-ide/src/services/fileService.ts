import axios from 'axios';
import { BACKEND_URL } from '../resources/configs/config';
import { authenticationService } from './userService';
import * as vscode from 'vscode';

export interface FileNode {
  name: string;
  path: string;
  type: 'file' | 'directory';
  children?: FileNode[];
}

export const fileService = {
  async getFileStructure(context: vscode.ExtensionContext): Promise<FileNode[]> {
    try {
      const token = await context.secrets.get('authToken');
      if (!token) {
        throw new Error('请先登录');
      }

      const userInfo = await authenticationService.getUserInfo(token);

      const response = await axios.get(`${BACKEND_URL}/api/files/structure`, {
        params: { role: userInfo.role },
        headers: { "Access-Token": token }
      });

      return response.data.items;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 401) {
        await context.secrets.delete('authToken');
        vscode.window.showErrorMessage('登录已过期');
      }
      throw error;
    }
  }
};