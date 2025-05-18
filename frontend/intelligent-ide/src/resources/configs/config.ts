export const API_CONFIG = {
  BASE_URL: 'http://localhost:8081/api',
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
export const OPENAI_API_KEY = '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';