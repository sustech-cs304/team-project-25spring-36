import * as assert from 'assert';
import * as sinon from 'sinon';
import * as vscode from 'vscode';
import { authenticationService } from '../../services/userService';
import * as viewManager from '../../views/viewManager';
import * as authUtils from '../../utils/authUtils';
import { registerUserCommands } from '../../commands/UserCommands';

suite('User Commands Test Suite', () => {
    // Context and state mocks with proper types
    let mockContext: vscode.ExtensionContext;
    let mockGlobalState: Map<string, any>;
    let mockSecrets: {
        store: sinon.SinonStub<[string, string], Promise<void>>;
        get: sinon.SinonStub<[string], Promise<string | undefined>>;
        delete: sinon.SinonStub<[string], Promise<void>>;
    };
    let mockCommands: Record<string, (...args: any[]) => any>;
    let globalStateUpdateStub: sinon.SinonStub<[string, any], Promise<void>>;

    // VS Code API stubs with proper return types
    let showInputBoxStub: sinon.SinonStub<Parameters<typeof vscode.window.showInputBox>, ReturnType<typeof vscode.window.showInputBox>>;
    let showQuickPickStub: sinon.SinonStub<Parameters<typeof vscode.window.showQuickPick>, ReturnType<typeof vscode.window.showQuickPick>>;
    let showInfoMessageStub: sinon.SinonStub<Parameters<typeof vscode.window.showInformationMessage>, ReturnType<typeof vscode.window.showInformationMessage>>;
    let showErrorMessageStub: sinon.SinonStub<Parameters<typeof vscode.window.showErrorMessage>, ReturnType<typeof vscode.window.showErrorMessage>>;
    let showWarningMessageStub: sinon.SinonStub<Parameters<typeof vscode.window.showWarningMessage>, ReturnType<typeof vscode.window.showWarningMessage>>;

    // View manager stubs
    let refreshAllViewsStub: sinon.SinonStub;
    let refreshViewsStub: sinon.SinonStub;

    // Auth utils stub
    let getAuthDetailsStub: sinon.SinonStub;

    // Service stubs with proper return types
    let loginStub: sinon.SinonStub<[string, string], Promise<string>>;
    let registerStub: sinon.SinonStub<[string, string, string, string], Promise<string>>;
    let updateStub: sinon.SinonStub<[string, string, string], Promise<string>>;
    let getUserInfoStub: sinon.SinonStub<[string, vscode.ExtensionContext], Promise<any>>;
    let getVerificationCodeStub: sinon.SinonStub<[string], Promise<string>>;

    const mockToken = 'mock-token-123';
    const mockLoginInfo = {
        id: 1,
        email: 'test@example.com',
        username: 'testuser',
        role: 'student' as 'student',
        token: mockToken
    };

    setup(() => {
        // Reset mocks before each test
        sinon.restore();

        // Setup mock global state
        mockGlobalState = new Map<string, any>();

        // Setup mock secrets with proper typings
        mockSecrets = {
            store: sinon.stub<[string, string], Promise<void>>().resolves(),
            get: sinon.stub<[string], Promise<string | undefined>>().resolves(mockToken),
            delete: sinon.stub<[string], Promise<void>>().resolves()
        };

        // Setup mock commands registry
        mockCommands = {};
        // Mock vscode extension context
        globalStateUpdateStub = sinon.stub<[string, any], Promise<void>>().callsFake(
            async (key: string, value: any) => {
                mockGlobalState.set(key, value);
                return Promise.resolve();
            }
        );

        mockContext = {
            subscriptions: [],
            globalState: {
                get: (key: string) => mockGlobalState.get(key),
                update: globalStateUpdateStub
            } as any,
            secrets: mockSecrets
        } as unknown as vscode.ExtensionContext;

        // Mock vscode commands with proper return types
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

        // Mock vscode window with proper return types
        showInputBoxStub = sinon.stub(vscode.window, 'showInputBox');
        showQuickPickStub = sinon.stub(vscode.window, 'showQuickPick');
        showInfoMessageStub = sinon.stub(vscode.window, 'showInformationMessage').resolves(undefined);
        showErrorMessageStub = sinon.stub(vscode.window, 'showErrorMessage').resolves(undefined);
        showWarningMessageStub = sinon.stub(vscode.window, 'showWarningMessage').resolves(undefined);

        // Default values
        showInputBoxStub.resolves('test-input');
        showQuickPickStub.resolves({ label: 'teacher' });

        // Mock auth service with proper parameter and return types
        loginStub = sinon.stub(authenticationService, 'login').resolves(mockToken);
        registerStub = sinon.stub(authenticationService, 'register').resolves(mockToken);
        updateStub = sinon.stub(authenticationService, 'update').resolves(mockToken);
        getUserInfoStub = sinon.stub(authenticationService, 'getUserInfo').resolves({
            id: 1,
            username: 'testuser',
            email: 'test@example.com'
        });
        getVerificationCodeStub = sinon.stub(authenticationService, 'getVerificationCode').resolves('123456');

        // Mock view management
        refreshAllViewsStub = sinon.stub(viewManager, 'refreshAllViews');
        refreshViewsStub = sinon.stub(viewManager, 'refreshViews');

        // Mock auth utils
        getAuthDetailsStub = sinon.stub(authUtils, 'getAuthDetails')
            .resolves({ token: mockToken, loginInfo: mockLoginInfo });

        // Register commands
        registerUserCommands(mockContext);
    });

    teardown(() => {
        sinon.restore();
    });

    test('Login command - successful login', async () => {
        // Setup with more specific control
        showInputBoxStub.onFirstCall().resolves('user@example.com');
        showInputBoxStub.onSecondCall().resolves('password123');

        // Execute
        await vscode.commands.executeCommand('intelligent-ide.login');

        // Verify
        assert.ok(loginStub.calledWith('user@example.com', 'password123'));
        assert.ok(mockSecrets.store.calledWith('authToken', mockToken));
        assert.ok(refreshAllViewsStub.called);
        assert.ok(showInfoMessageStub.calledWith('Login successful!'));
    });

    test('Login command - missing credentials', async () => {
        // Setup: Only email entered, no password
        showInputBoxStub.onFirstCall().resolves('user@example.com');
        showInputBoxStub.onSecondCall().resolves(undefined);

        // Execute
        await vscode.commands.executeCommand('intelligent-ide.login');

        // Verify
        assert.ok(!loginStub.called);
        assert.ok(showErrorMessageStub.calledWith('Username and password are required.'));
    });

    test('Register command - successful registration', async () => {
        // Setup
        showInputBoxStub.onCall(0).resolves('newusername'); // username
        showInputBoxStub.onCall(1).resolves('new@example.com'); // email
        showInputBoxStub.onCall(2).resolves('123456'); // verification code
        showInputBoxStub.onCall(3).resolves('password123'); // password

        // Execute
        await vscode.commands.executeCommand('intelligent-ide.register');

        // Verify
        assert.ok(getVerificationCodeStub.calledWith('new@example.com'));
        assert.ok(registerStub.calledWith('newusername', 'new@example.com', 'password123', '123456'));
        assert.ok(mockSecrets.store.calledWith('authToken', mockToken));
        assert.ok(getUserInfoStub.called);
        assert.ok(showInfoMessageStub.calledWith('Registration successful for newusername !'));
    });

    test('Logout command - successful logout', async () => {
        // Execute
        await vscode.commands.executeCommand('intelligent-ide.logout');
        // Verify
        assert.ok(globalStateUpdateStub.calledWith('loginInfo', undefined));
        assert.ok(mockSecrets.delete.calledWith('authToken'));
        assert.ok(refreshAllViewsStub.called);
        assert.ok(showInfoMessageStub.calledWith('Logout successful!'));
        assert.ok(showInfoMessageStub.calledWith('Logout successful!'));
    });

    test('SwitchRole command - successful role switch', async () => {
        // Setup
        mockGlobalState.set('loginInfo', { ...mockLoginInfo }); // Set initial login info
        showQuickPickStub.resolves({ label: 'teacher' });

        // Execute
        await vscode.commands.executeCommand('intelligent-ide.switchRole');

        // Verify
        assert.ok(mockGlobalState.has('loginInfo'));
        const updatedLoginInfo = mockGlobalState.get('loginInfo');
        assert.ok(refreshViewsStub.called);
    });

    test('Update command - successful update', async () => {
        // Setup
        showInputBoxStub.onFirstCall().resolves('updatedusername');
        showInputBoxStub.onSecondCall().resolves('newpassword123');

        // Execute
        await vscode.commands.executeCommand('intelligent-ide.update');

        // Verify
        assert.ok(updateStub.calledWith('updatedusername', 'newpassword123', mockToken));
        assert.ok(showInfoMessageStub.calledWith('Updated successfully!'));
    });

    test('Error handling in commands', async () => {
        // Setup - cause login to throw an error
        const errorMessage = 'Authentication failed';
        loginStub.rejects(new Error(errorMessage));

        // Setup inputs
        showInputBoxStub.onFirstCall().resolves('user@example.com');
        showInputBoxStub.onSecondCall().resolves('password123');

        // Execute
        await vscode.commands.executeCommand('intelligent-ide.login');

        // Verify
        assert.ok(showErrorMessageStub.calledWith(`Login failed: ${errorMessage}`));
    });
});