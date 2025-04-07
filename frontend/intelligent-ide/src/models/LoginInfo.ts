export interface LoginInfo {
  username: string;
  email: string;
  token: string;
  role: 'student' | 'teacher' | 'admin';
}