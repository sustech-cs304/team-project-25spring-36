// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from 'vscode';
import { registerLoginCommand } from './commands/loginCommand';
import { registerRegisterCommand } from './commands/registerCommand';
import { registerUpdateCommand } from './commands/updateCommand';
import { displayUserView } from './views/userView'; // Import the user view logic
import { registerLogoutCommand } from './commands/logoutCommand';

// This method is called when your extension is activated
// Your extension is activated along the vscode
export function activate(context: vscode.ExtensionContext) {
    // Display the user view
  displayUserView(context);

  //register all commands
  registerLoginCommand(context);
  registerRegisterCommand(context);
  registerUpdateCommand(context);
  registerLogoutCommand(context);

  console.log('Congratulations, your extension "intelligent-ide" is now active!');
}

// This method is called when your extension is deactivated
export function deactivate() { }
