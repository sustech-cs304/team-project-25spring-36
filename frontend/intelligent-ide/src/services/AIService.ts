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
 * Send a message to OpenAI API and get a respons
 */
export async function getChatResponse(userMessage: string, context: vscode.ExtensionContext): Promise<string> {
    try {
        // Make sure we have an API key and client
        if (!openaiClient) {
            const apiKey = await getOpenAIKey(context);
            initializeAIService(apiKey);
        }

        if (!openaiClient) {
            throw new Error('OpenAI client not initialized');
        }

        let response;

        // If we have a previous response, continue the conversation
        if (lastResponseId) {
            response = await openaiClient.responses.create({
                model: OPENAI_API_MODEL,
                previous_response_id: lastResponseId,
                input: [{ role: "user", content: userMessage }],
                store: true,
            });
        } else {
            // Start a new conversation with history
            response = await openaiClient.responses.create({
                model: OPENAI_API_MODEL,
                input: conversationHistory.concat({ role: "user", content: userMessage }),
                store: true,
            });
        }

        // Store the response ID for the next message
        lastResponseId = response.id;

        // Add messages to conversation history for backup
        conversationHistory.push({ role: 'user', content: userMessage });
        if (response.output_text) {
            conversationHistory.push({ role: 'assistant', content: response.output_text });
        }

        return response.output_text || 'Sorry, I couldn\'t generate a response';
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

        let completeResponse = '';
        let stream;

        // If we have a previous response, continue the conversation
        if (lastResponseId) {
            stream = await openaiClient.chat.completions.create({
                model: OPENAI_API_MODEL,
                messages: [{ role: "user", content: userMessage }],
                stream: true,
            });
        } else {
            // Start a new conversation with history
            stream = await openaiClient.chat.completions.create({
                model: OPENAI_API_MODEL,
                messages: conversationHistory.concat({ role: "user", content: userMessage }),
                stream: true,
            });
        }

        // Handle the streaming response
        for await (const chunk of stream) {
            // Extract the content from the chunk
            const content = chunk.choices[0]?.delta?.content || '';
            if (content) {
                completeResponse += content;
                onChunk(content);
            }

            // Store the response ID for the next message if available
            if (chunk.id) {
                lastResponseId = chunk.id;
            }
        }

        // Add messages to conversation history for backup
        conversationHistory.push({ role: 'user', content: userMessage });
        conversationHistory.push({ role: 'assistant', content: completeResponse });

        return completeResponse || 'Sorry, I couldn\'t generate a response';
    } catch (error: any) {
        console.error('Error getting AI streaming response:', error);
        throw new Error(`Failed to get AI response: ${error.message}`);
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