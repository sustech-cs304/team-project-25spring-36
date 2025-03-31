import axios, { AxiosError, AxiosResponse } from 'axios';
import { BACKEND_URL, USER_URL } from '../resources/configs/config';
import { parseResponse } from '../utils/parseResponse';

export interface IUserInfo {
  username: string;
  email: string;
  id?: string;
  uid?: string;
  created_at?: string;
  updated_at?: string;
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

  async getVerificationCode(email: string): Promise<void> {
    try {
      const response =  await axios.get(`${BACKEND_URL}${USER_URL}/register/code`, { params: { email } });
      parseResponse(response);
      console.log(`Verification code sent to ${email}`);
    } catch (error: any) {
      console.error('Verification code error:', error);
      if (error.response?.data?.message) {
        throw new Error(`Verification code failed: ${error.response.data.message}`);
      }
      throw error;
    }
  },

  async update(username: string, password: string, token: string): Promise<string> {
    try {
      const response = await axios.put(
        `${BACKEND_URL}${USER_URL}`,
        { username, password },
        { headers: { "Access-Token": token } }
      );
      const data = parseResponse<{ token: string }>(response);
      const newToken = data.token;
      if (!newToken) {
        throw new Error('Update failed: No token received');
      }
      console.log(`Updated ${username} token: ${newToken}`);
      return newToken;
    } catch (error: any) {
      console.error('Update error:', error);
      if (error.response?.data?.message) {
        throw new Error(`Update failed: ${error.response.data.message}`);
      }
      throw error;
    }
  },

  async getUserInfo(token: string): Promise<IUserInfo> {
    try {
      const response = await axios.get(`${BACKEND_URL}${USER_URL}`, {
        headers: { "Access-Token": token }
      });
      const userInfo = parseResponse<IUserInfo>(response);
      if (!userInfo.username || !userInfo.email) {
        throw new Error('Fetch user info failed: No user info received');
      }
      console.log(`Fetched user info: ${JSON.stringify(userInfo)}`);
      return userInfo;
    } catch (error: any) {
      console.error('Fetch user info error:', error);
      if (error.response?.data?.message) {
        throw new Error(`Fetch user info failed: ${error.response.data.message}`);
      }
      throw error;
    }
  }
};