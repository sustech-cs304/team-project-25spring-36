import axios from 'axios';
import { parseResponse } from '../utils/parseResponse';
import {BACKEND_URL, USER_URL} from '../resources/configs/config';
import * as vscode from 'vscode';

export interface IUserInfo {
  id: number;
  username: string;
  email: string;
}

export const authenticationService = {
  async login(email: string, password: string): Promise<string> {
    try {
      const response = await axios.post(`${BACKEND_URL}${USER_URL}/login`, { email, password });
      const data = parseResponse<{ token: string }>(response);
      const token = data.token;
      if (!token) {
        throw new Error('Login failed: No token received');
      }
      console.log(`Logged in token: ${token}`);
      return token;
    } catch (error: any) {
      console.error('Login error:', error);
      if (error.response?.data?.message) {
        throw new Error(`Login failed: ${error.response.data.message}`);
      }
      throw error;
    }
  },

  async register(username: string, email: string, password: string, code: string): Promise<string> {
    try {
      const response = await axios.post(`${BACKEND_URL}${USER_URL}/register`, { username, password, email, code });
      const data = parseResponse<{ token: string }>(response);
      const token = data.token;
      if (!token) {
        throw new Error('Registration failed: No token received');
      }
      console.log(`Registered ${username} with email ${email} token: ${token}`);
      return token;
    } catch (error: any) {
      console.error('Registration error:', error);
      if (error.response?.data?.message) {
        throw new Error(`Registration failed: ${error.response.data.message}`);
      }
      throw error;
    }
  },

  async getUserInfo(token: string, context: vscode.ExtensionContext): Promise<IUserInfo> {
    try {
      const response = await axios.get(`${BACKEND_URL}${USER_URL}`, {
        headers: {
          'Access-Token': token,
        },
      });
      const userInfo = parseResponse<IUserInfo>(response);

      // Store login info in global state
      const newLoginInfo = {
        token: token,
        username: userInfo.username,
        email: userInfo.email,
        role: "student",
      };
      await context.globalState.update('loginInfo', newLoginInfo);

      return userInfo;
    } catch (error: any) {
      console.error('Get user info error:', error);
      if (error.response?.data?.message) {
        throw new Error(`Get user info failed: ${error.response.data.message}`);
      }
      throw error;
    }
  },

  async update(username: string, password: string, token: string): Promise<string> {
    try {
      const response = await axios.put(
        `${BACKEND_URL}${USER_URL}`,
        { username, password },
        {
          headers: {
           'Access-Token': token,
          },
        }
      );
      const data = parseResponse<{ token: string }>(response);
      const newToken = data.token;
      if (!newToken) {
        throw new Error('Update failed: No token received');
      }
      console.log(`Updated username/password, new token: ${newToken}`);
      return newToken;
    } catch (error: any) {
      console.error('Update error:', error);
      if (error.response?.data?.message) {
        throw new Error(`Update failed: ${error.response.data.message}`);
      }
      throw error;
    }
  },

  async getVerificationCode(email: string): Promise<string> {
    try {
      const response = await axios.get(`${BACKEND_URL}${USER_URL}/register/code`, {
        params: { email },
      });
      const data = parseResponse<string>(response);
      console.log(`Verification code sent to ${email}`);
      return data;
    } catch (error: any) {
      console.error('Get verification code error:', error);
      if (error.response?.data?.message) {
        throw new Error(`Failed to send verification code: ${error.response.data.message}`);
      }
      throw error;
    }
  },
};