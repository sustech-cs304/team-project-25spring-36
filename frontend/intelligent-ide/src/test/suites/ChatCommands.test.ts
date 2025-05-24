import * as assert from 'assert';
import * as sinon from 'sinon';
import * as vscode from 'vscode';
import * as viewManager from '../../views/viewManager';
import * as ai from '../../services/AIService';
import { registerChatCommands } from '../../commands/ChatCommands';

suite('Chat Commands Test Suite', () => {
    let mockContext: vscode.ExtensionContext;
    let mockCommands: Record<string, (...args: any[]) => any>;
    
    // VS Code API stubs
    let showInfoMessageStub: sinon.SinonStub;
    let showErrorMessageStub: sinon.SinonStub;
    
    // View manager stubs
    let refreshViewsStub: sinon.SinonStub;
    let getChatViewPanelStub: sinon.SinonStub;
    
    // AI Service stub
    let clearConversationStub: sinon.SinonStub;
    
    // Mock WebView panel
    let mockWebviewPanel: {
        webview: {
            postMessage: sinon.SinonStub;
        }
    };

    setup(() => {
        sinon.restore();
        
        mockContext = {
            subscriptions: []
        } as unknown as vscode.ExtensionContext;
        
        mockCommands = {};
        
        sinon.stub(vscode.commands, 'registerCommand').callsFake((commandId, handler) => {
            mockCommands[commandId] = handler;
            return { dispose: () => { } };
        });
        
        sinon.stub(vscode.commands, 'executeCommand').callsFake((commandId, ...args) => {
            if (mockCommands[commandId]) {
                return Promise.resolve(mockCommands[commandId](...args));
            }
            return Promise.resolve(undefined);
        });
        
        // VS Code window stubs
        showInfoMessageStub = sinon.stub(vscode.window, 'showInformationMessage').resolves(undefined);
        showErrorMessageStub = sinon.stub(vscode.window, 'showErrorMessage').resolves(undefined);
        
        // Mock webview panel
        mockWebviewPanel = {
            webview: {
                postMessage: sinon.stub().returns(true)
            }
        };
        
        // View manager stubs
        refreshViewsStub = sinon.stub(viewManager, 'refreshViews').resolves();
        getChatViewPanelStub = sinon.stub(viewManager, 'getChatViewPanel').returns(mockWebviewPanel as any);
        
        // AI service stub
        clearConversationStub = sinon.stub(ai, 'clearConversation');
        
        // Register commands
        registerChatCommands(mockContext);
    });

    teardown(() => {
        sinon.restore();
    });

    test('Open chat command - successful', async () => {
        await vscode.commands.executeCommand('intelligent-ide.chat.open');
        
        assert.ok(refreshViewsStub.calledWith([viewManager.ViewType.CHAT]), 
            "refreshViews should be called with CHAT view type");
        assert.ok(showInfoMessageStub.calledWithMatch(/Chat assistant ready/), 
            "Info message should confirm chat is ready");
    });
    
    test('Open chat command - error handling', async () => {
        const error = new Error('View refresh failed');
        refreshViewsStub.rejects(error);
        
        await vscode.commands.executeCommand('intelligent-ide.chat.open');
        
        assert.ok(showErrorMessageStub.calledWithMatch(/Failed to open chat/), 
            "Error message should be shown");
        assert.ok(showErrorMessageStub.calledWithMatch(/View refresh failed/), 
            "Error message should contain the error details");
    });

    test('Clear conversation command - with open panel', async () => {
        await vscode.commands.executeCommand('intelligent-ide.chat.clear');
        
        assert.ok(clearConversationStub.calledOnce, 
            "AI service clearConversation should be called");
        assert.ok(mockWebviewPanel.webview.postMessage.calledWith({ command: 'clear' }), 
            "Webview should receive clear command");
        assert.ok(showInfoMessageStub.calledWithMatch(/conversation history cleared/), 
            "Info message should confirm conversation cleared");
    });
    
    test('Clear conversation command - without open panel', async () => {
        getChatViewPanelStub.returns(undefined);
        
        await vscode.commands.executeCommand('intelligent-ide.chat.clear');
        
        assert.ok(clearConversationStub.calledOnce, 
            "AI service clearConversation should still be called");
        assert.ok(!mockWebviewPanel.webview.postMessage.called, 
            "No webview message should be sent");
        assert.ok(showInfoMessageStub.calledWithMatch(/conversation history cleared/), 
            "Info message should still confirm conversation cleared");
    });
    
    test('Clear conversation command - error handling', async () => {
        const error = new Error('Failed to clear AI state');
        clearConversationStub.throws(error);
        
        await vscode.commands.executeCommand('intelligent-ide.chat.clear');
        
        assert.ok(showErrorMessageStub.calledWithMatch(/Failed to clear conversation/), 
            "Error message should be shown");
        assert.ok(showErrorMessageStub.calledWithMatch(/Failed to clear AI state/), 
            "Error message should contain the error details");
    });
});