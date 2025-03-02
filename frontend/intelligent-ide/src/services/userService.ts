import axios from 'axios';
import { BACKEND_URL, USER_URL } from '../resources/configs/config';
import { parseResponse } from '../utils/responseParser';

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
      // Include the JWT token in the Authorization header
      const response = await axios.put(
        `${BACKEND_URL}${USER_URL}`,
        { username, password, role },
        { headers: { "Access-Token": `${token}` } }
      );
      const newToken = parseResponse(response);
      console.log(`Updated ${username} token: ${newToken}`);
      return newToken;
    } catch (error) {
      console.error('Update error:', error);
      throw error;
    }
  }
};