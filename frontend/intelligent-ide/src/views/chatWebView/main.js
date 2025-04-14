(function () {
    // Get VS Code API
    const vscode = acquireVsCodeApi();

    // Elements
    const chatContainer = document.getElementById('chat-container');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const attachButton = document.getElementById('attach-button');

    // Current streaming response element
    let currentStreamingMessage = null;
    let streamingContent = '';

    // Restore previous state if available
    const previousState = vscode.getState() || { messages: [] };
    let messages = previousState.messages;

    // Add welcome message if no messages exist
    if (messages.length === 0) {
        addWelcomeMessage();
    } else {
        // Restore previous messages
        messages.forEach(msg => {
            if (msg.type === 'attachment') {
                addAttachment(msg.filename, msg.content);
            } else {
                addMessageToUI(msg.sender, msg.text);
            }
        });
    }

    // Event listeners
    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keydown', handleKeyDown);
    attachButton.addEventListener('click', requestCodeAttachment);

    // Welcome message
    function addWelcomeMessage() {
        const welcomeDiv = document.createElement('div');
        welcomeDiv.className = 'welcome-message';
        welcomeDiv.textContent = 'Welcome to AI Assistant! How can I help you today?';
        chatContainer.appendChild(welcomeDiv);
    }

    // Send message to extension
    function sendMessage() {
        const text = messageInput.value.trim();
        if (!text) return;

        // Add to UI
        addMessageToUI('user', text);

        // Clear input
        messageInput.value = '';

        // Send to extension
        vscode.postMessage({
            command: 'sendMessage',
            text
        });
    }

    // Handle Enter key
    function handleKeyDown(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
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
        messageDiv.textContent = text;

        chatContainer.appendChild(messageDiv);

        // Auto scroll
        chatContainer.scrollTop = chatContainer.scrollHeight;

        // Save to state
        messages.push({ sender, text });
        vscode.setState({ messages });

        return messageDiv;
    }

    // Start streaming response
    function startStreamingResponse() {
        // Create a new message div for the streaming content
        currentStreamingMessage = document.createElement('div');
        currentStreamingMessage.className = 'message assistant-message';
        streamingContent = '';
        chatContainer.appendChild(currentStreamingMessage);
        return currentStreamingMessage;
    }

    // Update streaming response with new chunk
    function appendToStreamingResponse(chunk) {
        if (!currentStreamingMessage) {
            currentStreamingMessage = startStreamingResponse();
        }

        // Add the new content
        streamingContent += chunk;
        currentStreamingMessage.textContent = streamingContent;

        // Auto scroll
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // Complete streaming response
    function completeStreamingResponse() {
        if (currentStreamingMessage && streamingContent) {
            // Save to state
            messages.push({ sender: 'assistant', text: streamingContent });
            vscode.setState({ messages });

            // Reset streaming variables
            currentStreamingMessage = null;
            streamingContent = '';
        }
    }

    // Add code attachment
    function addAttachment(filename, content) {
        const attachmentDiv = document.createElement('div');
        attachmentDiv.className = 'attachment';

        const header = document.createElement('div');
        header.className = 'attachment-header';
        header.textContent = `File: ${filename}`;

        const pre = document.createElement('pre');
        pre.textContent = content;

        attachmentDiv.appendChild(header);
        attachmentDiv.appendChild(pre);
        chatContainer.appendChild(attachmentDiv);

        // Auto scroll
        chatContainer.scrollTop = chatContainer.scrollHeight;

        // Save to state
        messages.push({ type: 'attachment', filename, content });
        vscode.setState({ messages });
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

            case 'aiResponse':
                // Legacy non-streaming support
                addMessageToUI('assistant', message.text);
                break;

            case 'codeAttachment':
                addAttachment(message.filename, message.text);
                break;

            case 'clear':
                // Clear all messages from UI
                chatContainer.innerHTML = '';
                // Reset messages array
                messages = [];
                vscode.setState({ messages });
                // Add welcome message back
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
})();