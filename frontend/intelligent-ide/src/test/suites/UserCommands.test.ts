import * as assert from 'assert';
import * as sinon from 'sinon';
import * as vscode from 'vscode';
import { authenticationService } from '../../services/userService';
import * as viewManager from '../../views/viewManager';
import * as authUtils from '../../utils/authUtils';
import { registerUserCommands } from '../../commands/UserCommands';

suite('User Commands Test Suite', () => {
    let mockContext: vscode.ExtensionContext;
    let mockGlobalState: Map<string, any>;
    let mockWorkspaceState: Map<string, any>;
    let mockSecrets: {
        store: sinon.SinonStub<[string, string], Promise<void>>;
        get: sinon.SinonStub<[string], Promise<string | undefined>>;
        delete: sinon.SinonStub<[string], Promise<void>>;
    };
    let mockCommands: Record<string, (...args: any[]) => any>;
    let globalStateUpdateStub: sinon.SinonStub<[string, any], Promise<void>>;
    let workspaceStateUpdateStub: sinon.SinonStub<[string, any], Promise<void>>;

    // VS Code API stubs
    let showInputBoxStub: sinon.SinonStub;
    let showQuickPickStub: sinon.SinonStub;
    let showInfoMessageStub: sinon.SinonStub;
    let showErrorMessageStub: sinon.SinonStub;
    let showWarningMessageStub: sinon.SinonStub;

    // View manager stubs
    let refreshAllViewsStub: sinon.SinonStub;
    let refreshViewsStub: sinon.SinonStub;

    // Auth utils stub
    let getAuthDetailsStub: sinon.SinonStub;

    // Service stubs
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
        sinon.restore();

        mockGlobalState = new Map<string, any>();
        mockWorkspaceState = new Map<string, any>();

        mockSecrets = {
            store: sinon.stub<[string, string], Promise<void>>().resolves(),
            get: sinon.stub<[string], Promise<string | undefined>>().resolves(mockToken),
            delete: sinon.stub<[string], Promise<void>>().resolves()
        };

        mockCommands = {};

        globalStateUpdateStub = sinon.stub<[string, any], Promise<void>>().callsFake(
            async (key: string, value: any) => {
                mockGlobalState.set(key, value);
                return Promise.resolve();
            }
        );

        workspaceStateUpdateStub = sinon.stub<[string, any], Promise<void>>().callsFake(
            async (key: string, value: any) => {
                mockWorkspaceState.set(key, value);
                return Promise.resolve();
            }
        );

        mockContext = {
            subscriptions: [],
            globalState: {
                get: (key: string) => mockGlobalState.get(key),
                update: globalStateUpdateStub
            } as any,
            workspaceState: {
                get: (key: string) => mockWorkspaceState.get(key),
                update: workspaceStateUpdateStub
            } as any,
            secrets: mockSecrets
        } as unknown as vscode.ExtensionContext;

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
        showInputBoxStub = sinon.stub(vscode.window, 'showInputBox');
        showQuickPickStub = sinon.stub(vscode.window, 'showQuickPick');
        showInfoMessageStub = sinon.stub(vscode.window, 'showInformationMessage').resolves(undefined);
        showErrorMessageStub = sinon.stub(vscode.window, 'showErrorMessage').resolves(undefined);
        showWarningMessageStub = sinon.stub(vscode.window, 'showWarningMessage').resolves(undefined);

        // Default values
        showInputBoxStub.resolves('test-input');
        showQuickPickStub.resolves({ label: 'teacher' });

        // Service stubs
        loginStub = sinon.stub(authenticationService, 'login').resolves(mockToken);
        registerStub = sinon.stub(authenticationService, 'register').resolves(mockToken);
        updateStub = sinon.stub(authenticationService, 'update').resolves(mockToken);
        getUserInfoStub = sinon.stub(authenticationService, 'getUserInfo').resolves({
            id: 1,
            username: 'testuser',
            email: 'test@example.com'
        });
        getVerificationCodeStub = sinon.stub(authenticationService, 'getVerificationCode').resolves('123456');

        // View manager stubs
        refreshAllViewsStub = sinon.stub(viewManager, 'refreshAllViews');
        refreshViewsStub = sinon.stub(viewManager, 'refreshViews');

        // Auth utils stub
        getAuthDetailsStub = sinon.stub(authUtils, 'getAuthDetails')
            .resolves({ token: mockToken, loginInfo: mockLoginInfo });

        // Register commands
        registerUserCommands(mockContext);
    });

    teardown(() => {
        sinon.restore();
    });

    test('Login command - successful login', async () => {
        showInputBoxStub.onFirstCall().resolves('user@example.com');
        showInputBoxStub.onSecondCall().resolves('password123');

        await vscode.commands.executeCommand('intelligent-ide.login');

        assert.ok(loginStub.calledWith('user@example.com', 'password123'));
        assert.ok(getUserInfoStub.called);
        assert.ok(refreshAllViewsStub.called);
        assert.ok(showInfoMessageStub.calledWith('Login successful!'));
    });

    test('Login command - missing credentials', async () => {
        showInputBoxStub.onFirstCall().resolves('user@example.com');
        showInputBoxStub.onSecondCall().resolves(undefined);

        await vscode.commands.executeCommand('intelligent-ide.login');

        assert.ok(!loginStub.called);
        assert.ok(showErrorMessageStub.calledWith('Username and password are required.'));
    });

    test('Register command - successful registration', async () => {
        showInputBoxStub.onCall(0).resolves('newusername');
        showInputBoxStub.onCall(1).resolves('new@example.com');
        showInputBoxStub.onCall(2).resolves('123456');
        showInputBoxStub.onCall(3).resolves('password123');

        await vscode.commands.executeCommand('intelligent-ide.register');

        assert.ok(getVerificationCodeStub.calledWith('new@example.com'));
        assert.ok(registerStub.calledWith('newusername', 'new@example.com', 'password123', '123456'));
        assert.ok(getUserInfoStub.called);
        assert.ok(showInfoMessageStub.calledWith('Registration successful for newusername !'));
    });

    test('Logout command - successful logout', async () => {
        await vscode.commands.executeCommand('intelligent-ide.logout');

        assert.ok(workspaceStateUpdateStub.calledWith('loginInfo', undefined));
        assert.ok(refreshAllViewsStub.called);
        assert.ok(showInfoMessageStub.calledWith('Logout successful!'));
    });

    test('SwitchRole command - successful role switch', async () => {
        mockWorkspaceState.set('loginInfo', { ...mockLoginInfo });
        showQuickPickStub.resolves({ label: 'teacher' });

        await vscode.commands.executeCommand('intelligent-ide.switchRole');

        assert.ok(mockWorkspaceState.has('loginInfo'));
        assert.ok(refreshViewsStub.called);
    });

    test('Update command - successful update', async () => {
        showInputBoxStub.onFirstCall().resolves('updatedusername');
        showInputBoxStub.onSecondCall().resolves('newpassword123');

        await vscode.commands.executeCommand('intelligent-ide.update');

        assert.ok(updateStub.calledWith('updatedusername', 'newpassword123', mockToken));
        assert.ok(showInfoMessageStub.calledWith('Updated successfully!'));
    });

    test('Error handling in commands', async () => {
        const errorMessage = 'Authentication failed';
        loginStub.rejects(new Error(errorMessage));

        showInputBoxStub.onFirstCall().resolves('user@example.com');
        showInputBoxStub.onSecondCall().resolves('password123');

        await vscode.commands.executeCommand('intelligent-ide.login');

        assert.ok(showErrorMessageStub.calledWith(`Login failed: ${errorMessage}`));
    });
});