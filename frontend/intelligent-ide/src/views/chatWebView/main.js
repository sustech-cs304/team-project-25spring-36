(function () {
    // Get VS Code API
    const vscode = acquireVsCodeApi();

    // Elements
    const chatContainer = document.getElementById('chat-container');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const attachButton = document.getElementById('attach-button');
    const attachmentsPanel = document.getElementById('attachments-panel');
    const inputContainer = document.getElementById('input-container');

    // Flag to track if response is streaming
    let isStreaming = false;

    // Initialize markdown converter
    let converter;
    if (typeof showdown !== 'undefined') {
        converter = new showdown.Converter({
            tables: true,
            tasklists: true,
            strikethrough: true,
            emoji: true
        });
    }

    // Current streaming response element
    let currentStreamingMessage = null;
    let streamingContent = '';

    // Restore previous state if available
    const previousState = vscode.getState() || { messages: [] };
    let messages = previousState.messages;

    // Store attachments in an array
    let attachments = [];

    // Add welcome message if no messages exist
    if (messages.length === 0) {
        addWelcomeMessage();
    } else {
        // Restore previous messages
        messages.forEach(msg => {
            if (msg.type === 'attachment') {
                addAttachment({
                    type: 'code',
                    filename: msg.filename,
                    content: msg.content
                });
            } else {
                addMessageToUI(msg.sender, msg.text);
            }
        });
    }

    // Initialize chat UI
    document.addEventListener('DOMContentLoaded', () => {
        sendButton.addEventListener('click', handleSendButtonClick);
        messageInput.addEventListener('keydown', handleKeyDown);
        attachButton.addEventListener('click', requestCodeAttachment);

        // Add drag and drop events
        setupDragAndDrop();

        updateAttachmentsPanel();
    });

    // Welcome message
    function addWelcomeMessage() {
        const welcomeDiv = document.createElement('div');
        welcomeDiv.className = 'welcome-message';
        welcomeDiv.textContent = 'Welcome to AI Assistant! How can I help you today?';
        chatContainer.appendChild(welcomeDiv);
    }

    // Handle send button click based on current state
    function handleSendButtonClick() {
        if (isStreaming) {
            terminateResponse();
        } else {
            sendMessage();
        }
    }

    // Send message to extension
    function sendMessage() {
        const text = messageInput.value.trim();
        if (text || attachments.length > 0) {
            addUserMessage(text, attachments);
            vscode.postMessage({
                command: 'sendMessage',
                text: text,
                attachments: attachments
            });
            messageInput.value = '';

            // Clear attachments after sending
            attachments = [];
            updateAttachmentsPanel();

            // Update button to terminate mode
            updateButtonToTerminate();
        }
    }

    // Terminate the streaming response
    function terminateResponse() {
        vscode.postMessage({
            command: 'terminateResponse'
        });

        // Don't restore button yet - wait for the confirmation from backend
    }

    // Update button to terminate mode
    function updateButtonToTerminate() {
        isStreaming = true;
        sendButton.textContent = 'Stop';
        sendButton.classList.add('terminate-button');
        messageInput.disabled = true;
        attachButton.disabled = true;
    }

    // Restore button to send mode
    function restoreButton() {
        isStreaming = false;
        sendButton.textContent = 'Send';
        sendButton.classList.remove('terminate-button');
        messageInput.disabled = false;
        attachButton.disabled = false;
    }

    // Handle Enter key
    function handleKeyDown(e) {
        if (e.key === 'Enter' && !e.shiftKey && !isStreaming) {
            e.preventDefault();
            sendMessage();
        }
    }

    // Request code attachment from extension
    function requestCodeAttachment() {
        vscode.postMessage({
            command: 'attachCode'
        });
    }

    // Add message to UI
    function addMessageToUI(sender, text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;

        // Apply markdown rendering for assistant messages
        if (sender === 'assistant' && converter) {
            try {
                let html = converter.makeHtml(text);
                if (window.DOMPurify) {
                    html = window.DOMPurify.sanitize(html);
                }
                messageDiv.innerHTML = html;
                // Highlight code blocks
                if (window.hljs) {
                    messageDiv.querySelectorAll('pre code').forEach(block => {
                        window.hljs.highlightElement(block);
                    });
                }
            } catch (e) {
                messageDiv.textContent = text;
            }
        } else {
            messageDiv.textContent = text;
        }

        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        messages.push({ sender, text });
        vscode.setState({ messages });
        return messageDiv;
    }

    // Add user message to the UI
    function addUserMessage(text, messageAttachments) {
        const messageDiv = addMessageToUI('user', text);

        // If there are attachments, add them to the message
        if (messageAttachments && messageAttachments.length > 0) {
            const attachmentsContainer = document.createElement('div');
            attachmentsContainer.className = 'message-attachments';

            messageAttachments.forEach(attachment => {
                const attachmentItem = document.createElement('div');
                attachmentItem.className = 'message-attachment';
                attachmentItem.textContent = `📎 ${attachment.filename}`;
                attachmentsContainer.appendChild(attachmentItem);
            });

            messageDiv.appendChild(attachmentsContainer);
        }
    }

    // Start streaming response
    function startStreamingResponse() {
        currentStreamingMessage = document.createElement('div');
        currentStreamingMessage.className = 'message assistant-message';
        streamingContent = '';
        chatContainer.appendChild(currentStreamingMessage);
        updateButtonToTerminate();
        return currentStreamingMessage;
    }

    // Update streaming response with new chunk
    function appendToStreamingResponse(chunk) {
        if (!currentStreamingMessage) {
            currentStreamingMessage = startStreamingResponse();
        }
        streamingContent += chunk;
        if (converter) {
            try {
                let html = converter.makeHtml(streamingContent);
                if (window.DOMPurify) {
                    html = window.DOMPurify.sanitize(html);
                }
                currentStreamingMessage.innerHTML = html;
                // Highlight code blocks
                if (window.hljs) {
                    currentStreamingMessage.querySelectorAll('pre code').forEach(block => {
                        window.hljs.highlightElement(block);
                    });
                }
            } catch (e) {
                currentStreamingMessage.textContent = streamingContent;
            }
        } else {
            currentStreamingMessage.textContent = streamingContent;
        }
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // Complete streaming response
    function completeStreamingResponse() {
        if (currentStreamingMessage && streamingContent) {
            messages.push({ sender: 'assistant', text: streamingContent });
            vscode.setState({ messages });
            currentStreamingMessage = null;
            streamingContent = '';
            restoreButton();
        }
    }

    // Add a new attachment to the list
    function addAttachment(attachment) {
        attachments.push(attachment);
        updateAttachmentsPanel();
    }

    // Remove an attachment from the list
    function removeAttachment(index) {
        attachments.splice(index, 1);
        updateAttachmentsPanel();
    }

    // Update the attachments panel in the UI
    function updateAttachmentsPanel() {
        if (!attachmentsPanel) return;

        attachmentsPanel.innerHTML = '';

        if (attachments.length === 0) {
            attachmentsPanel.style.display = 'none';
            return;
        }

        attachmentsPanel.style.display = 'flex';
        attachments.forEach((attachment, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'attachment-item';

            const fileIcon = document.createElement('span');
            fileIcon.className = `file-icon ${attachment.type}`;
            fileIcon.textContent = getFileIconText(attachment.type);

            const fileName = document.createElement('span');
            fileName.className = 'file-name';
            fileName.textContent = attachment.filename;

            const removeBtn = document.createElement('button');
            removeBtn.className = 'remove-attachment';
            removeBtn.textContent = '×';
            removeBtn.addEventListener('click', () => {
                attachments.splice(index, 1);
                updateAttachmentsPanel();
            });

            fileItem.appendChild(fileIcon);
            fileItem.appendChild(fileName);
            fileItem.appendChild(removeBtn);
            attachmentsPanel.appendChild(fileItem);
        });
    }

    // Get icon text based on file type
    function getFileIconText(type) {
        switch (type) {
            case 'image': return '🖼️';
            case 'pdf': return '📄';
            case 'code': return '📝';
            case 'text': return '📃';
            default: return '📎';
        }
    }

    // Setup drag and drop functionality
    function setupDragAndDrop() {
        // Add drop zone indicator
        const dropZone = document.createElement('div');
        dropZone.id = 'drop-zone';
        dropZone.innerHTML = '<div class="drop-message">Drop files here to attach</div>';
        document.body.appendChild(dropZone);

        // Track drag state
        let isDragging = false;

        // Add drag events with capture phase to intercept VS Code's handling
        document.addEventListener('dragover', handleDragOver, true);
        document.addEventListener('dragenter', handleDragEnter, true);
        document.addEventListener('dragleave', handleDragLeave, true);
        document.addEventListener('drop', handleDrop, true);

        function handleDragEnter(e) {
            // Always prevent default to override VS Code's behavior
            e.preventDefault();
            e.stopPropagation();

            isDragging = true;
            dropZone.classList.add('active');
        }

        function handleDragOver(e) {
            // Always prevent default for all drag operations
            e.preventDefault();
            e.stopPropagation();

            // Set copy effect to indicate attachment rather than opening
            e.dataTransfer.dropEffect = 'copy';

            if (!isDragging) {
                dropZone.classList.add('active');
                isDragging = true;
            }
        }

        function handleDragLeave(e) {
            e.preventDefault();
            e.stopPropagation();

            // Only remove active state when truly leaving the document body
            const rect = document.body.getBoundingClientRect();
            if (
                e.clientX <= rect.left ||
                e.clientX >= rect.right ||
                e.clientY <= rect.top ||
                e.clientY >= rect.bottom
            ) {
                dropZone.classList.remove('active');
                isDragging = false;
            }
        }

        function handleDrop(e) {
            // Most important: prevent default behavior
            e.preventDefault();
            e.stopPropagation();

            // Hide drop zone
            dropZone.classList.remove('active');
            isDragging = false;

            // Collect file paths from various sources
            const filePaths = [];

            // Handle VS Code internal file drops (resources from the explorer)
            if (e.dataTransfer.getData('resourceURLs')) {
                try {
                    // VS Code stores dragged internal resources as JSON string of URLs
                    const resourceURLs = JSON.parse(e.dataTransfer.getData('resourceURLs'));
                    if (Array.isArray(resourceURLs)) {
                        resourceURLs.forEach(url => filePaths.push(url));
                    }
                } catch (error) {
                    console.error('Error parsing VS Code resource URLs', error);
                }
            }

            // Also check for text/uri-list format (common for internal file drag)
            if (e.dataTransfer.getData('text/uri-list')) {
                const uriList = e.dataTransfer.getData('text/uri-list').split('\n');
                uriList.forEach(uri => {
                    if (uri && !uri.startsWith('#')) {
                        filePaths.push(uri.trim());
                    }
                });
            }

            // Check for regular files (external drags from Finder/Explorer)
            if (e.dataTransfer.files.length > 0) {
                for (let i = 0; i < e.dataTransfer.files.length; i++) {
                    const file = e.dataTransfer.files[i];
                    // Use path property if available (Electron apps have this)
                    if (file.path) {
                        filePaths.push(file.path);
                    } else {
                        // Fallback to name for web context
                        filePaths.push(file.name);
                    }
                }
            }

            // Fall back to text/plain if nothing else worked (VS Code sometimes uses this)
            if (filePaths.length === 0 && e.dataTransfer.getData('text/plain')) {
                const text = e.dataTransfer.getData('text/plain');
                // Check if it looks like a file path or URI
                if (text.startsWith('file:') || text.includes('/') || text.includes('\\')) {
                    filePaths.push(text);
                }
            }

            // Send collected paths to extension
            if (filePaths.length > 0) {
                vscode.postMessage({
                    command: 'dropFiles',
                    filePaths: filePaths
                });
            }
        }
    }

    // Listen for messages from the extension
    window.addEventListener('message', event => {
        const message = event.data;

        switch (message.command) {
            case 'aiResponseStart':
                startStreamingResponse();
                break;
            case 'aiResponseChunk':
                appendToStreamingResponse(message.text);
                break;
            case 'aiResponseComplete':
                completeStreamingResponse();
                break;
            case 'aiResponseTerminated':
                // Handle terminated response
                if (currentStreamingMessage) {
                    appendToStreamingResponse('\n\n*Response terminated*');
                    completeStreamingResponse();
                }
                break;
            case 'aiResponse':
                addMessageToUI('assistant', message.text);
                break;
            case 'codeAttachment':
                addAttachment({
                    type: 'code',
                    filename: message.filename,
                    content: message.content || message.text,
                    filePath: message.filePath
                });
                break;
            case 'fileAttachment':
                addAttachment({
                    type: message.fileType,
                    filename: message.filename,
                    content: message.content,
                    filePath: message.filePath
                });
                break;
            case 'clear':
                chatContainer.innerHTML = '';
                messages = [];
                vscode.setState({ messages });
                addWelcomeMessage();
                break;
            case 'error':
                const errorDiv = document.createElement('div');
                errorDiv.className = 'message system-message';
                errorDiv.textContent = message.text;
                chatContainer.appendChild(errorDiv);
                chatContainer.scrollTop = chatContainer.scrollHeight;
                break;
        }
    });

    function showChatContainer() {
        document.getElementById('chat-container').style.display = 'block';
        document.getElementById('quiz-container').style.display = 'none';
    }

    function showQuizContainer() {
        document.getElementById('chat-container').style.display = 'none';
        document.getElementById('quiz-container').style.display = 'block';
    }

    // Show the return button
    function showReturnButton() {
        returnToChatButton.style.display = 'block';
    }

    // Hide the return button
    function hideReturnButton() {
        returnToChatButton.style.display = 'none';
    }

    // Add click event to the return button
    returnToChatButton.addEventListener('click', () => {
        showChatContainer(); // Switch back to the chat container
        hideReturnButton(); // Hide the return button
    });
})();