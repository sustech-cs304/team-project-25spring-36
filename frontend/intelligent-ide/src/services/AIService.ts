import * as vscode from 'vscode';
import OpenAI from 'openai';
import { OPENAI_API_KEY, OPENAI_API_MODEL } from '../resources/configs/config';

// Store conversation history
let conversationHistory: { role: 'system' | 'user' | 'assistant', content: string }[] = [
    {
        role: 'system',
        content: 'You are an AI assistant integrated into VS Code. Help the user with programming questions, code explanations, and other development tasks.'
    }
];

// Store the OpenAI instance
let openaiClient: OpenAI | undefined;
let lastResponseId: string | undefined;

/**
 * Initialize the OpenAI client with API key
 */
export function initializeAIService(apiKey: string): void {
    try {
        openaiClient = new OpenAI({
            apiKey: apiKey
        });
    } catch (error) {
        console.error('Failed to initialize OpenAI client:', error);
        throw error;
    }
}

/**
 * Get API key from config, extension settings, or prompt user to enter it
 */
export async function getOpenAIKey(context: vscode.ExtensionContext): Promise<string> {
    // First try to get from config
    let apiKey: string | undefined = OPENAI_API_KEY;

    // If not found, try to get from settings
    if (!apiKey) {
        const config = vscode.workspace.getConfiguration('intelligentIde');
        apiKey = config.get<string>('openaiApiKey');
    }

    // If not found, try to get from secrets storage
    if (!apiKey) {
        apiKey = await context.secrets.get('openai-api-key');
    }

    // If still not found, prompt the user
    if (!apiKey) {
        apiKey = await promptForAPIKey(context);
    }

    if (!apiKey) {
        throw new Error('OpenAI API key is required to use AI features');
    }

    return apiKey;
}

/**
 * Prompt user for API key and save it
 */
async function promptForAPIKey(context: vscode.ExtensionContext): Promise<string | undefined> {
    const apiKey = await vscode.window.showInputBox({
        prompt: 'Please enter your OpenAI API key',
        password: true,
        ignoreFocusOut: true
    });

    if (apiKey) {
        // Save to secrets storage
        await context.secrets.store('openai-api-key', apiKey);
    }

    return apiKey;
}

/**
 * Send a message to OpenAI API and get a response
 */
export async function getChatResponse(
    userMessage: string,
    attachments: any[] = [],
    context: vscode.ExtensionContext
): Promise<string> {
    try {
        // Make sure we have an API key and client
        if (!openaiClient) {
            const apiKey = await getOpenAIKey(context);
            initializeAIService(apiKey);
        }

        if (!openaiClient) {
            throw new Error('OpenAI client not initialized');
        }

        // Format message content with attachments
        let formattedMessage = userMessage;

        // Add attachments to the message
        if (attachments && attachments.length > 0) {
            formattedMessage += '\n\n--- Attachments ---\n';
            for (const attachment of attachments) {
                formattedMessage += `\n### ${attachment.filename} (${attachment.type}) ###\n`;
                if (attachment.type === 'code' && attachment.content) {
                    // Include code content directly
                    formattedMessage += `\n\`\`\`\n${attachment.content}\n\`\`\`\n`;
                } else {
                    // Reference to non-code files
                    formattedMessage += `[File reference: ${attachment.filePath}]\n`;
                }
            }
        }

        // Prepare messages for the API
        const messages = [
            ...conversationHistory,
            { role: 'user' as const, content: formattedMessage }
        ];

        // Send request to OpenAI
        const response = await openaiClient.chat.completions.create({
            model: OPENAI_API_MODEL,
            messages: messages
        });

        const assistantResponse = response.choices[0]?.message?.content || 'Sorry, I couldn\'t generate a response';

        // Add messages to conversation history
        conversationHistory.push({ role: 'user', content: formattedMessage });
        conversationHistory.push({ role: 'assistant', content: assistantResponse });

        return assistantResponse;
    } catch (error: any) {
        console.error('Error getting AI response:', error);
        throw new Error(`Failed to get AI response: ${error.message}`);
    }
}

/**
 * Send a message to OpenAI API and get a streaming response
 */
export async function getChatResponseStream(
    userMessage: string,
    attachments: any[],
    context: vscode.ExtensionContext,
    onChunk: (chunk: string) => void
): Promise<string> {
    try {
        // Make sure we have an API key and client
        if (!openaiClient) {
            const apiKey = await getOpenAIKey(context);
            initializeAIService(apiKey);
        }

        if (!openaiClient) {
            throw new Error('OpenAI client not initialized');
        }

        // Format message content with attachments
        let formattedMessage = userMessage;

        // Add attachments to the message
        if (attachments && attachments.length > 0) {
            formattedMessage += '\n\n--- Attachments ---\n';
            for (const attachment of attachments) {
                formattedMessage += `\n### ${attachment.filename} (${attachment.type}) ###\n`;
                if (attachment.type === 'code' && attachment.content) {
                    // Include code content directly
                    formattedMessage += `\n\`\`\`\n${attachment.content}\n\`\`\`\n`;
                } else {
                    // Reference to non-code files
                    formattedMessage += `[File reference: ${attachment.filePath}]\n`;
                }
            }
        }

        // Prepare messages for the API
        const messages = [
            ...conversationHistory,
            { role: 'user' as const, content: formattedMessage }
        ];

        let completeResponse = '';
        let abortController = new AbortController();

        // Create the streaming completion with abort controller
        const stream = await openaiClient.chat.completions.create({
            model: OPENAI_API_MODEL,
            messages: messages,
            stream: true,
        }, {
            signal: abortController.signal
        });

        // Handle the streaming response
        try {
            for await (const chunk of stream) {
                // Extract the content from the chunk
                const content = chunk.choices[0]?.delta?.content || '';
                if (content) {
                    completeResponse += content;
                    onChunk(content);
                }
            }
        } catch (e: any) {
            // Check if this was aborted
            if (e.name === 'AbortError') {
                throw new Error('TERMINATED');
            }
            throw e;
        }

        // Add messages to conversation history
        conversationHistory.push({ role: 'user', content: formattedMessage });
        conversationHistory.push({ role: 'assistant', content: completeResponse });

        return completeResponse || 'Sorry, I couldn\'t generate a response';
    } catch (error: any) {
        // If it's our special termination error, handle it differently
        if (error.message === 'TERMINATED') {
            throw error;
        }

        console.error('Error getting AI streaming response:', error);
        throw new Error(`Failed to get AI response: ${error.message}`);
    }
}

/**
 * Upload a file to OpenAI and get the file ID
 */
async function uploadFileToOpenAI(filePath: string): Promise<string | null> {
    if (!openaiClient) {
        throw new Error('OpenAI client not initialized');
    }

    try {
        const fs = require('fs');
        const fileData = fs.readFileSync(filePath);
        const fileName = require('path').basename(filePath);

        const file = await openaiClient.files.create({
            file: fileData,
            purpose: 'assistants',
        });

        return file.id;
    } catch (error) {
        console.error('Error uploading file to OpenAI:', error);
        return null;
    }
}

/**
 * Clear the conversation history and reset the conversation
 */
export function clearConversation(): void {
    // Keep only the system message
    conversationHistory = conversationHistory.filter(msg => msg.role === 'system');
    lastResponseId = undefined;
}

/**
 * Get the current conversation history
 */
export function getConversationHistory(): { role: 'system' | 'user' | 'assistant', content: string }[] {
    return [...conversationHistory];
}