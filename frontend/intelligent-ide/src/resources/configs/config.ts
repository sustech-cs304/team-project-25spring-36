export const API_CONFIG = {
  BASE_URL: 'http://localhost:8080',
  // User endpoints
  USER: {
    LOGIN: '/api/user/login',
    REGISTER: '/api/user/register',
    REGISTER_CODE: '/api/user/register/code',
    INFO: '/api/user',
  },

  // Course endpoints
  COURSE: {
    BASE: '/api/course',
    DIRECTORY: '/api/course/directory',
    DIRECTORY_ENTRY: '/api/course/directory/entry',
    DIRECTORY_ENTRY_DOWNLOAD: '/api/course/directory/entry/download',
    DIRECTORY_ENTRY_MOVE: '/api/course/directory/entry/move',
    STUDENT: '/api/course/student',
    STUDENT_JOIN: '/api/course/student/join',
    COLLABORATIVE: '/api/course/collaborative',
    COLLABORATIVE_HISTORY: '/api/course/collaborative/history',
    COLLABORATIVE_DOWNLOAD: '/api/course/collaborative/download'
  }
};
export const OPENAI_API_MODEL = 'gpt-4.1';
export const OPENAI_API_KEY = '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';