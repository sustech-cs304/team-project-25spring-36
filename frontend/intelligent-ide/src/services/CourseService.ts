import axios from 'axios';
import * as vscode from 'vscode';
import * as path from 'path';
import WebSocket from 'ws';
import * as fs from 'fs';
import { API_CONFIG } from '../resources/configs/config.js';
const Y = require('yjs');
import { parseResponse } from '../utils/parseResponse.js';
import { ICourse, ICourseDirectory, ICourseDirectoryEntry, DirectoryPermissionType, ICourseStudent, ICollaborativeEntry } from '../models/CourseModels.js';

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
      // Create request body with required fields and default empty permissio
      const requestBody: any = {
        course_id: courseId,
        name,
        permission: permission || {} // Always include permission field, default to empty object
      };

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


  /**
   * 
   * @param token Authentication toke
   * @param courseId 
   * @returns 
   */
  async joinCourse(token: string, courseId: number): Promise<number> {
    try {
      const response = await axios.post(
        `${API_CONFIG.BASE_URL}${API_CONFIG.COURSE.STUDENT_JOIN}`,
        { course_id: courseId },
        {
          headers: { 'Access-Token': token }
        }
      );

      const result = parseResponse<{ course_student_id: number }>(response);
      return result.course_student_id;
    } catch (err: any) {
      console.error('Error joining course:', err);
      throw new Error(err.response?.data?.message || err.message);

    }
  },
  async getStudents(token: string, courseId: number): Promise<ICourseStudent[]> {
    try {
      const response = await axios.get(
        `${API_CONFIG.BASE_URL}${API_CONFIG.COURSE.STUDENT}`, {
        params: { course_id: courseId },
        headers: {
          'Access-Token': token
        }
      });

      // The students array is directly in the data field, not in a nested 'students' property
      return parseResponse<ICourseStudent[]>(response);
    } catch (err: any) {
      console.error('Error getting students:', err);
      throw new Error(err.response?.data?.message || err.message);
    }
  },

  async deleteStudent(token: string, courseId: number, course_student_id: number): Promise<string> {
    try {
      const response = await axios.delete(
        `${API_CONFIG.BASE_URL}${API_CONFIG.COURSE.STUDENT}`, {
        params: { course_id: courseId, course_student_id: course_student_id },
        headers: {
          'Access-Token': token
        }
      });
      const result = parseResponse<{ msg: string }>(response);
      return result.msg;
    } catch (err: any) {
      console.error('Error deleting student:', err);
      throw new Error(err.response?.data?.message || err.message);
    }
  },
  async getCollaborativeDirectories(token: string, courseId: number): Promise<ICollaborativeEntry[]> {
    try {
      const response = await axios.get(`${API_CONFIG.BASE_URL}${API_CONFIG.COURSE.COLLABORATIVE}`, {
        params: { course_id: courseId },
        headers: {
          'Access-Token': token
        }
      });
      return parseResponse<ICollaborativeEntry[]>(response);
    } catch (error: any) {
      console.error('Error getting directories:', error);
      throw new Error(error.response?.data?.message || error.message);
    }
  },
  /**
 * Delete a directory entry (file or folder)
 */
  async deleteCollaborativeEntry(token: string, courseID: number, entryId: number): Promise<string> {
    try {
      const response = await axios.delete(
        `${API_CONFIG.BASE_URL}${API_CONFIG.COURSE.COLLABORATIVE}`,
        {
          params: { course_id: courseID, course_collaborative_directory_entry_id: entryId },
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



  async CollaborativeHistory(token: string, courseID: number, entryId: number): Promise<string> {
    try {
      const response = await axios.get(
        `${API_CONFIG.BASE_URL}${API_CONFIG.COURSE.COLLABORATIVE_HISTORY}`,
        {
          params: { course_id: courseID, course_collaborative_directory_entry_id: entryId },
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
  async uploadCollaborativeFile(
    token: string,
    directoryId: number,
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
      form.append('course_id', directoryId.toString());
      //form.append('path', entryPath);

      // Convert Uint8Array to Buffer and add as file
      form.append('file', Buffer.from(fileContent), {
        filename: fileName
      });

      const response = await axios.post(
        `${API_CONFIG.BASE_URL}${API_CONFIG.COURSE.COLLABORATIVE}`,
        form,
        {
          params: {
            course_id: directoryId   // 添加 Query 参数
          },
          headers: {
            'Access-Token': token,
            ...form.getHeaders()
          },
          // For large files
          maxBodyLength: Infinity,
          maxContentLength: Infinity
        }
      );
      //console.log('Full response from server:', response);
      // Extract entry ID from response
      const result = parseResponse<{ course_collaborative_directory_entry_id: number }>(response);
      return result.course_collaborative_directory_entry_id;

    } catch (error: any) {
      console.error('Error uploading file:', error);

      throw new Error(error.response?.data?.message || error.message);
    }
  },
  async downloadCollaborativeEntry(token: string, courseID: number, entryId: number): Promise<Uint8Array> {
    try {
      const response = await axios.get(
        `${API_CONFIG.BASE_URL}${API_CONFIG.COURSE.COLLABORATIVE_DOWNLOAD}`,
        {
          params: { course_id: courseID, course_collaborative_directory_entry_id: entryId },
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
      console.log(courseID, entryId);
      // Return the binary data as Uint8Array
      return new Uint8Array(response.data);
    } catch (error: any) {
      console.error('Error downloading entry:', error);
      throw new Error(error.response?.data?.message || error.message);
    }
  },
  async joinCollaborativeSession(
    token: string,
    courseId: number,
    entryId: number
  ): Promise<void> {
    try {
      // 构建 WebSocket URL
      const wsUrl = `ws://localhost:8080/ws/course/collaborative/join?course_id=${courseId}&course_collaborative_directory_entry_id=${entryId}`;
      console.log(`Connecting to WebSocket URL: ${wsUrl}`);

      // 创建 WebSocket 连接
      const websocket = new WebSocket(wsUrl, {
        headers: {
          'Access-Token': token,
        },
      });

      // 创建 Y.Doc 实例
      const ydoc = new Y.Doc();
      const ytext = ydoc.getText('text');

      // 打开协作编辑器
      const panel = vscode.window.createWebviewPanel(
        'collaborativeEditor',
        `Collaborative Editor - ${courseId}`,
        vscode.ViewColumn.One,
        {
          enableScripts: true,
          retainContextWhenHidden: true,
        }
      );

      // 设置 WebView 内容为 HTML 文件内容
      panel.webview.html = this.getCollaborativeEditorHtml();

      // WebSocket 事件处理
      websocket.onopen = () => {
        console.log('WebSocket connection opened.');

        // 发送同步请求
        const stateVector = Y.encodeStateVector(ydoc);
        websocket.send(
          JSON.stringify({
            type: 'sync',
            state_vector: Buffer.from(stateVector).toString('hex'),
          })
        );
        ydoc.on('update', (update: any) => {
          console.log('content update:', update);
          // 当 Y.Doc 更新时，发送增量更新到服务器
          websocket.send(
            JSON.stringify({
              type: 'update',
              update: Buffer.from(update).toString('hex'),  // 增量更新转换为十六进制字符串
            })
          );
        });
      };

      websocket.onmessage = (event) => {
        const message = JSON.parse(event.data.toString());
        if (message.type === 'update') {
          const updateBytes = Uint8Array.from(Buffer.from(message.update, 'hex'));
          Y.applyUpdate(ydoc, updateBytes);

          // 将更新后的文档内容发送到 HTML 页面
          panel.webview.postMessage({
            command: 'updateContent',
            ytext: ytext,
            content: ytext.toDelta(), // 转换为 Quill Delta 格式
            userId: message.user_id,
            time: message.time,
          });
        }
      };

      websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        panel.webview.postMessage({ command: 'error', error: error.message });
      };

      websocket.onclose = () => {
        console.warn('WebSocket connection closed.');
        panel.webview.postMessage({ command: 'disconnected' });
      };

      // 监听 HTML 页面发送的消息
      panel.webview.onDidReceiveMessage((message) => {
        if (message.command === 'editContent') {
          // 更新 Y.Doc 文档
          const delta = message.content;
          ydoc.getText('text').applyDelta(delta.ops); // 应用 Quill 的 Delta 格式内容
          console.log('Received content update:', ytext.toString());
          // // 发送增量更新到服务器
          // const update = Y.encodeStateAsUpdate(ydoc);
          // websocket.send(
          //     JSON.stringify({
          //         type: 'update',@
          //         update: Buffer.from(update).toString('hex'),
          //     })
          // );


        }
      });

      // 关闭 WebSocket 连接时清理资源
      panel.onDidDispose(() => {
        websocket.close();
      });
    } catch (error: any) {
      console.error('Error joining collaborative session:', error);
      throw new Error(error.message || 'Failed to join collaborative session.');
    }
  },

  // openCollaborativeEditor(
  //     token: string,
  //     websocket: WebSocket,
  //     courseId: number,
  //     entryId: number
  // ): void {
  //     const panel = vscode.window.createWebviewPanel(
  //         'collaborativeEditor',
  //         'Collaborative Editor',
  //         vscode.ViewColumn.One,
  //         {
  //             enableScripts: true,
  //             retainContextWhenHidden: true,
  //         }
  //     );

  //     // 设置 WebView 内容为 HTML 文件内容
  //     panel.webview.html = this.getCollaborativeEditorHtml();

  //     // 监听 WebSocket 消息
  //     websocket.onmessage = (event) => {
  //         const message = JSON.parse(event.data.toString());
  //         if (message.type === 'update') {
  //             panel.webview.postMessage({
  //                 command: 'applyUpdate',
  //                 update: message.update,
  //                 userId: message.user_id,
  //                 time: message.time,
  //             });
  //         }
  //     };

  //     websocket.onopen = () => {
  //         console.log('WebSocket connection opened.');
  //         panel.webview.postMessage({ command: 'connected' });
  //     };

  //     websocket.onclose = () => {
  //         console.warn('WebSocket connection closed.');
  //         panel.webview.postMessage({ command: 'disconnected' });
  //     };

  //     websocket.onerror = (error) => {
  //         console.error('WebSocket error:', error);
  //         panel.webview.postMessage({ command: 'error', error: error.message });
  //     };

  //     // 监听 WebView 消息
  //     panel.webview.onDidReceiveMessage((message) => {
  //         if (message.command === 'sync') {
  //             websocket.send(
  //                 JSON.stringify({
  //                     type: 'sync',
  //                     state_vector: message.stateVector,
  //                 })
  //             );
  //         } else if (message.command === 'update') {
  //             websocket.send(
  //                 JSON.stringify({
  //                     type: 'update',
  //                     update: message.update,
  //                 })
  //             );
  //         }
  //     });

  //     panel.onDidDispose(() => {
  //         websocket.close();
  //     });
  // },

  getCollaborativeEditorHtml(): string {
    return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Collaborative Editor</title>
    <link href="https://cdn.quilljs.com/1.3.7/quill.snow.css" rel="stylesheet">
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            height: 100vh;
        }
        #editor-container {
            flex: 1;
            width: 100%;
            box-sizing: border-box;
        }
        .status {
            padding: 5px;
            background-color: #f4f4f4;
            border-top: 1px solid #ccc;
            text-align: center;
        }
        #debug {
            max-height: 80px;
            overflow-y: auto;
            background-color: #f9f9f9;
            padding: 5px;
            font-size: 10px;
            border-bottom: 1px solid #ddd;
        }
    </style>
</head>
<body>
    <div id="debug">Initializing Quill editor...</div>
    <div id="editor-container"></div>
    <div class="status" id="status">Connecting...</div>
    
    <!-- 只加载 Quill，不加载 Y.js -->
    <script src="https://cdn.quilljs.com/1.3.7/quill.min.js"></script>
    
<script>
    const vscode = acquireVsCodeApi();
    const statusElement = document.getElementById('status');
    const debugElement = document.getElementById('debug');
    
    let quill = null;
    let isApplyingUpdate = false;
    
    function log(message) {
        console.log(message);
        debugElement.innerHTML += '<br>' + new Date().toLocaleTimeString() + ': ' + message;
        debugElement.scrollTop = debugElement.scrollHeight;
    }
    
    log('Starting Quill editor initialization...');

    // 初始化 Quill 编辑器
    function initQuill() {
        try {
            if (typeof Quill === 'undefined') {
                throw new Error('Quill not loaded');
            }
            
            quill = new Quill('#editor-container', {
                theme: 'snow',
                placeholder: 'Start collaborating...',
                modules: {
                    toolbar: [
                        ['bold', 'italic', 'underline'],
                        [{ 'header': [1, 2, false] }],
                        [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                        ['clean']
                    ],
                    history: {
                        userOnly: true
                    }
                }
            });
            
            log('Quill editor created successfully');
            statusElement.textContent = 'Editor ready - Waiting for connection...';
            
            // 监听用户输入
            quill.on('text-change', (delta, oldDelta, source) => {
                if (source === 'user' && !isApplyingUpdate) {
                    log('User edit detected, sending to extension...');
                    
                    // 发送纯文本内容给扩展
                    vscode.postMessage({
                        command: 'editContent',
                        content: quill.getText(), // 发送纯文本，不是 Delta
                    });
                }
            });
            
            // 隐藏调试信息
            setTimeout(() => {
                debugElement.style.display = 'none';
            }, 8000);
            
        } catch (error) {
            log('Error initializing Quill: ' + error.message);
            statusElement.textContent = 'Error: ' + error.message;
        }
    }

    // 接收来自扩展的消息
    window.addEventListener('message', (event) => {
        const message = event.data;
        log('Received: ' + message.command);

        if (message.command === 'updateContent') {
            if (!quill) {
                log('Quill not ready, skipping update');
                return;
            }
            
            try {
                isApplyingUpdate = true;
                
                log('Applying content update: "' + message.content + '"');
                
                // 获取当前选择位置
                const selection = quill.getSelection();
                
                // 设置纯文本内容
                if (typeof message.content === 'string') {
                    quill.setText(message.content, 'api');
                } else {
                    log('Warning: received non-string content');
                    quill.setText('', 'api');
                }
                
                // 尝试恢复选择位置
                if (selection) {
                    const newLength = quill.getLength() - 1; // -1 for trailing newline
                    const newIndex = Math.min(selection.index, newLength);
                    quill.setSelection(newIndex, 0, 'api');
                }
                
                statusElement.textContent = message.userId ? 
                    \`Updated by user \${message.userId}\` : 
                    'Content synchronized';
                    
                // 2秒后恢复状态
                setTimeout(() => {
                    statusElement.textContent = 'Connected - Ready to collaborate!';
                }, 2000);
                
            } catch (error) {
                log('Error applying update: ' + error.message);
            } finally {
                isApplyingUpdate = false;
            }
            
        } else if (message.command === 'disconnected') {
            statusElement.textContent = 'Disconnected from server';
            log('Disconnected');
            
        } else if (message.command === 'error') {
            statusElement.textContent = \`Error: \${message.error}\`;
            log('Error: ' + message.error);
        }
    });

    // 等待 DOM 加载完成
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initQuill);
    } else {
        setTimeout(initQuill, 100);
    }
</script>
</body>
</html>
    `;
  },
  /**
   * 打开课程聊天的 WebView
   */
  openCourseChatWebView(context: vscode.ExtensionContext, token: string, courseId: number): void {
    const panel = vscode.window.createWebviewPanel(
      'courseChat',
      `Course Chat - ${courseId}`,
      vscode.ViewColumn.One,
      {
        enableScripts: true,
        retainContextWhenHidden: true,
      }
    );

    // 设置 WebView 的 HTML 内容
    panel.webview.html = this.getCourseChatHtml();

    // 创建 WebSocket 连接
    const wsUrl = `ws://localhost:8080/ws/course/chat/${courseId}`;
    console.log(`Connecting to WebSocket URL: ${wsUrl}`);
    // 创建 WebSocket 连接
    const websocket = new WebSocket(wsUrl, {
      headers: {
        "Access-Token": token,
      },
    });

    // 处理 WebSocket 连接打开事件
    websocket.onopen = () => {

      console.log(`WebSocket connection opened: ${wsUrl}`);

      // 发送认证消息和协作参数
      websocket.send(
        JSON.stringify({
          type: 'authenticate',
          token: token,
          course_id: courseId
        })
      );
    };


    websocket.onmessage = (event) => {
      const message = JSON.parse(event.data.toString());
      console.log('Received WebSocket message:', JSON.stringify(message, null, 2));
      // 检查消息类型
      if (message.data.type === 'authenticate') {
        // 特殊处理加入会话的消息
        panel.webview.postMessage({
          command: 'newMessage',
          user: 'System', // 系统消息
          content: `${message.user_username} has joined the chat.`,
        });
      } else {
        // 正常处理聊天消息
        panel.webview.postMessage({
          command: 'newMessage',
          user: message.user_username,
          content: message.data.content || message.data, // 提取消息内容
        });
      }
    };

    websocket.onclose = () => {
      vscode.window.showWarningMessage('Chat connection closed.');
    };

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
      vscode.window.showErrorMessage('WebSocket connection error.');
    };

    // 监听 WebView 消息
    panel.webview.onDidReceiveMessage((message) => {
      if (message.command === 'sendMessage') {
        websocket.send(JSON.stringify({ content: message.content }));
      }
    });

    panel.onDidDispose(() => {
      websocket.close();
    });
  },
  getCourseChatHtml(): string {
    return `
  <!DOCTYPE html>
  <html lang="en">
  <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Course Chat</title>
      <style>
          body {
              font-family: Arial, sans-serif;
              margin: 0;
              padding: 0;
              display: flex;
              flex-direction: column;
              height: 100vh;
          }
          #messages {
              flex: 1;
              overflow-y: auto;
              padding: 10px;
              border-bottom: 1px solid #ccc;
          }
          #input-container {
              display: flex;
              padding: 10px;
              border-top: 1px solid #ccc;
          }
          #message-input {
              flex: 1;
              padding: 10px;
              font-size: 16px;
          }
          #send-button {
              padding: 10px 20px;
              font-size: 16px;
              cursor: pointer;
          }
      </style>
  </head>
  <body>
      <div id="messages"></div>
      <div id="input-container">
          <input id="message-input" type="text" placeholder="Type a message..." />
          <button id="send-button">Send</button>
      </div>
      <script>
          const vscode = acquireVsCodeApi();
window.postMessage({ type: 'log', message: 'Entered initializeWebSocket block' });
          // 发送消息
          document.getElementById('send-button').addEventListener('click', () => {
              const input = document.getElementById('message-input');
              const message = input.value.trim();
              if (message) {
                  vscode.postMessage({ command: 'sendMessage', content: message });
                  input.value = '';
              }
          });

          // 接收来自扩展的消息
          window.addEventListener('message', (event) => {
              const message = event.data;
              if (message.command === 'newMessage') {
                  const messagesDiv = document.getElementById('messages');
                  const messageDiv = document.createElement('div');
                  messageDiv.textContent = \`\${message.user}: \${message.content}\`;
                  messagesDiv.appendChild(messageDiv);
                  messagesDiv.scrollTop = messagesDiv.scrollHeight;
              }
          });
      </script>
  </body>
  </html>
  `;
  },
  async getOrCreateNotebooksDirectoryId(token: string, courseId: number): Promise<number> {
    console.log('Checking for notebooks directory...');
    const directories = await this.getDirectories(token, courseId);

    // Check if "notebooks" directory exists
    const notebooksDirectory = directories.find(dir => dir.name === 'notebooks');
    if (notebooksDirectory) {
      console.log('Notebooks directory found:', notebooksDirectory.id);
      return notebooksDirectory.id;
    }

    // If not found, create the "notebooks" directory
    console.log('Notebooks directory not found. Creating...');
    const newDirectoryId = await this.postDirectory(token, courseId, 'notebooks', undefined);
    console.log('Notebooks directory created with ID:', newDirectoryId);
    return newDirectoryId;
  }
};