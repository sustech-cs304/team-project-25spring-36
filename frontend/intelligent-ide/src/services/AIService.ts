import * as vscode from 'vscode';
import OpenAI from 'openai';
import {  OPENAI_API_MODEL } from '../resources/configs/config';

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
    let apiKey: string | undefined ;

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
    attachments: any[], // Pass in vector store IDs for file search
    context: vscode.ExtensionContext,
    onChunk: (chunk: string) => void
): Promise<string> {
    try {
        if (!openaiClient) {
            const apiKey = await getOpenAIKey(context);
            initializeAIService(apiKey);
        }
        if (!openaiClient) {
            throw new Error('OpenAI client not initialized');
        }

        // Setup tools array if vector store is used
        let tools: any[] = [];

        let vectorStoreIds: string[] = [];
        if (attachments && attachments.length > 0) {
            const filePaths: string[] = [];
            for (const attachment of attachments) { 
                filePaths.push(attachment.filePath);
            }
            const vectorStoreId = await uploadFile(filePaths);
            if (vectorStoreId) {
                vectorStoreIds.push(vectorStoreId);
            }
        }
        if (vectorStoreIds.length > 0) {
            tools.push({
                type: "file_search",
                vector_store_ids: vectorStoreIds,
                max_num_results: 20 // Optional: tune as needed
            });
        }

        let completeResponse = '';
        let abortController = new AbortController();

        // Compose input
        const input = userMessage;

        // Send request to /v1/responses endpoint with streaming
        const stream = await openaiClient.responses.create({
            model: OPENAI_API_MODEL,
            input,
            previous_response_id: lastResponseId,
            tools: tools.length > 0 ? tools : undefined,
            stream: true,
        }, {
            signal: abortController.signal
        });

        let newResponseId: string | undefined = undefined;

         for await (const event of stream) {
        // OpenAI SDK: event.type always present
        switch (event.type) {
            case "response.output_text.delta":
                // Get incremental content
                if (typeof event.delta === 'string' && event.delta.length > 0) {
                    completeResponse += event.delta;
                    onChunk(event.delta);
                }
                break;
            // Optionally handle other events for progress/status
            case "response.created":
            case "response.in_progress":
            case "response.output_text.done":
            case "response.content_part.done":
            case "response.output_item.done":
                break;
            case "response.completed":
                if (!newResponseId && event.response?.id) {
                    newResponseId = event.response.id;
                }
                break;
        }
    }

    // Save for next request
    if (newResponseId) {
        lastResponseId = newResponseId;
    }


        return completeResponse || 'Sorry, I couldn\'t generate a response';
    } catch (error: any) {
        if (error.message === 'TERMINATED') {
            throw error;
        }
        console.error('Error getting AI streaming response:', error);
        throw new Error(`Failed to get AI response: ${error.message}`);
    }
}



/**
 * Upload multiple files, batch them into a single vector store, and wait for ingestion.
 * Returns the vector_store_id ready for file_search tools.
 */
async function uploadFile(filePaths: string[], vectorStoreName: string = 'VSCode Vector Store'): Promise<string | null> {
    if (!openaiClient) {throw new Error('OpenAI client not initialized');}
    try {
        const fs = require('fs');
        const path = require('path');

        // 1. Upload all files and collect file IDs
        const fileIds: string[] = [];
        for (const filePath of filePaths) {
            const fileStream = fs.createReadStream(filePath);
            const file = await openaiClient.files.create({
                file: fileStream,
                purpose: 'user_data',
            });
            fileIds.push(file.id);
        }

        // 2. Create a vector store
        const vectorStore = await openaiClient.vectorStores.create({ name: vectorStoreName });
        const vectorStoreId = vectorStore.id;

        // 3. Attach all files as a batch to the vector store
        const fileBatch = await openaiClient.vectorStores.fileBatches.create(vectorStoreId, {
            file_ids: fileIds
        });
        const fileBatchId = fileBatch.id;

        // 4. Wait for ingestion to complete (polling)
        let status = 'in_progress';
        let waited = 0;
        while (status !== 'completed' && waited < 120) { // Wait up to 2 minutes
            await new Promise(res => setTimeout(res, 2000));
            const batchStatus = await openaiClient.vectorStores.fileBatches.retrieve(vectorStoreId, fileBatchId);
            status = batchStatus.status;
            waited += 2;
        }
        if (status !== 'completed') {
            throw new Error('Vector store ingestion timed out');
        }

        // 5. Return the vector store ID
        return vectorStoreId;
    } catch (error) {
        console.error('Error in uploadFilesAndGetVectorStoreId:', error);
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