const BASE_PORT = 8080;

export const API_CONFIG = {
  BASE_PORT: BASE_PORT,
  BASE_URL: 'http://localhost:' + BASE_PORT + '/api',
  BASE_WS_URL: 'ws://localhost:'+ BASE_PORT +'/ws',
  // User endpoints
  USER: {
    LOGIN: '/user/login',
    REGISTER: '/user/register',
    REGISTER_CODE: '/user/register/code',
    INFO: '/user',
  },

  // Course endpoints
  COURSE: {
    BASE: '/course',
    DIRECTORY: '/course/directory',
    DIRECTORY_ENTRY: '/course/directory/entry',
    DIRECTORY_ENTRY_DOWNLOAD: '/course/directory/entry/download',
    DIRECTORY_ENTRY_MOVE: '/course/directory/entry/move',
    STUDENT: '/course/student',
    STUDENT_JOIN: '/course/student/join',
    COLLABORATIVE: '/course/collaborative',
    COLLABORATIVE_JOIN: '/course/collaborative/join',
    COLLABORATIVE_HISTORY: '/course/collaborative/history',
    COLLABORATIVE_DOWNLOAD: '/course/collaborative/download'
  },
  // Homework endpoints
  HOMEWORK: {
    ASSIGNMENT: '/course/homework/assignment',
    ASSIGNMENT_STATUS: '/course/homework/assignment/status',
    SUBMISSION: '/course/homework/submission',
    SUBMISSION_GRADE: '/course/homework/submission/grade',
  },
};
export const OPENAI_API_MODEL = 'gpt-4.1';
