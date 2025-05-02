(function () {
    // Get VS Code API
    const vscode = acquireVsCodeApi();

    // Elements
    const chatContainer = document.getElementById('chat-container');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const attachButton = document.getElementById('attach-button');
    const importButton = document.getElementById('import-button');
    const fileInput = document.getElementById('file-input');

    const questionContainer = document.getElementById('question-container');
    const answerInput = document.getElementById('answer-input');
    const submitAnswerButton = document.getElementById('submit-answer-button');
    const progressText = document.getElementById('progress-text');

    const quizContainer = document.getElementById('quiz-container');
    quizContainer.style.display = 'none'; // Ensure it's hidden on load

    const returnToChatButton = document.getElementById('return-to-chat-button');

    let questions = [];
    let currentQuestionIndex = 0;
    let correctAnswers = 0;

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
    importButton.addEventListener('click', () => {
        fileInput.click();
    });
    fileInput.addEventListener('change', async (event) => {
        const file = event.target.files[0];
        if (!file) {
            return;
        }

        const content = await file.text();

        fileInput.value = '';
    });

    fileInput.addEventListener('change', async (event) => {
        const file = event.target.files[0];
        if (!file) return;

        const content = await file.text();
        questions = parseQuizFile(content);

        if (questions.length > 0) {
            showQuizContainer();
            displayQuestion(0);
        }

        fileInput.value = '';
    });

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

    // parse QA file content
    function parseQAFile(content) {
        const lines = content.split('\n');
        const qaPairs = [];
        let currentQuestion = '';
        let currentAnswer = '';

        lines.forEach(line => {
            if (line.startsWith('Q:')) {
                if (currentQuestion && currentAnswer) {
                    qaPairs.push({ question: currentQuestion.trim(), answer: currentAnswer.trim() });
                }
                currentQuestion = line.substring(2).trim();
                currentAnswer = '';
            } else if (line.startsWith('A:')) {
                currentAnswer = line.substring(2).trim();
            } else {
                currentAnswer += ` ${line.trim()}`;
            }
        });

        // add the last pair if exists
        if (currentQuestion && currentAnswer) {
            qaPairs.push({ question: currentQuestion.trim(), answer: currentAnswer.trim() });
        }

        return qaPairs;
    }

    // parse file
    function parseQuizFile(content) {
        const lines = content.split('\n');
        const parsedQuestions = [];
        let currentQuestion = null;

        lines.forEach(line => {
            if (line.startsWith('Q:')) {
                if (currentQuestion) {
                    parsedQuestions.push(currentQuestion);
                }
                currentQuestion = { question: line.substring(2).trim(), options: [], answer: '' };
            } else if (line.match(/^\d+\./)) {
                currentQuestion.options.push(line.trim());
            } else if (line.startsWith('A:')) {
                currentQuestion.answer = line.substring(2).trim();
            }
        });

        if (currentQuestion) {
            parsedQuestions.push(currentQuestion);
        }

        return parsedQuestions;
    }

    // display question
    function displayQuestion(index) {
        const question = questions[index];
        questionContainer.innerHTML = `<p>${question.question}</p>`;

        if (question.options.length > 0) {
            question.options.forEach(option => {
                const optionElement = document.createElement('p');
                optionElement.textContent = option;
                questionContainer.appendChild(optionElement);
            });
        }

        // Update progress text
        progressText.textContent = `Question ${index + 1} of ${questions.length}`;
        progressText.style.display = 'block'; // Ensure progress text is visible

        // Clear the answer input
        answerInput.value = '';
    }

    // submit answer
    submitAnswerButton.addEventListener('click', () => {
        const userAnswer = answerInput.value.trim();
        const correctAnswer = questions[currentQuestionIndex].answer;

        if (userAnswer === correctAnswer) {
            correctAnswers++;
            vscode.postMessage({ command: 'correctAnswer', questionIndex: currentQuestionIndex });
        } else {
            vscode.postMessage({ command: 'wrongAnswer', questionIndex: currentQuestionIndex });
        }

        // Clear the input field after submission
        answerInput.value = '';

        // Show the next question or display the result if all questions are answered
        currentQuestionIndex++;
        if (currentQuestionIndex < questions.length) {
            displayQuestion(currentQuestionIndex);
        } else {
            displayQuizResult();
        }
    });

    // show result
    function displayQuizResult() {
        // Display the result
        questionContainer.innerHTML = `<p>You answered ${correctAnswers} out of ${questions.length} questions correctly!</p>`;

        // Hide input and submit button
        answerInput.style.display = 'none';
        submitAnswerButton.style.display = 'none';
        progressText.style.display = 'none';

        // Show the return button
        showReturnButton();
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