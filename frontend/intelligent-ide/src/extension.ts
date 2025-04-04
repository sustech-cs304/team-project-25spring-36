// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from 'vscode';
import { displayUserView } from './views/userView'; // Import the user view logic
import {registerAll} from './commands/UserCommands'; // Import all commands

// This method is called when your extension is activated
// Your extension is activated along the vscode
export function activate(context: vscode.ExtensionContext) {
    // Display the user view
  displayUserView(context);

  registerAll(context);
  console.log('Congratulations, your extension "intelligent-ide" is now active!');
}

// This method is called when your extension is deactivated
export function deactivate() { }
