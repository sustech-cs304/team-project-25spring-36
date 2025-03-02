import axios from 'axios';
import { BACKEND_URL, USER_URL } from '../resources/configs/config';
import { parseResponse } from '../utils/responseParser';

export interface IUserInfo {
  username: string;
  role: string;
  // add other fields as necessary
}

export const authenticationService = {
  async login(username: string, password: string): Promise<string> {
    try {
      const response = await axios.post(`${BACKEND_URL}${USER_URL}/login`, { username, password });
      const token = parseResponse(response);
      console.log(`Logged in token: ${token}`);
      return token;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  },

  async register(username: string, password: string, role: string): Promise<string> {
    try {
      const response = await axios.post(`${BACKEND_URL}${USER_URL}/register`, { username, password, role });
      const token = parseResponse(response);
      console.log(`Registered ${username} with role ${role} token: ${token}`);
      return token;
    } catch (error) {
      console.error('Registration error:', error);
      throw error;
    }
  },

  async update(username: string, password: string, role: string, token: string): Promise<string> {
    try {
      // Include the JWT token in the header (note: remove any space in header names)
      const response = await axios.put(
        `${BACKEND_URL}${USER_URL}`,
        { username, password, role },
        { headers: { "Access-Token": token } }
      );
      const newToken = parseResponse(response);
      console.log(`Updated ${username} token: ${newToken}`);
      return newToken;
    } catch (error) {
      console.error('Update error:', error);
      throw error;
    }
  },

  async getUserInfo(token: string): Promise<IUserInfo> {
    try {
      // Make a GET request to fetch user info. Adjust endpoint below if needed.
      const response = await axios.get(`${BACKEND_URL}${USER_URL}`, {
        headers: { "Access-Token": token }
      });
      const userInfo: IUserInfo = parseResponse(response);
      console.log(`Fetched user info: ${JSON.stringify(userInfo)}`);
      return userInfo;
    } catch (error) {
      console.error('Fetch user info error:', error);
      throw error;
    }
  }
};